import { useId } from 'react'

import type { CutoffOption } from '../api'

type Props = { options: CutoffOption[]; value: string; onChange: (cutoff: string) => void }

export function CutoffControl({ options, value, onChange }: Props) {
  const customId = useId()
  const isPreset = options.some((option) => option.time === value)

  return (
    <fieldset className="flex flex-wrap items-center gap-2">
      <legend className="sr-only">Decision cutoff on the day before delivery (UK time)</legend>
      {options.map((option) => (
        <button
          key={option.key}
          type="button"
          title={option.label}
          aria-pressed={option.time === value}
          onClick={() => onChange(option.time)}
          className={`rounded-md border px-3 py-1.5 text-sm ${
            option.time === value
              ? 'border-forecast bg-forecast text-surface'
              : 'border-line bg-surface hover:border-forecast'
          }`}
        >
          {option.label.replace(/ \(.*\)/, '')} <span className="font-semibold">{option.time}</span>
        </button>
      ))}
      <label htmlFor={customId} className="ml-1 text-sm text-muted">
        Custom
      </label>
      <input
        id={customId}
        type="time"
        value={value}
        onChange={(event) => event.target.value && onChange(event.target.value)}
        className={`rounded-md border bg-surface px-2 py-1 text-sm ${
          isPreset ? 'border-line' : 'border-forecast'
        }`}
      />
    </fieldset>
  )
}
