import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'

import { fetchDeliveryDays } from './api'
import { CutoffControl } from './components/CutoffControl'
import { StatusMessage } from './components/StatusMessage'
import { About } from './views/About'
import { AccuracyView } from './views/AccuracyView'
import { DecisionView } from './views/DecisionView'

const VIEWS = [
  { id: 'decision', label: 'Decision day' },
  { id: 'accuracy', label: 'Accuracy' },
  { id: 'method', label: 'Method' },
] as const

type ViewId = (typeof VIEWS)[number]['id']

function viewFromHash(): ViewId {
  const hash = window.location.hash.slice(1)
  return VIEWS.find((view) => view.id === hash)?.id ?? 'decision'
}

export function App() {
  const [view, setView] = useState<ViewId>(viewFromHash)
  const [cutoff, setCutoff] = useState<string | null>(null)
  const [day, setDay] = useState<string | null>(null)
  const meta = useQuery({ queryKey: ['delivery-days'], queryFn: fetchDeliveryDays })

  useEffect(() => {
    const onHashChange = () => setView(viewFromHash())
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  const activeCutoff = cutoff ?? meta.data?.default_cutoff ?? '09:20'
  const activeDay = day ?? meta.data?.delivery_days[0] ?? null

  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div>
            <h1 className="condensed text-xl font-semibold">Wind forecast decision portal</h1>
            <p className="text-sm text-muted">
              GB national wind, day-ahead decisions, January 2026
            </p>
          </div>
          <nav aria-label="Views" className="flex gap-1">
            {VIEWS.map((item) => (
              <a
                key={item.id}
                href={`#${item.id}`}
                aria-current={view === item.id ? 'page' : undefined}
                className={`rounded-md px-3 py-1.5 text-sm ${
                  view === item.id ? 'bg-paper font-semibold' : 'text-muted hover:text-ink'
                }`}
              >
                {item.label}
              </a>
            ))}
          </nav>
        </div>
        {view !== 'method' && meta.data && (
          <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-6 pb-4">
            <span className="text-sm text-muted">Decide at, the day before (UK time):</span>
            <CutoffControl
              options={meta.data.cutoff_options}
              value={activeCutoff}
              onChange={setCutoff}
            />
          </div>
        )}
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        {view === 'method' ? (
          <About />
        ) : meta.isPending ? (
          <StatusMessage kind="loading" />
        ) : meta.isError ? (
          <StatusMessage kind="error" message={meta.error.message} />
        ) : view === 'accuracy' ? (
          <AccuracyView cutoff={activeCutoff} />
        ) : activeDay ? (
          <DecisionView
            days={meta.data.delivery_days}
            day={activeDay}
            onDayChange={setDay}
            cutoff={activeCutoff}
          />
        ) : (
          <StatusMessage kind="empty" message="No delivery days are available." />
        )}
      </main>
    </div>
  )
}
