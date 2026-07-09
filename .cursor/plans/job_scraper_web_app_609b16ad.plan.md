---
name: Job Scraper Web App
overview: Extend the existing Python scraper at c:\Scraping-tool with a FastAPI backend and a responsive React frontend. Users can trigger LinkedIn/Wuzzuf scrapes, track progress, browse/filter saved jobs, export CSV/JSON, and schedule recurring scrapes.
todos:
  - id: backend-foundation
    content: Add FastAPI app, SQLite models (jobs, scrape_runs, schedules), and extract ScraperService from main.py
    status: completed
  - id: api-routes
    content: "Implement REST endpoints: categories, scrapes (start/status/history), jobs (filter/paginate), exports (CSV/JSON), CSV import"
    status: completed
  - id: scraper-tweaks
    content: Add source field to JobListing, to_csv in exporter.py, category ID→name mapping on save
    status: completed
  - id: frontend-scaffold
    content: Create React+Vite+Tailwind app in web/ with responsive layout and API proxy
    status: completed
  - id: frontend-scrape
    content: "Build Scrape page: category picker, form, live progress polling"
    status: completed
  - id: frontend-jobs
    content: "Build Jobs page: mobile cards + desktop table, filters, pagination, export buttons"
    status: completed
  - id: scheduler
    content: Add APScheduler service + Schedules page for recurring scrapes
    status: completed
  - id: history-polish
    content: Build History page, error/empty states, README with local run instructions
    status: completed
isProject: false
---

# Job Scraper Web App Plan

## Context

You already have a working CLI scraper at [`c:\Scraping-tool`](c:\Scraping-tool):

- [`scrapers/linkedin.py`](c:\Scraping-tool\scrapers\linkedin.py) and [`scrapers/wuzzuf.py`](c:\Scraping-tool\scrapers\wuzzuf.py) use Playwright
- [`models.py`](c:\Scraping-tool\models.py) defines the `JobListing` schema
- [`categories.json`](c:\Scraping-tool\categories.json) provides a parent/child category tree (e.g. Creative & Design → Graphic Design)
- Sample output [`creative_and_design_jobs_final.csv`](c:\Scraping-tool\creative_and_design_jobs_final.csv) has **496 jobs** with columns: `title, description, salary, type, company, category, country, applyLink, location, status`

The web app will **wrap this existing logic**, not replace it. The CLI in [`main.py`](c:\Scraping-tool\main.py) stays usable.

---

## Target Architecture

```mermaid
flowchart TB
    subgraph frontend [React Frontend - responsive]
        ScrapePage[Scrape Form]
        JobsPage[Jobs Browser]
        HistoryPage[Scrape History]
        SchedulePage[Scheduled Scrapes]
    end

    subgraph backend [FastAPI Backend]
        API[REST API]
        ScraperSvc[ScraperService]
        Scheduler[APScheduler]
        DB[(SQLite DB)]
    end

    subgraph existing [Existing Python Scrapers]
        LinkedIn[LinkedInScraper]
        Wuzzuf[WuzzufScraper]
        Playwright[Playwright Chromium]
    end

    ScrapePage --> API
    JobsPage --> API
    HistoryPage --> API
    SchedulePage --> API
    API --> ScraperSvc
    API --> DB
    Scheduler --> ScraperSvc
    ScraperSvc --> LinkedIn
    ScraperSvc --> Wuzzuf
    LinkedIn --> Playwright
    Wuzzuf --> Playwright
    ScraperSvc --> DB
```

---

## Proposed Project Structure

Add these folders/files alongside existing code:

```
c:\Scraping-tool\
├── api/
│   ├── main.py                 # FastAPI entry + CORS
│   ├── database.py             # SQLAlchemy + SQLite
│   ├── models_db.py            # ScrapeRun, Job, ScheduledScrape tables
│   ├── schemas.py              # Pydantic request/response models
│   ├── routes/
│   │   ├── categories.py       # GET /categories (from categories.json)
│   │   ├── scrapes.py          # POST /scrapes, GET /scrapes/{id}
│   │   ├── jobs.py             # GET /jobs with filters + pagination
│   │   ├── exports.py          # GET /exports/csv|json
│   │   └── schedules.py        # CRUD scheduled scrapes
│   └── services/
│       ├── scraper_service.py  # Wraps existing scrapers + dedupe
│       └── scheduler_service.py
├── web/                        # React + Vite + Tailwind
│   ├── src/pages/
│   │   ├── ScrapePage.tsx
│   │   ├── JobsPage.tsx
│   │   ├── HistoryPage.tsx
│   │   └── SchedulesPage.tsx
│   └── src/components/
│       ├── CategoryPicker.tsx
│       ├── JobCard.tsx
│       ├── JobTable.tsx
│       └── ScrapeProgress.tsx
├── scrapers/                   # existing (minor tweaks)
├── models.py                   # existing JobListing
├── categories.json             # existing
└── main.py                     # existing CLI (unchanged)
```

---

## Data Model

### Jobs table (persist scraped results)

| Column | Source | Notes |
|--------|--------|-------|
| id | auto | Primary key |
| title, description, salary, type, company, category, country, applyLink, location, status | `JobListing` | Match CSV schema exactly |
| source | new | `linkedin` or `wuzzuf` |
| scrape_run_id | new | FK to scrape session |
| scraped_at | new | Timestamp |

**Dedup rule:** unique on `applyLink` (same as CLI `seen_links` logic in [`main.py`](c:\Scraping-tool\main.py) lines 80-103).

### Scrape runs table (history + progress)

| Column | Purpose |
|--------|---------|
| id, status | `queued`, `running`, `completed`, `failed` |
| config | JSON: categories, location, pages, platforms |
| progress | current category, jobs found, error message |
| started_at, finished_at | timing |

### Scheduled scrapes table

| Column | Purpose |
|--------|---------|
| id, name, enabled | user-defined schedule |
| cron_expression | e.g. `0 8 * * 1` (every Monday 8am) |
| config | same shape as manual scrape form |

---

## Backend Implementation

### 1. Extract shared scraping logic from CLI

Refactor [`main.py`](c:\Scraping-tool\main.py) into a reusable `ScraperService` so both CLI and API call the same code:

```python
# api/services/scraper_service.py (conceptual)
def run_scrape(config, on_progress) -> ScrapeResult:
    # load categories from categories.json
    # launch Playwright (headless)
    # for each category: scrape Wuzzuf + LinkedIn
    # dedupe by applyLink
    # persist jobs + update scrape_run progress
```

- Run Playwright in a **thread pool** (`asyncio.to_thread`) because existing scrapers use sync Playwright API
- Emit progress callbacks so the API can update `scrape_runs.progress`
- Add `source` field to `JobListing` (small change in [`models.py`](c:\Scraping-tool\models.py))

### 2. FastAPI endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/categories` | Return parent → children tree from `categories.json` |
| `POST /api/scrapes` | Start scrape (returns `scrape_run_id`) |
| `GET /api/scrapes` | List past runs (history page) |
| `GET /api/scrapes/{id}` | Status + progress (polled every 2-3s while running) |
| `GET /api/jobs` | Paginated jobs with filters: `q`, `source`, `category`, `company`, `location`, `scrape_run_id`, date range |
| `GET /api/jobs/{id}` | Full job detail (long descriptions) |
| `GET /api/exports/csv` | Download filtered jobs as CSV (same columns as sample) |
| `GET /api/exports/json` | Download filtered jobs as JSON |
| `POST /api/import/csv` | One-time import of existing `creative_and_design_jobs_final.csv` |
| `GET/POST/PATCH/DELETE /api/schedules` | Manage scheduled scrapes |

### 3. Scheduled scraping

Use **APScheduler** started on FastAPI app startup:

- Load enabled schedules from DB
- On trigger: create a new `scrape_run` and call `ScraperService.run_scrape`
- Expose cron presets in UI: daily, weekly, custom

### 4. Minor scraper improvements

- Add `source` tagging in [`linkedin.py`](c:\Scraping-tool\scrapers\linkedin.py) and [`wuzzuf.py`](c:\Scraping-tool\scrapers\wuzzuf.py)
- Extend [`exporter.py`](c:\Scraping-tool\exporter.py) with `to_csv()` (currently JSON-only) for API export reuse
- Map category IDs to names on save (reuse logic from [`map_categories.py`](c:\Scraping-tool\map_categories.py))

### 5. New Python dependencies

Add to [`requirements.txt`](c:\Scraping-tool\requirements.txt):

```
fastapi
uvicorn[standard]
sqlalchemy
apscheduler
python-multipart
```

---

## Frontend Implementation (Mobile + Desktop)

**Stack:** React + Vite + Tailwind CSS (responsive-first, no separate mobile app needed).

### Pages

1. **Scrape** (`/`)
   - Parent category dropdown → multi-select subcategories (from `categories.json` tree)
   - Free-text keyword override (optional)
   - Location (default: Egypt), pages per platform, platform toggles (LinkedIn / Wuzzuf)
   - "Start Scrape" button → live progress panel (status, current category, job count)
   - Disable form while scrape is running

2. **Jobs** (`/jobs`)
   - **Mobile:** stacked `JobCard` components (title, company, location, source badge, expand for description)
   - **Desktop:** sortable table with truncated description + row click for detail drawer/modal
   - Filters: search box, source, category, company, location, date
   - Pagination (25/50 per page)
   - Export CSV / JSON buttons (respects active filters)

3. **History** (`/history`)
   - List of past scrape runs with status, duration, jobs found, config summary
   - Click a run → filter Jobs page to that run

4. **Schedules** (`/schedules`)
   - Create/edit/delete recurring scrapes
   - Enable/disable toggle
   - Show last run + next run time

### Responsive design rules

- Single-column layout below `md` breakpoint; sidebar nav collapses to bottom tab bar on mobile
- Touch-friendly buttons (min 44px tap targets)
- Job descriptions in scrollable panels (avoid page overflow from long text like in sample CSV)
- Sticky filter bar on Jobs page

---

## Data Flow for a Manual Scrape

```mermaid
sequenceDiagram
    participant User
    participant UI as React UI
    participant API as FastAPI
    participant Svc as ScraperService
    participant PW as Playwright
    participant DB as SQLite

    User->>UI: Submit scrape form
    UI->>API: POST /api/scrapes
    API->>DB: Create scrape_run (queued)
    API-->>UI: scrape_run_id
    API->>Svc: run_scrape (background task)
    Svc->>DB: status = running
    loop Each category
        Svc->>PW: Wuzzuf + LinkedIn scrape
        Svc->>DB: Insert new jobs, update progress
        UI->>API: GET /api/scrapes/{id} (poll)
        API-->>UI: progress update
    end
    Svc->>DB: status = completed
    UI->>API: GET /api/jobs?scrape_run_id=...
    API-->>UI: Job results
```

---

## Implementation Phases

### Phase 1 — Backend foundation (days 1-2)
- SQLite schema + SQLAlchemy models
- `ScraperService` extracted from CLI
- Core API: categories, start scrape, poll status, list jobs
- Import existing sample CSV into DB for immediate UI testing

### Phase 2 — Frontend MVP (days 2-4)
- Vite + React + Tailwind scaffold in `web/`
- Scrape form + progress polling
- Jobs browser with filters, cards/table responsive layout
- CSV/JSON export

### Phase 3 — History + schedules (days 4-5)
- History page wired to scrape runs
- APScheduler integration
- Schedules CRUD UI

### Phase 4 — Polish + hardening (day 5-6)
- Error states (LinkedIn blocked, timeout, empty results)
- Loading skeletons, empty states
- README with run instructions
- Optional: serve React build from FastAPI static files for single-command deploy

---

## Running Locally (target developer experience)

```bash
# Terminal 1 — API
cd c:\Scraping-tool
.\venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
uvicorn api.main:app --reload --port 8000

# Terminal 2 — Frontend
cd c:\Scraping-tool\web
npm install
npm run dev
```

- API: `http://localhost:8000`
- UI: `http://localhost:5173` (proxies `/api` to backend)

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| LinkedIn blocks headless scraping | Show clear error in UI; add retry + delay; allow Wuzzuf-only runs |
| Scrapes take minutes (per-job description fetch) | Background jobs + progress polling; don't block HTTP request |
| Long multiline descriptions break CSV | Use pandas `to_csv` with proper quoting (already proven in sample CSV) |
| Playwright not installed on new machine | Document `playwright install chromium` in README |
| Duplicate jobs across runs | Enforce unique `applyLink` in DB |

---

## Out of Scope (for v1)

- User authentication / multi-tenant access
- Cloud deployment (can add later: Docker + Railway/Render)
- LinkedIn login / authenticated scraping
- Real-time WebSockets (polling is sufficient for v1)
