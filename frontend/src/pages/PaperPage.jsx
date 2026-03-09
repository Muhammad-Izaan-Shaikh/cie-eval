import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { papersApi, questionsApi } from '../services/api'
import QuestionCard from '../components/QuestionCard'
import { Loader, ChevronLeft, BookOpen, AlertCircle } from 'lucide-react'

export default function PaperPage() {
  const { paperId } = useParams()

  const { data: paper, isLoading: paperLoading } = useQuery({
    queryKey: ['paper', paperId],
    queryFn: () => papersApi.get(paperId).then((r) => r.data),
  })

  const { data: questions, isLoading: qLoading, error: qError } = useQuery({
    queryKey: ['questions', paperId],
    queryFn: () => questionsApi.getByPaper(paperId).then((r) => r.data),
    enabled: paper?.parse_status === 'complete',
    retry: false,
  })

  if (paperLoading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader size={24} className="animate-spin text-ink/30" />
      </div>
    )
  }

  if (!paper) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-20 text-center">
        <AlertCircle size={32} className="text-crimson mx-auto mb-4" />
        <h2 className="font-display text-xl text-ink mb-2">Paper not found</h2>
        <Link to="/dashboard" className="btn-secondary mt-4 inline-block">Back to dashboard</Link>
      </div>
    )
  }

  const totalMarks = questions?.reduce((sum, q) => sum + q.marks, 0) || 0

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      {/* Breadcrumb */}
      <div className="mb-6">
        <Link
          to="/dashboard"
          className="flex items-center gap-1.5 text-xs text-ink/40 hover:text-ink/70 transition-colors"
        >
          <ChevronLeft size={14} />
          Back to dashboard
        </Link>
      </div>

      {/* Paper header */}
      <div className="card p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="font-mono text-xs bg-ink text-parchment px-2 py-0.5">
                {paper.subject_code}
              </span>
              {paper.year && <span className="text-xs text-ink/40">{paper.year}</span>}
              {paper.session && <span className="text-xs text-ink/40">{paper.session}</span>}
            </div>
            <h1 className="font-display text-2xl text-ink mb-1">{paper.subject_name}</h1>
            <p className="text-sm text-ink/50">{paper.paper_name}</p>
          </div>

          <div className="text-right">
            <div className="text-xs text-ink/30 tracking-widest uppercase mb-1">Total marks</div>
            <div className="font-display text-3xl text-ink">{totalMarks}</div>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-4 pt-4 border-t border-ink/10">
          <div className="flex items-center gap-2 text-xs text-ink/40">
            <BookOpen size={12} />
            <span>
              Answer all questions. Submit each answer for AI grading. Use the chat panel for feedback.
            </span>
          </div>
        </div>
      </div>

      {/* Questions */}
      {paper.parse_status !== 'complete' ? (
        <div className="text-center py-20">
          <Loader size={28} className="animate-spin text-gold mx-auto mb-4" />
          <p className="text-sm text-ink/50">Paper is being processed…</p>
          <p className="text-xs text-ink/30 mt-1">This may take a minute. Refresh the page to check.</p>
        </div>
      ) : qLoading ? (
        <div className="text-center py-20">
          <Loader size={24} className="animate-spin text-ink/30 mx-auto" />
        </div>
      ) : qError ? (
        <div className="text-center py-20">
          <AlertCircle size={28} className="text-crimson mx-auto mb-3" />
          <p className="text-sm text-ink/50">Failed to load questions</p>
          <p className="text-xs text-ink/30 mt-1">{qError.response?.data?.detail}</p>
        </div>
      ) : questions?.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-sm text-ink/40">
            No questions were parsed from this paper.
            Ensure you uploaded a text-based Cambridge PDF.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-ink/30 tracking-widest uppercase">
              {questions.length} question{questions.length !== 1 ? 's' : ''}
            </span>
          </div>
          {questions.map((q, i) => (
            <QuestionCard
              key={q.id}
              question={q}
              defaultOpen={i === 0}
            />
          ))}
        </div>
      )}
    </div>
  )
}
