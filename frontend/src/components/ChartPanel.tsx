import type { ReactNode } from 'react'

type Props = { title: string; caption?: ReactNode; children: ReactNode; className?: string }

export function ChartPanel({ title, caption, children, className = '' }: Props) {
  return (
    <section className={`rounded-lg border border-line bg-surface p-5 ${className}`}>
      <h3 className="text-base font-semibold">{title}</h3>
      {caption && <p className="mt-1 max-w-prose text-sm text-muted">{caption}</p>}
      <div className="mt-4 h-64">{children}</div>
    </section>
  )
}
