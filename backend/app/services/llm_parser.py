"""
LLM-based exam paper and mark scheme parser.

Sends raw PDF text to the LLM with precise prompts and gets back
structured JSON. This is far more robust than regex for Cambridge/Edexcel
papers which vary in layout across exam boards and years.

Two-step process:
  1. parse_question_paper_with_llm()  -> list of question dicts
  2. parse_mark_scheme_with_llm()     -> list of mark scheme dicts
  3. merge_questions_and_markscheme() -> final flat list for DB insertion
"""

import json
import logging
import re
from typing import List, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────────────────────────────────────

QUESTION_PAPER_PROMPT = """You are an expert at parsing Cambridge and Edexcel A-level exam papers.

I will give you the raw extracted text of an exam question paper.
Your job is to identify every question and sub-question, extract its text, and return structured JSON.

RULES:
1. Include ALL questions including MCQ (multiple choice) questions.
2. For MCQ questions, include the options A/B/C/D as part of the question_text.
3. Preserve the exact question text including all chemical formulas, numbers, and units.
4. Use the exact Cambridge/Edexcel numbering hierarchy:
   - Top level: 1, 2, 3, ...
   - Parts: (a), (b), (c), ...
   - Sub-parts: (i), (ii), (iii), ...
5. question_key format:
   - Top level with no parts: "Q1", "Q2"
   - Part only: "Q1a", "Q1b", "Q16a"
   - Sub-part: "Q1a_i", "Q16b_iii"
6. marks: extract from annotations like "(1)", "(2)", "(3 marks)" near the question.
   Set to 0 if you cannot find marks for that specific sub-question.
7. question_type: "mcq" if it has A/B/C/D options, "diagram" if it asks to draw/sketch/show mechanism, otherwise "text"
8. Do NOT include instructions, rubrics, or section headers — only actual questions.
9. If a question has sub-parts, do NOT create a record for the parent — only create records for the leaf sub-parts that students actually answer.
   Exception: if a top-level question has NO parts at all, create one record for it.

Return ONLY a valid JSON array. No markdown, no explanation, no code fences.

Format:
[
  {
    "question_key": "Q1a",
    "question_text": "Full text of the question as it appears in the paper...",
    "marks": 1,
    "question_type": "text"
  },
  ...
]

EXAM PAPER TEXT:
"""

MARK_SCHEME_PROMPT = """You are an expert at parsing Cambridge and Edexcel A-level mark schemes.

I will give you the raw extracted text of a mark scheme.
Your job is to extract the marking guidance for every question and return structured JSON.

RULES:
1. Use the EXACT same question_key format as the question paper:
   - "Q1a", "Q1b", "Q16a_i", "Q20b", etc.
2. marks: the number of marks awarded for this question/sub-question.
3. scheme_text: combine the ANSWER and any ADDITIONAL GUIDANCE / ALLOW / DO NOT AWARD notes.
   This is what the AI examiner will use to grade student answers, so include everything relevant:
   - The correct answer(s)
   - Alternative acceptable answers (Allow...)
   - What NOT to accept (Do not award...)
   - Marking guidance for calculations (e.g. "correct answer with working scores 2")
   - For extended writing questions, include ALL indicative content points
4. If multiple marking points exist (M1, M2, M3), include all of them in scheme_text.
5. For "Total for Question" lines — ignore them.
6. Ignore preamble, general marking guidance, and publication information at the start.

Return ONLY a valid JSON array. No markdown, no explanation, no code fences.

Format:
[
  {
    "question_key": "Q1a",
    "marks": 1,
    "scheme_text": "The only correct answer is B (two). A is incorrect because... Allow: two peaks. Do not award: 1 peak."
  },
  ...
]

MARK SCHEME TEXT:
"""


# ─────────────────────────────────────────────────────────────────────────────
# LLM call (synchronous — runs inside background thread)
# ─────────────────────────────────────────────────────────────────────────────

def _call_llm_sync(prompt: str) -> str:
    """
    Synchronous LLM call for use inside background threads.
    Uses OpenAI or Anthropic depending on settings.
    """
    if settings.AI_PROVIDER == "anthropic":
        return _call_anthropic_sync(prompt)
    elif settings.AI_PROVIDER == "qwen":
        return _call_qwen_sync(prompt)
    else:
        return _call_openai_sync(prompt)

def _call_qwen_sync(prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=settings.QWEN_API_KEY, base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
    response = client.chat.completions.create(
        model=settings.AI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=6000,
        temperature=0,
    )
    return response.choices[0].message.content

def _call_openai_sync(prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=settings.AI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
        temperature=0,
    )
    return response.choices[0].message.content


def _call_anthropic_sync(prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


# ─────────────────────────────────────────────────────────────────────────────
# JSON extraction helper
# ─────────────────────────────────────────────────────────────────────────────

def _extract_json(raw: str) -> List[Dict]:
    """
    Robustly extract a JSON array from an LLM response.
    Handles cases where the model wraps output in markdown code fences.
    """
    # Strip markdown fences if present
    text = raw.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'```\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()

    # Find the JSON array
    start = text.find('[')
    end   = text.rfind(']')
    if start == -1 or end == -1:
        raise ValueError(f"No JSON array found in LLM response. Response was:\n{raw[:500]}")

    json_str = text[start:end + 1]
    try:
        result = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from LLM: {e}\nJSON was:\n{json_str[:500]}")

    if not isinstance(result, list):
        raise ValueError(f"Expected JSON array, got {type(result)}")

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Text chunking — LLMs have context limits
# ─────────────────────────────────────────────────────────────────────────────

MAX_CHARS = 20000  # ~7k tokens, well within gpt-4o/claude limits with room for prompt


def _chunk_text(text: str) -> List[str]:
    """
    Split text into chunks that fit within LLM context.
    Tries to split on double newlines (between questions) rather than mid-sentence.
    """
    if len(text) <= MAX_CHARS:
        return [text]

    chunks = []
    current = ""
    for paragraph in text.split("\n\n"):
        if len(current) + len(paragraph) + 2 > MAX_CHARS:
            if current:
                chunks.append(current.strip())
            current = paragraph
        else:
            current += "\n\n" + paragraph if current else paragraph

    if current.strip():
        chunks.append(current.strip())

    logger.info(f"Text split into {len(chunks)} chunks for LLM processing")
    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def parse_question_paper_with_llm(raw_text: str) -> List[Dict]:
    """
    Send question paper text to LLM and get back structured question list.
    Returns list of dicts with: question_key, question_text, marks, question_type
    """
    logger.info(f"Parsing question paper with LLM ({len(raw_text):,} chars)")
    chunks = _chunk_text(raw_text)
    all_questions: List[Dict] = []
    seen_keys = set()

    for i, chunk in enumerate(chunks):
        logger.info(f"  Q-paper chunk {i+1}/{len(chunks)} ({len(chunk):,} chars)")
        prompt = QUESTION_PAPER_PROMPT + chunk

        try:
            raw_response = _call_llm_sync(prompt)
            questions = _extract_json(raw_response)
        except Exception as e:
            logger.error(f"  LLM failed on Q-paper chunk {i+1}: {e}")
            raise

        for q in questions:
            key = q.get("question_key", "")
            if not key or key in seen_keys:
                continue
            seen_keys.add(key)
            all_questions.append({
                "question_key":  key,
                "question_text": q.get("question_text", "").strip(),
                "marks":         int(q.get("marks", 0)),
                "question_type": q.get("question_type", "text"),
            })

    logger.info(f"Q-paper parsed: {len(all_questions)} questions extracted by LLM")
    return all_questions


def parse_mark_scheme_with_llm(raw_text: str) -> List[Dict]:
    """
    Send mark scheme text to LLM and get back structured marking entries.
    Returns list of dicts with: question_key, marks, scheme_text
    """
    logger.info(f"Parsing mark scheme with LLM ({len(raw_text):,} chars)")
    chunks = _chunk_text(raw_text)
    all_entries: List[Dict] = []
    seen_keys = set()

    for i, chunk in enumerate(chunks):
        logger.info(f"  MS chunk {i+1}/{len(chunks)} ({len(chunk):,} chars)")
        prompt = MARK_SCHEME_PROMPT + chunk

        try:
            raw_response = _call_llm_sync(prompt)
            entries = _extract_json(raw_response)
        except Exception as e:
            logger.error(f"  LLM failed on MS chunk {i+1}: {e}")
            raise

        for entry in entries:
            key = entry.get("question_key", "")
            if not key:
                continue
            if key in seen_keys:
                # Append additional marking points for same question
                for existing in all_entries:
                    if existing["question_key"] == key:
                        extra = entry.get("scheme_text", "").strip()
                        if extra:
                            existing["scheme_text"] += " / " + extra
                        existing["marks"] = max(
                            existing["marks"], int(entry.get("marks", 0))
                        )
                continue
            seen_keys.add(key)
            all_entries.append({
                "question_key": key,
                "marks":        int(entry.get("marks", 0)),
                "scheme_text":  entry.get("scheme_text", "").strip(),
            })

    logger.info(f"Mark scheme parsed: {len(all_entries)} entries extracted by LLM")
    return all_entries


def merge_questions_and_markscheme(
    questions: List[Dict],
    markscheme: List[Dict],
) -> List[Dict]:
    """
    Merge question list with mark scheme list into final DB records.
    Mark scheme entries are matched by question_key.
    For questions with no mark scheme entry, scheme_text is left empty.
    """
    ms_index = {entry["question_key"]: entry for entry in markscheme}
    records  = []

    for order, q in enumerate(questions):
        key = q["question_key"]
        ms  = ms_index.get(key, {})

        # Prefer mark scheme marks over question paper marks (more reliable)
        marks = ms.get("marks") or q.get("marks", 0)

        records.append({
            "question_key":    key,
            "question_text":   q.get("question_text", ""),
            "markscheme_text": ms.get("scheme_text", ""),
            "marks":           marks,
            "question_type":   q.get("question_type", "text"),
            "order_index":     order,
        })

    # Log sample for verification
    for r in records[:5]:
        logger.info(
            f"  Merged: {r['question_key']:12s} "
            f"{r['marks']}m | "
            f"q={r['question_text'][:50]!r} | "
            f"ms={r['markscheme_text'][:50]!r}"
        )

    logger.info(f"Merge complete: {len(records)} records ready for DB")
    return records
