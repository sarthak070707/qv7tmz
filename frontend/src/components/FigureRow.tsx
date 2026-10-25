export type Figure = { label: string; value: string; note?: string; tone?: 'shortfall' }

export function FigureRow({ figures }: { figures: Figure[] }) {
  return (
    <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-line bg-line md:grid-cols-4">
      {figures.map((figure) => (
        <div key={figure.label} className="bg-surface px-5 py-4">
          <dt className="text-sm text-muted">{figure.label}</dt>
          <dd
            className={`condensed mt-1 text-xl font-semibold md:text-2xl ${
              figure.tone === 'shortfall' ? 'text-shortfall' : ''
            }`}
          >
            {figure.value}
          </dd>
          {figure.note && <p className="mt-1 text-xs text-muted">{figure.note}</p>}
        </div>
      ))}
    </dl>
  )
}
