import { useState } from 'react'
import { answersApi } from '../services/api'
import toast from 'react-hot-toast'
import AIChatPanel from './AIChatPanel'
import { Send, Image, ChevronDown, ChevronUp, Star, StarHalf } from 'lucide-react'
import clsx from 'clsx'

function MarksBar({ awarded, total }) {
  if (total === 0) return null
  const pct = Math.min(Math.round((awarded / total) * 100), 100)
  const color = pct >= 75 ? 'bg-sage' : pct >= 50 ? 'bg-gold' : 'bg-crimson'

  return (
    <div className="mt-3">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-ink/40">Score</span>
        <span className={clsx('font-mono font-medium',
          pct >= 75 ? 'text-sage' : pct >= 50 ? 'text-gold' : 'text-crimson'
        )}>
          {awarded}/{total}
        </span>
      </div>
      <div className="h-1 bg-ink/10 rounded-full overflow-hidden">
        <div className={clsx('h-full transition-all duration-700', color)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function QuestionCard({ question, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  const [text, setText] = useState('')
  const [answer, setAnswer] = useState(null)
  const [loading, setLoading] = useState(false)
  const [imageFile, setImageFile] = useState(null)
  const [chatOpen, setChatOpen] = useState(false)

  const handleSubmit = async () => {
    if (!text.trim()) {
      toast.error('Please enter an answer')
      return
    }
    setLoading(true)
    try {
      const res = await answersApi.submit({
        question_id: question.id,
        answer_text: text,
      })
      setAnswer({
        answer_text: text,
        marks_awarded: res.data.marks_awarded,
        ai_feedback: res.data.feedback,
        chat_history: [],
        id: res.data.answer_id,
      })
      setChatOpen(true)
      toast.success(`Graded: ${res.data.marks_awarded}/${res.data.max_marks} marks`)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Submission failed')
    } finally {
      setLoading(false)
    }
  }

  const handleImageUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const fd = new FormData()
    fd.append('image', file)
    try {
      await answersApi.uploadImage(question.id, fd)
      toast.success('Diagram uploaded')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Image upload failed')
    }
  }

  return (
    <div className={clsx('card animate-fade-in', open && 'ring-1 ring-ink/10')}>
      {/* Question header */}
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-5 text-left hover:bg-ink/2 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="font-mono text-xs bg-ink text-parchment px-2 py-0.5">
            {question.question_key}
          </span>
          <span className="text-sm text-ink/50 truncate max-w-lg">
            {question.question_text?.slice(0, 80) || 'No question text'}
            {(question.question_text?.length || 0) > 80 && '…'}
          </span>
        </div>

        <div className="flex items-center gap-3 flex-shrink-0">
          {answer && (
            <MarksBar awarded={answer.marks_awarded} total={question.marks} />
          )}
          <span className="badge badge-slate ml-2">{question.marks}m</span>
          {open ? <ChevronUp size={16} className="text-ink/30" /> : <ChevronDown size={16} className="text-ink/30" />}
        </div>
      </button>

      {/* Expanded content */}
      {open && (
        <div className="border-t border-ink/10">
          <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-ink/10">
            {/* Answer section */}
            <div className="p-5 space-y-4">
              {/* Full question text */}
              {question.question_text && (
                <div className="bg-parchment-dark p-4 text-sm text-ink/80 leading-relaxed">
                  <div className="text-xs text-ink/30 tracking-widest uppercase mb-2">Question</div>
                  {question.question_text}
                  <div className="mt-2 text-xs text-ink/30">[{question.marks} mark{question.marks !== 1 ? 's' : ''}]</div>
                </div>
              )}

              {/* Answer input */}
              <div>
                <label className="label">Your answer</label>
                <textarea
                  rows={5}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  className="input-field resize-none font-body text-sm"
                  placeholder="Type your answer here…"
                />
              </div>

              {/* Image upload */}
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-2 text-xs text-ink/40 hover:text-ink/70 cursor-pointer transition-colors">
                  <Image size={14} />
                  Upload diagram
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={handleImageUpload}
                  />
                </label>
                <span className="text-xs text-ink/20">(max 3 uploads)</span>
              </div>

              <button
                onClick={handleSubmit}
                disabled={loading}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                <Send size={14} />
                {loading ? 'Grading…' : answer ? 'Resubmit answer' : 'Submit for grading'}
              </button>

              {/* Feedback panel */}
              {answer && (
                <div className="border border-ink/10 p-4 bg-parchment-dark animate-fade-in">
                  <div className="flex items-start justify-between mb-3">
                    <div className="text-xs tracking-widest uppercase text-ink/40">AI Feedback</div>
                    <div className="font-mono text-sm font-medium">
                      <span className={clsx(
                        answer.marks_awarded / question.marks >= 0.75 ? 'text-sage' :
                        answer.marks_awarded / question.marks >= 0.5 ? 'text-gold' : 'text-crimson'
                      )}>
                        {answer.marks_awarded}
                      </span>
                      <span className="text-ink/30">/{question.marks}</span>
                    </div>
                  </div>
                  <p className="text-xs text-ink/70 leading-relaxed whitespace-pre-wrap">
                    {answer.ai_feedback}
                  </p>
                </div>
              )}
            </div>

            {/* Chat section */}
            <div className={clsx(
              'flex flex-col',
              chatOpen ? 'h-96' : 'h-20'
            )}>
              {!chatOpen ? (
                <button
                  onClick={() => setChatOpen(true)}
                  className="h-full flex items-center justify-center gap-2 text-sm text-ink/30 hover:text-ink/60 transition-colors"
                >
                  Open AI chat →
                </button>
              ) : (
                <AIChatPanel
                  question={question}
                  answer={answer}
                />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
