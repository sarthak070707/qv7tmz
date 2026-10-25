const SOURCES = [
  {
    name: 'Actual wind generation (FUELHH)',
    url: 'https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream',
    detail: 'Half-hourly outturn by fuel type, filtered to wind and averaged into hours.',
  },
  {
    name: 'Wind generation forecast (WINDFOR)',
    url: 'https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream',
    detail: 'Published 8 times a day, hourly values, each covering roughly three days ahead.',
  },
]

export function About() {
  return (
    <article className="max-w-prose space-y-6 leading-relaxed">
      <section>
        <h2 className="condensed text-3xl font-semibold">How the numbers are made</h2>
        <p className="mt-3">
          For each hour of a delivery day, the portal uses the latest wind forecast published
          strictly before the decision cutoff on the day before. A forecast published after the
          cutoff, or at the same minute, is never used, so the accuracy figures match what a buyer
          could really have known.
        </p>
      </section>

      <section>
        <h3 className="text-lg font-semibold">Scope</h3>
        <p className="mt-2">
          Decisions made from 1 to 31 January 2026, which means delivery days from 2 January to 1
          February. January is GMT, so UK time and UTC are the same throughout.
        </p>
      </section>

      <section>
        <h3 className="text-lg font-semibold">Cutoffs</h3>
        <p className="mt-2">
          The default is 09:20, the EPEX day-ahead hourly auction. You can switch to N2EX at 09:50,
          EPEX half-hourly at 15:30, or any custom time.
        </p>
      </section>

      <section>
        <h3 className="text-lg font-semibold">Metrics</h3>
        <p className="mt-2">
          Error is forecast minus actual, so a positive error means wind fell short. The buffer is
          the 90th percentile of hourly shortfalls, counting hours where wind beat the forecast as
          zero. Percentage error uses average wind output as the base, because plain percentage
          error becomes meaningless when wind is close to zero.
        </p>
      </section>

      <section>
        <h3 className="text-lg font-semibold">Data sources</h3>
        <ul className="mt-2 space-y-3">
          {SOURCES.map((source) => (
            <li key={source.name}>
              <a className="font-semibold text-forecast underline" href={source.url}>
                {source.name}
              </a>
              <p className="text-muted">{source.detail}</p>
            </li>
          ))}
        </ul>
        <p className="mt-3 text-muted">
          Both come from Elexon's open Insights API. The portal serves a saved snapshot, so it keeps
          working if Elexon is unavailable.
        </p>
      </section>

      <section>
        <h3 className="text-lg font-semibold">Known limitations</h3>
        <p className="mt-2">
          The forecast runs well above actual output across January. A likely reason, not yet
          confirmed, is curtailment: on windy days wind farms are often paid to reduce output when
          the grid can't carry the power, so delivered wind falls below what the weather allowed.
          The figures cover one month, so they show this winter's pattern rather than a year-round
          one.
        </p>
      </section>
    </article>
  )
}
