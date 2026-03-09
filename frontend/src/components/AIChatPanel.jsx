import { useState, useRef, useEffect } from 'react'
import { answersApi } from '../services/api'
import toast from 'react-hot-toast'
import { Send, Bot, User, Loader, Lightbulb, BookOpen, Wand2 } from 'lucide-react'
import clsx from 'clsx'

const MODES = [
  { id: 'feedback', label: 'Ask question', icon: Lightbulb },
  { id: 'improve', label: 'Improve my answer', icon: Wand2 },
  { id: 'model_answer', label: 'Show model answer', icon: BookOpen },
]

export default function AIChatPanel({ question, answer, onAnswerUpdate }) {
  const [messages, setMessages] = useState(answer?.chat_history || [])
  const [input, setInput] = useState('')
  const [mode, setMode] = useState('feedback')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    setMessages(answer?.chat_history || [])
  }, [answer?.id])

  const sendMessage = async (messageOverride, modeOverride) => {
    const msg = messageOverride || input
    const selectedMode = modeOverride || mode

    if (!msg.trim() && selectedMode === 'feedback') return
    if (!answer) {
      toast.error('Submit an answer first before chatting')
      return
    }

    const userMsg = { role: 'user', content: msg || `[${selectedMode}]` }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await answersApi.chat({
        question_id: question.id,
        message: msg || selectedMode,
        mode: selectedMode,
      })
      const aiMsg = { role: 'assistant', content: res.data.response }
      setMessages((prev) => [...prev, aiMsg])
    } catch (err) {
      toast.error(err.response?.data?.detail || 'AI unavailable')
    } finally {
      setLoading(false)
    }
  }

  const handleQuickAction = (m) => {
    const actionLabel = MODES.find((x) => x.id === m)?.label || m
    sendMessage(actionLabel, m)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-ink/10">
        <Bot size={14} className="text-gold" />
        <span className="text-xs tracking-widest uppercase text-ink/50">AI Examiner</span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <Bot size={28} className="text-ink/20 mx-auto mb-2" />
            <p className="text-xs text-ink/30">
              Submit your answer to enable AI feedback
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={clsx('flex gap-2', msg.role === 'user' ? 'flex-row-reverse' : '')}
          >
            <div className={clsx(
              'flex-shrink-0 w-6 h-6 flex items-center justify-center',
              msg.role === 'user' ? 'bg-ink/10' : 'bg-gold/20'
            )}>
              {msg.role === 'user'
                ? <User size={12} className="text-ink" />
                : <Bot size={12} className="text-gold" />}
            </div>
            <div className={clsx(
              'max-w-[85%] px-3 py-2 text-xs leading-relaxed whitespace-pre-wrap',
              msg.role === 'user'
                ? 'bg-ink text-parchment'
                : 'bg-parchment-dark text-ink border border-ink/10'
            )}>
              {msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-2">
            <div className="w-6 h-6 flex items-center justify-center bg-gold/20">
              <Bot size={12} className="text-gold" />
            </div>
            <div className="bg-parchment-dark border border-ink/10 px-3 py-2">
              <Loader size={12} className="animate-spin text-ink/40" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Quick actions */}
      {answer && (
        <div className="px-4 py-2 border-t border-ink/5">
          <div className="flex flex-wrap gap-1.5">
            {MODES.map((m) => {
              const Icon = m.icon
              return (
                <button
                  key={m.id}
                  onClick={() => handleQuickAction(m.id)}
                  disabled={loading}
                  className="flex items-center gap-1 text-xs px-2.5 py-1 border border-ink/15 hover:bg-ink/5 text-ink/50 hover:text-ink transition-colors disabled:opacity-40"
                >
                  <Icon size={10} />
                  {m.label}
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-ink/10">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder={answer ? 'Ask the AI examiner…' : 'Submit an answer first'}
            disabled={!answer || loading}
            className="input-field text-xs flex-1"
          />
          <button
            onClick={() => sendMessage()}
            disabled={!answer || loading || !input.trim()}
            className="btn-primary px-3"
          >
            <Send size={14} />
          </button>
        </div>
      </div>
    </div>
  )
}
