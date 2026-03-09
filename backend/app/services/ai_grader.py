"""
AI grading and chat service.
Uses async LLM calls for grading and chat (runs in FastAPI async context).
"""
from typing import List, Dict, Optional, Tuple
import logging
import re
from app.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Grading prompt
# ─────────────────────────────────────────────────────────────────────────────

GRADE_PROMPT = """You are a senior Cambridge / Edexcel O / A-level examiner with decades of marking experience.

Grade the student's answer STRICTLY according to the mark scheme below.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUESTION:
{question}

MARKS AVAILABLE: {marks}

MARK SCHEME:
{markscheme}

STUDENT ANSWER:
{answer}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MARKING RULES:
1. Award marks ONLY for points present in the mark scheme.
2. If the mark scheme says "Allow X", award the mark if the student says X.
3. If the mark scheme says "Do not award Y", do not award the mark even if Y sounds correct.
4. Accept correct ideas expressed in different but scientifically equivalent wording.
5. For calculations: award marks for correct method even if arithmetic is wrong (error carried forward).
6. For MCQ: award 1 mark only if the student selects the exact correct option.
7. Be concise. Do not add encouragement or filler.

RESPOND IN THIS EXACT FORMAT — nothing before or after:
Marks awarded: X/{marks}

Feedback:
[For each marking point: state whether it was awarded and why. If marks were lost, quote the specific mark scheme requirement that was not met.]
"""

# ─────────────────────────────────────────────────────────────────────────────
# Chat prompts
# ─────────────────────────────────────────────────────────────────────────────

CHAT_PROMPT = """You are a senior Cambridge / Edexcel A-level examiner helping a student improve.

QUESTION: {question}
MARKS AVAILABLE: {marks}
MARK SCHEME: {markscheme}
STUDENT ANSWER: {answer}
MARKS AWARDED: {current_marks}/{marks}
EXAMINER FEEDBACK: {feedback}

The student asks: {user_message}

Answer as a strict but helpful examiner. Reference the mark scheme when relevant. Be concise.
"""

IMPROVE_PROMPT = """You are a senior Cambridge / Edexcel A-level examiner.

QUESTION: {question}
MARKS AVAILABLE: {marks}
MARK SCHEME: {markscheme}
STUDENT ANSWER: {answer}
CURRENT MARKS: {current_marks}/{marks}

Rewrite the student's answer to earn full marks, staying as close to their original wording as possible.
Only add or change what is necessary to satisfy the mark scheme.
Output the improved answer only — no preamble, no explanation.
"""

MODEL_ANSWER_PROMPT = """You are a senior Cambridge / Edexcel A-level examiner.

QUESTION: {question}
MARKS AVAILABLE: {marks}
MARK SCHEME: {markscheme}

Write a concise model answer that would earn full marks according to the mark scheme.
Output the model answer only — no preamble.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Async LLM calls (for FastAPI routes)
# ─────────────────────────────────────────────────────────────────────────────

async def _call_llm(messages: List[Dict]) -> str:
    if settings.AI_PROVIDER == "anthropic":
        return await _call_anthropic(messages)
    elif settings.AI_PROVIDER == "qwen":
        return await _call_qwen(messages)
    else:
        return await _call_openai(messages)

async def _call_qwen(messages: List[Dict]) -> str:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.QWEN_API_KEY,base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
    response = await client.chat.completions.create(
        model=settings.AI_MODEL,
        messages=messages,
        max_tokens=1000,
        temperature=0.1,
    )
    return response.choices[0].message.content

async def _call_openai(messages: List[Dict]) -> str:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=settings.AI_MODEL,
        messages=messages,
        max_tokens=1500,
        temperature=0.1,
    )
    return response.choices[0].message.content


async def _call_anthropic(messages: List[Dict]) -> str:
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = await client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1500,
        messages=messages,
    )
    return response.content[0].text


# ─────────────────────────────────────────────────────────────────────────────
# Parse grading response
# ─────────────────────────────────────────────────────────────────────────────

def _parse_grade_response(response: str, max_marks: int) -> Tuple[float, str]:
    marks_awarded = 0.0
    feedback = response.strip()

    m = re.search(r'Marks awarded:\s*(\d+(?:\.\d+)?)\s*/\s*\d+', response, re.IGNORECASE)
    if m:
        marks_awarded = min(float(m.group(1)), float(max_marks))

    fb = re.search(r'Feedback:\s*(.*)', response, re.IGNORECASE | re.DOTALL)
    if fb:
        feedback = fb.group(1).strip()

    return marks_awarded, feedback


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

async def grade_answer(
    question_text: str,
    markscheme_text: str,
    marks: int,
    student_answer: str,
) -> Tuple[float, str]:
    """Grade a student answer. Returns (marks_awarded, feedback)."""
    prompt = GRADE_PROMPT.format(
        question=question_text or "No question text available",
        markscheme=markscheme_text or "No mark scheme available",
        marks=marks or 1,
        answer=student_answer or "No answer provided",
    )
    try:
        response = await _call_llm([{"role": "user", "content": prompt}])
    except Exception as e:
        logger.error(f"LLM grading failed: {e}")
        raise ValueError(f"AI grading service error: {e}")

    return _parse_grade_response(response, marks or 1)


async def chat_with_ai(
    question_text: str,
    markscheme_text: str,
    marks: int,
    student_answer: str,
    current_marks: float,
    ai_feedback: str,
    user_message: str,
    mode: str,
    chat_history: List[Dict],
) -> str:
    """Handle a chat message. mode: feedback | improve | model_answer"""

    if mode == "improve":
        prompt = IMPROVE_PROMPT.format(
            question=question_text,
            markscheme=markscheme_text,
            marks=marks,
            answer=student_answer,
            current_marks=current_marks,
        )
    elif mode == "model_answer":
        prompt = MODEL_ANSWER_PROMPT.format(
            question=question_text,
            markscheme=markscheme_text,
            marks=marks,
        )
    else:
        prompt = CHAT_PROMPT.format(
            question=question_text,
            markscheme=markscheme_text,
            marks=marks,
            answer=student_answer,
            current_marks=current_marks,
            feedback=ai_feedback or "Not yet graded",
            user_message=user_message,
        )

    # Include recent chat history for context (last 6 messages)
    messages = []
    for msg in (chat_history or [])[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": prompt})

    try:
        return await _call_llm(messages)
    except Exception as e:
        logger.error(f"LLM chat failed: {e}")
        raise ValueError(f"AI chat service error: {e}")
