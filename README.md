# Wind forecast decision portal

**Live app: https://qv7tmz.vercel.app**

A web portal for a GB energy buyer's day-ahead team. For every delivery day from 2 January to 1 February 2026, it shows the national wind forecast that was actually available at auction time and what the wind really did. It also measures how wrong those forecasts were across the month, so the team can size a safety buffer.

## Key findings

| Decision cutoff (D−1, UK time) | Forecast used | Average miss | Bias (forecast minus actual) | Buffer for 90% of hours |
|---|---|---|---|---|
| 09:20, EPEX day-ahead 60 min | 07:30 publish | 2,039 MW | +1,748 MW | 4,098 MW |
| 09:50, N2EX day-ahead | 09:30 publish | 2,013 MW | +1,730 MW | 4,144 MW |

- The forecast ran high across January: wind came in about 1,700 MW below it on average, which leaves a buyer short.
- Waiting from 09:20 to 09:50 for a newer forecast barely helps. The average miss improves by about 1%, and the buffer needed does not shrink.
- A likely cause of the bias is curtailment on windy days (wind farms paid to reduce output). This is not confirmed and is listed as a limitation.

## How to run it

### With Docker (one command)

```bash
docker compose up --build
```

Then open http://localhost:8080. The API is also available at http://localhost:8000, with interactive docs at http://localhost:8000/docs.

### Without Docker

Backend (Python 3.11 or newer), from `backend/`:

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m uvicorn app.main:app --reload
```

Frontend (Node 20 or newer), from `frontend/`, in a second terminal:

```bash
npm install
npm run dev
```

Then open http://localhost:5173. The development server forwards `/api` calls to the backend on port 8000.

### Refresh the data

The repo includes a saved snapshot of the Elexon data in `backend/data/`, so the app never depends on Elexon being up. To download it again, from `backend/`:

```bash
python ingest.py --refresh
```

### Run the tests

```bash
cd backend && python -m pytest
```

GitHub Actions runs the backend tests, `ruff` and `black`, plus the frontend lint, format check and build, on every push.

## Files and directories

```
qv7tmz/
├── backend/
│   ├── app/
│   │   ├── config.py        Scope dates, auction cutoffs, Elexon base URL
│   │   ├── elexon.py        Downloads FUELHH and WINDFOR, with retries
│   │   ├── forecasting.py   Picks the decision-time forecast and aligns it with actuals
│   │   ├── metrics.py       Error metrics, buffer and chart breakdowns
│   │   ├── service.py       Builds API responses from the snapshot, cached per cutoff
│   │   ├── snapshot.py      Saves and loads the data snapshot
│   │   ├── schemas.py       Pydantic response models
│   │   └── main.py          FastAPI app and the four endpoints
│   ├── data/                Committed snapshot of January 2026 Elexon data
│   ├── tests/               pytest suite, using real Elexon samples as fixtures
│   ├── ingest.py            Builds the snapshot from Elexon
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/           Decision day, Accuracy and Method pages
│   │   ├── components/      Charts, figure row, cutoff control, status messages
│   │   ├── api.ts           Typed client for the backend
│   │   └── format.ts        Number and UK time formatting
│   ├── nginx.conf           Serves the built site and proxies /api in Docker
│   └── Dockerfile
├── api/index.py             Vercel entry point for the backend
├── vercel.json              Vercel build and routing settings
├── requirements.txt         Python packages Vercel installs for the backend
├── docker-compose.yml       Runs backend and frontend together
└── .github/workflows/ci.yml Tests and checks on every push
```

## API

| Endpoint | Returns |
|---|---|
| `GET /api/health` | Status and when the data snapshot was taken |
| `GET /api/delivery-days` | Delivery days in scope and the cutoff options |
| `GET /api/day/{date}?cutoff=09:20` | Hourly forecast, actual, error, publish time and lead time, plus a day summary |
| `GET /api/accuracy?cutoff=09:20` | Month metrics, headline sentence, and data for every chart |

`cutoff` accepts any `HH:MM` time. Dates outside the scope or malformed cutoffs return `422` with a reason.

## Key assumptions and decisions

- **Decision time.** The buying decision for delivery day D is made on D−1. The default cutoff is 09:20 UK time (EPEX day-ahead 60-minute auction), with 09:50 (N2EX), 15:30 (EPEX 30-minute) and custom times available.
- **"Decisions made in January 2026"** means decision dates 1–31 January, so delivery days run from 2 January to 1 February.
- **Strictly before the cutoff.** A forecast counts only if it was published before the cutoff, not at it. WINDFOR publishes at 15:30, the same minute the 15:30 auction closes, and a buyer cannot act on it. Tests prove no later forecast is ever used.
- **Hourly comparison.** WINDFOR is hourly and FUELHH is half-hourly, so each pair of FUELHH half-hours is averaged into an hour. An hour missing one half is excluded rather than averaged from one value.
- **Time zones.** Everything is stored and computed in UTC and shown in UK time. January is GMT, so the two match throughout the scope.
- **Buffer.** The 90th percentile of hourly shortfalls (forecast above actual), with hours where wind beat the forecast counted as zero shortfall.
- **No plain MAPE.** Percentage error uses average wind output as its base, because plain percentage error becomes meaningless when wind is near zero.
- **Snapshot as compressed CSV.** The data is small, and Parquet would need pyarrow, which is large for a serverless function.

## Known limitations

- The large positive bias may come from curtailment rather than forecast quality. Separating the two would need constraint data.
- Lead time and hour of day move together at a fixed cutoff, so the lead-time chart partly reflects time-of-day effects. The app notes this on the chart.
- One month of winter data, so the figures show this January's pattern rather than a year-round one.

## AI tools used

I used **Claude** (Anthropic, in claude.ai) throughout this project to:

- draft the PRD, including the domain research on auction gate closures;
- write most of the code: the backend, the frontend, the tests, and the Docker, Vercel and CI configuration;
- explain the Elexon datasets and help interpret the results.

My own work: I verified the data by making real calls to the Elexon API and checking the responses, made the product decisions (the default cutoff, the strictly-before rule, how to frame the buffer), ran the tests, Docker setup and website on my own laptop at every step, found and reported a bug in the error handling, and deployed the app. I reviewed the code and can explain every part of it.
