import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { papersApi } from '../services/api'
import toast from 'react-hot-toast'
import { Upload, FileText, X, AlertTriangle } from 'lucide-react'
import clsx from 'clsx'

function PdfDropzone({ label, file, onFile, onRemove }) {
  const onDrop = useCallback((accepted) => {
    if (accepted[0]) onFile(accepted[0])
  }, [onFile])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
  })

  return (
    <div>
      <label className="label">{label}</label>
      {file ? (
        <div className="border border-ink/20 bg-white p-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-ink">
            <FileText size={16} className="text-gold" />
            <span className="truncate max-w-xs">{file.name}</span>
            <span className="text-ink/30 text-xs">({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
          </div>
          <button onClick={onRemove} className="text-ink/30 hover:text-crimson">
            <X size={16} />
          </button>
        </div>
      ) : (
        <div
          {...getRootProps()}
          className={clsx(
            'border-2 border-dashed p-8 text-center cursor-pointer transition-colors',
            isDragActive
              ? 'border-gold bg-gold/5'
              : 'border-ink/20 hover:border-ink/40 bg-white'
          )}
        >
          <input {...getInputProps()} />
          <Upload size={24} className="text-ink/30 mx-auto mb-2" />
          <p className="text-sm text-ink/50">
            {isDragActive ? 'Drop PDF here' : 'Drag & drop or click to upload'}
          </p>
          <p className="text-xs text-ink/30 mt-1">PDF only, max 50MB</p>
        </div>
      )}
    </div>
  )
}

const SUBJECT_PRESETS = [
  { code: '9701', name: 'Chemistry' },
  { code: '9702', name: 'Physics' },
  { code: '9709', name: 'Mathematics' },
  { code: '9700', name: 'Biology' },
  { code: '9608', name: 'Computer Science' },
  { code: '9231', name: 'Further Mathematics' },
  { code: '9093', name: 'English Language' },
  { code: '9389', name: 'History' },
]

export default function UploadPaperPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    subject_code: '',
    subject_name: '',
    paper_name: '',
    year: '',
    session: '',
  })
  const [questionPdf, setQuestionPdf] = useState(null)
  const [markscheme, setMarkscheme] = useState(null)
  const [loading, setLoading] = useState(false)

  const handlePreset = (preset) => {
    setForm((f) => ({ ...f, subject_code: preset.code, subject_name: preset.name }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!questionPdf || !markscheme) {
      toast.error('Please upload both PDFs')
      return
    }

    const fd = new FormData()
    Object.entries(form).forEach(([k, v]) => v && fd.append(k, v))
    fd.append('question_pdf', questionPdf)
    fd.append('markscheme_pdf', markscheme)

    setLoading(true)
    try {
      await papersApi.upload(fd)
      toast.success('Paper uploaded — processing in background')
      navigate('/dashboard')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-10">
      <div className="mb-8">
        <h1 className="page-title mb-1">Upload Paper</h1>
        <p className="text-sm text-ink/40">
          Upload a Cambridge exam question paper and its corresponding mark scheme.
        </p>
      </div>

      {/* Requirements notice */}
      <div className="border border-gold/30 bg-gold/5 p-4 mb-6 flex gap-3">
        <AlertTriangle size={16} className="text-gold flex-shrink-0 mt-0.5" />
        <div className="text-sm text-ink/70 leading-relaxed">
          <strong className="text-ink">Text-based PDFs only.</strong> Download papers directly from
          PapaCambridge, GCE Guide, or similar sites. Scanned image PDFs will not parse correctly.
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Subject presets */}
        <div>
          <label className="label">Subject presets</label>
          <div className="flex flex-wrap gap-2">
            {SUBJECT_PRESETS.map((p) => (
              <button
                key={p.code}
                type="button"
                onClick={() => handlePreset(p)}
                className={clsx(
                  'text-xs px-3 py-1.5 border transition-colors',
                  form.subject_code === p.code
                    ? 'border-ink bg-ink text-parchment'
                    : 'border-ink/20 hover:border-ink/50 text-ink/60'
                )}
              >
                {p.code} {p.name}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Subject code *</label>
            <input
              required
              value={form.subject_code}
              onChange={(e) => setForm({ ...form, subject_code: e.target.value })}
              className="input-field"
              placeholder="e.g. 9701"
            />
          </div>
          <div>
            <label className="label">Subject name *</label>
            <input
              required
              value={form.subject_name}
              onChange={(e) => setForm({ ...form, subject_name: e.target.value })}
              className="input-field"
              placeholder="e.g. Chemistry"
            />
          </div>
        </div>

        <div>
          <label className="label">Paper name *</label>
          <input
            required
            value={form.paper_name}
            onChange={(e) => setForm({ ...form, paper_name: e.target.value })}
            className="input-field"
            placeholder="e.g. Paper 2 — Structured Questions"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Year</label>
            <input
              value={form.year}
              onChange={(e) => setForm({ ...form, year: e.target.value })}
              className="input-field"
              placeholder="e.g. 2023"
            />
          </div>
          <div>
            <label className="label">Session</label>
            <input
              value={form.session}
              onChange={(e) => setForm({ ...form, session: e.target.value })}
              className="input-field"
              placeholder="e.g. May/June"
            />
          </div>
        </div>

        <div className="divider" />

        <PdfDropzone
          label="Question Paper PDF *"
          file={questionPdf}
          onFile={setQuestionPdf}
          onRemove={() => setQuestionPdf(null)}
        />

        <PdfDropzone
          label="Mark Scheme PDF *"
          file={markscheme}
          onFile={setMarkscheme}
          onRemove={() => setMarkscheme(null)}
        />

        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={loading} className="btn-primary flex-1">
            {loading ? 'Uploading…' : 'Upload & Process'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="btn-secondary"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
