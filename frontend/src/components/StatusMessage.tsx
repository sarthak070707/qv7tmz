type Props = { kind: 'loading' | 'error' | 'empty'; message?: string }

const DEFAULTS = {
  loading: 'Loading data…',
  error: 'Something went wrong loading this view.',
  empty: 'No data for this selection.',
}

export function StatusMessage({ kind, message }: Props) {
  return (
    <p
      role={kind === 'error' ? 'alert' : 'status'}
      className={`rounded-md border px-4 py-6 text-sm ${
        kind === 'error' ? 'border-shortfall text-shortfall' : 'border-line text-muted'
      }`}
    >
      {message ?? DEFAULTS[kind]}
    </p>
  )
}
