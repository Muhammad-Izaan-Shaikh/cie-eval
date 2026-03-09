import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { papersApi } from '../services/api'
import toast from 'react-hot-toast'
import {
  FileText, Trash2, Search, Plus, Clock,
  CheckCircle, AlertCircle, Loader
} from 'lucide-react'

const STATUS_CFG = {
  pending:    { label: 'Pending',    Icon: Clock,         cls: 'badge-slate' },
  processing: { label: 'Processing', Icon: Loader,        cls: 'badge-gold'   },
  complete:   { label: 'Ready',      Icon: CheckCircle,   cls: 'badge-sage'   },
  failed:     { label: 'Failed',     Icon: AlertCircle,   cls: 'badge-crimson'},
}

function StatusBadge({ status }) {
  const cfg = STATUS_CFG[status] || STATUS_CFG.pending
  const { Icon, label, cls } = cfg
  return (
    <span className={`badge ${cls} flex items-center gap-1`}>
      <Icon size={10} className={status === 'processing' ? 'animate-spin' : ''} />
      {label}
    </span>
  )
}

export default function DashboardPage() {
  const qc = useQueryClient()
  const [search, setSearch]   = useState({ subject_code: '', subject_name: '' })
  const [filters, setFilters] = useState({ subject_code: '', subject_name: '' })

  // Check whether any paper is still pending/processing
  const hasInProgress = (papers) =>
    papers?.some((p) => p.parse_status === 'pending' || p.parse_status === 'processing')

  const { data: papers, isLoading } = useQuery({
    queryKey: ['papers', filters],
    queryFn:  () => papersApi.list(filters).then((r) => r.data),
    // Poll every 3 seconds while any paper is still being processed
    refetchInterval: ({ state }) => (hasInProgress(state.data) ? 3000 : false),
    refetchIntervalInBackground: true,
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => papersApi.delete(id),
    onSuccess:  () => { qc.invalidateQueries(['papers']); toast.success('Paper deleted') },
    onError:    () => toast.error('Failed to delete paper'),
  })

  const handleSearch = (e) => {
    e.preventDefault()
    setFilters({ ...search })
  }

  const handleClear = () => {
    setSearch({ subject_code: '', subject_name: '' })
    setFilters({ subject_code: '', subject_name: '' })
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="page-title mb-1">My Papers</h1>
          <p className="text-sm text-ink/40">
            Upload Cambridge exam papers and practise with AI feedback.
          </p>
        </div>
        <Link to="/upload" className="btn-primary flex items-center gap-2">
          <Plus size={15} />
          Upload Paper
        </Link>
      </div>

      {/* Filters */}
      <form onSubmit={handleSearch} className="card p-4 mb-6 flex gap-3 items-end">
        <div className="flex-1">
          <label className="label">Subject code</label>
          <input
            value={search.subject_code}
            onChange={(e) => setSearch({ ...search, subject_code: e.target.value })}
            className="input-field"
            placeholder="e.g. 9701"
          />
        </div>
        <div className="flex-1">
          <label className="label">Subject name</label>
          <input
            value={search.subject_name}
            onChange={(e) => setSearch({ ...search, subject_name: e.target.value })}
            className="input-field"
            placeholder="e.g. Chemistry"
          />
        </div>
        <button type="submit" className="btn-secondary flex items-center gap-2">
          <Search size={14} />
          Filter
        </button>
        <button type="button" onClick={handleClear} className="btn-secondary text-ink/40">
          Clear
        </button>
      </form>

      {/* Processing notice */}
      {hasInProgress(papers) && (
        <div className="border border-gold/30 bg-gold/5 px-4 py-3 mb-4 flex items-center gap-3 text-sm text-ink/70">
          <Loader size={14} className="animate-spin text-gold flex-shrink-0" />
          Parsing PDFs in the background — this page refreshes automatically.
        </div>
      )}

      {/* Papers grid */}
      {isLoading ? (
        <div className="text-center py-20 text-ink/30">
          <Loader size={24} className="animate-spin mx-auto mb-3" />
          Loading papers…
        </div>
      ) : !papers?.length ? (
        <div className="text-center py-20">
          <FileText size={36} className="text-ink/20 mx-auto mb-4" />
          <p className="text-ink/40 mb-4">No papers uploaded yet.</p>
          <Link to="/upload" className="btn-primary">Upload your first paper</Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {papers.map((paper) => (
            <div
              key={paper.id}
              className="card p-5 hover:shadow-paper-hover transition-shadow duration-200"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="text-xs text-ink/40 tracking-widest mb-1">
                    {paper.subject_code}
                  </div>
                  <div className="section-title leading-tight">{paper.subject_name}</div>
                </div>
                <StatusBadge status={paper.parse_status} />
              </div>

              <div className="text-sm text-ink/60 mb-1">{paper.paper_name}</div>
              {(paper.year || paper.session) && (
                <div className="text-xs text-ink/30">
                  {[paper.year, paper.session].filter(Boolean).join(' · ')}
                </div>
              )}

              <div className="divider my-4" />

              <div className="flex items-center gap-3">
                {paper.parse_status === 'complete' ? (
                  <Link
                    to={`/papers/${paper.id}`}
                    className="btn-primary text-xs flex-1 text-center"
                  >
                    Open Paper
                  </Link>
                ) : paper.parse_status === 'failed' ? (
                  <span className="text-xs text-crimson/70 flex-1">
                    Parse failed — try re-uploading a text-based PDF
                  </span>
                ) : (
                  <span className="text-xs text-ink/30 flex-1 flex items-center gap-1.5">
                    <Loader size={11} className="animate-spin" />
                    Processing…
                  </span>
                )}
                <button
                  onClick={() => {
                    if (window.confirm('Delete this paper and all answers?')) {
                      deleteMutation.mutate(paper.id)
                    }
                  }}
                  className="text-ink/20 hover:text-crimson transition-colors p-1.5"
                  title="Delete paper"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
