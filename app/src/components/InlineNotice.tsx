import { AlertCircle, CheckCircle2 } from 'lucide-react'

interface InlineNoticeProps {
  kind: 'error' | 'success'
  message: string
}

export default function InlineNotice({ kind, message }: InlineNoticeProps) {
  const Icon = kind === 'error' ? AlertCircle : CheckCircle2
  return (
    <div
      className={`flex items-start gap-2 rounded-md border px-3 py-2 text-sm ${
        kind === 'error'
          ? 'border-red-200 bg-red-50 text-red-700'
          : 'border-emerald-200 bg-emerald-50 text-emerald-700'
      }`}
      role={kind === 'error' ? 'alert' : 'status'}
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <span>{message}</span>
    </div>
  )
}
