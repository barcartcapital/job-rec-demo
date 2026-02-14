---
title: "feat: Job Recommendation Demo with Content-Based Filtering"
type: feat
date: 2026-02-13
---

# Job Recommendation Demo with Content-Based Filtering

## Overview

Build a job recommendation system demo with two components: a **Jupyter notebook** for model development/evaluation and a **Next.js web app** for live presentation. The system ingests jobs from the Workable XML feed, builds two recommendation models (baseline vs. weighted multi-feature), and lets a live audience compare recommendations side-by-side.

## Problem Statement / Motivation

When a user views a single job listing, showing relevant "similar jobs" increases engagement and helps candidates discover roles they might not have found through search alone. This demo compares a naive baseline (title-only cosine similarity) against a weighted multi-feature approach (TF-IDF on descriptions + structured feature matching) to demonstrate the value of richer content-based filtering.

## Data Source

**Feed:** `https://www.workable.com/boards/workable.xml`
**Total jobs available:** ~177,000
**Sample size for demo:** 1,000 jobs (diverse sample across categories)

### XML Schema (per `<job>` element)

| Field | Type | Notes |
|---|---|---|
| `title` | CDATA string | Job title, sometimes includes location |
| `date` | CDATA string | Publication date |
| `referencenumber` | CDATA string | Unique ID (e.g., `F44ED9E40A`) |
| `url` | CDATA string | Apply URL on Workable |
| `company` | CDATA string | Employer name |
| `city` | CDATA string | City |
| `state` | CDATA string | State/province |
| `country` | CDATA string | 2-letter country code |
| `remote` | CDATA string | `"true"` or `"false"` |
| `postalcode` | CDATA string | Often empty |
| `description` | CDATA string | **HTML content** - full job description |
| `education` | CDATA string | e.g., "Bachelor's Degree", can be empty |
| `jobtype` | CDATA string | e.g., "Full-time", "Contract" |
| `category` | CDATA string | e.g., "Information Technology", "General Business" |
| `experience` | CDATA string | e.g., "Entry level", "Mid-Senior level", can be empty |
| `website` | CDATA string | Company website URL |

### Job Data Model

```python
@dataclass
class Job:
    id: str              # referencenumber
    title: str
    company: str
    city: str
    state: str
    country: str
    remote: bool
    description: str     # raw HTML
    description_clean: str  # cleaned plain text (derived)
    education: str
    job_type: str        # jobtype
    category: str
    experience: str
    url: str
    date: str
```

---

## Proposed Solution

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Jupyter Notebook                     │
│                                                       │
│  1. Download & cache XML feed locally                │
│  2. Parse XML -> Job objects (sample 1,000)          │
│  3. Clean HTML descriptions (BeautifulSoup)          │
│  4. Preprocess text (lowercase, remove stopwords)    │
│  5. Build TF-IDF matrices (titles + descriptions)    │
│  6. Compute Baseline recs (title cosine similarity)  │
│  7. Compute Weighted recs (multi-feature scoring)    │
│  8. Evaluate & compare models                        │
│  9. Export JSON files for web app                    │
│                                                       │
│  Output files:                                       │
│  ├── jobs.json          (all job metadata + desc)    │
│  ├── recs_baseline.json (top-3 per job, title-only)  │
│  └── recs_weighted.json (top-3 per job, weighted)    │
└──────────────────┬──────────────────────────────────┘
                   │ copy to public/data/
                   v
┌─────────────────────────────────────────────────────┐
│                 Next.js Web App                       │
│                                                       │
│  /                  Job listing with search/filters  │
│  /jobs/[id]         Job detail + 2 rec groups        │
│                                                       │
│  Static export -> Vercel deployment                  │
└─────────────────────────────────────────────────────┘
```

---

## Phase 1: Jupyter Notebook

### 1.1 Setup & Data Ingestion

**File:** `notebook/job_recommendations.ipynb`

- [ ] Create `notebook/` directory with `requirements.txt`
- [ ] Cell 1: Install dependencies, imports
- [ ] Cell 2: Download XML feed via `requests` and save to `notebook/data/workable_feed.xml` (cache locally, skip re-download if file exists)
- [ ] Cell 3: Parse XML using `lxml.etree.iterparse` with element clearing for constant memory usage
- [ ] Cell 4: Load into a pandas DataFrame, display shape and sample rows
- [ ] Cell 5: Sample 1,000 jobs with diversity — stratified sample across `category` to ensure good representation

**Dependencies (`notebook/requirements.txt`):**
```
lxml>=5.0
beautifulsoup4>=4.12
scikit-learn>=1.4
pandas>=2.1
numpy>=1.26
matplotlib>=3.8
seaborn>=0.13
tqdm>=4.66
requests>=2.31
```

**Key consideration:** The feed is ~177K jobs and the XML file will be large. Download once, cache locally. If rate-limited (HTTP 1015), the notebook should handle this gracefully with a retry or instructions to download manually via browser.

### 1.2 Data Cleaning & Preprocessing

- [ ] Cell 6: Clean HTML from descriptions using BeautifulSoup — strip tags, remove URLs/emails, normalize whitespace
- [ ] Cell 7: Text preprocessing — lowercase, remove stopwords (sklearn's English list + domain-specific like "apply", "experience", "preferred", "required"), no heavy NLP (skip spaCy/lemmatization to keep Google Colab dependencies light)
- [ ] Cell 8: Handle missing/empty fields — fill empty `category` with "Other", empty `experience` with "Not Specified", empty `education` with "Not Specified"
- [ ] Cell 9: Display cleaned data statistics — category distribution, job type distribution, location distribution, description length histogram

### 1.3 Baseline Model (Title-Only Cosine Similarity)

- [ ] Cell 10: Build TF-IDF matrix on job titles only

```python
title_vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    max_features=5000,
    stop_words='english',
    sublinear_tf=True,
)
title_tfidf = title_vectorizer.fit_transform(df['title_clean'])
```

- [ ] Cell 11: Compute cosine similarity matrix (1000x1000 is ~8MB dense, fits in memory)

```python
from sklearn.metrics.pairwise import cosine_similarity
title_sim_matrix = cosine_similarity(title_tfidf)
```

- [ ] Cell 12: Extract top-3 recommendations per job (excluding self)

```python
baseline_recs = {}
for i in range(len(df)):
    scores = title_sim_matrix[i].copy()
    scores[i] = -1  # exclude self
    top_3 = np.argsort(scores)[::-1][:3]
    baseline_recs[df.iloc[i]['id']] = [
        {"id": df.iloc[top_3[j]]['id'], "score": float(scores[top_3[j]])}
        for j in range(3)
    ]
```

- [ ] Cell 13: Spot-check 3-5 example jobs and their baseline recommendations

### 1.4 Weighted Multi-Feature Model

- [ ] Cell 14: Build TF-IDF matrix on cleaned descriptions

```python
desc_vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    max_features=10000,
    max_df=0.85,
    min_df=2,
    stop_words='english',
    sublinear_tf=True,
    dtype=np.float32,
)
desc_tfidf = desc_vectorizer.fit_transform(df['description_clean'])
```

- [ ] Cell 15: Compute individual similarity matrices for each feature

```python
# Description similarity (TF-IDF cosine)
desc_sim = cosine_similarity(desc_tfidf)

# Title similarity (already computed)
# title_sim_matrix

# Category match (binary)
categories = df['category'].values
cat_sim = (categories[:, None] == categories[None, :]).astype(np.float32)

# Location similarity (tiered: same city=1.0, same state=0.5, same country=0.2, else 0.0)
# Vectorized computation using broadcasting
cities = df['city'].values
states = df['state'].values
countries = df['country'].values
loc_sim = np.where(cities[:, None] == cities[None, :], 1.0,
          np.where(states[:, None] == states[None, :], 0.5,
          np.where(countries[:, None] == countries[None, :], 0.2, 0.0)))

# Job type match (binary)
jobtypes = df['job_type'].values
type_sim = (jobtypes[:, None] == jobtypes[None, :]).astype(np.float32)

# Experience level similarity (ordinal distance)
exp_map = {"Entry level": 0, "Associate": 1, "Mid-Senior level": 2,
           "Director": 3, "Executive": 4, "Not Specified": 2}
exp_vals = np.array([exp_map.get(e, 2) for e in df['experience'].values])
exp_dist = np.abs(exp_vals[:, None] - exp_vals[None, :])
exp_sim = 1.0 - (exp_dist / exp_dist.max())
```

- [ ] Cell 16: Combine with weights

```python
WEIGHTS = {
    "description": 0.35,
    "title": 0.25,
    "category": 0.15,
    "location": 0.10,
    "job_type": 0.08,
    "experience": 0.07,
}

weighted_sim = (
    WEIGHTS["description"] * desc_sim +
    WEIGHTS["title"] * title_sim_matrix +
    WEIGHTS["category"] * cat_sim +
    WEIGHTS["location"] * loc_sim.astype(np.float32) +
    WEIGHTS["job_type"] * type_sim +
    WEIGHTS["experience"] * exp_sim.astype(np.float32)
)
```

- [ ] Cell 17: Extract top-3 weighted recommendations per job
- [ ] Cell 18: Spot-check the same 3-5 jobs and compare baseline vs weighted recs

### 1.5 Model Comparison & Evaluation

- [ ] Cell 19: Compute offline metrics for both models

| Metric | What it measures |
|---|---|
| **Mean Recommendation Score** | Average similarity of top-3 recs (higher = more confident matches) |
| **Intra-List Diversity (ILD)** | Average pairwise dissimilarity within each rec list (higher = more diverse) |
| **Catalog Coverage** | % of all jobs appearing in at least one rec list (higher = less popularity bias) |
| **Category Coherence** | % of recs in same category as source job |

- [ ] Cell 20: Visualize comparison — bar charts for each metric, side by side
- [ ] Cell 21: Create a **qualitative comparison panel** — pick 10 diverse jobs (across categories), show source job + top-3 from each model in a formatted table
- [ ] Cell 22: Summary markdown cell with findings and interpretation

### 1.6 Export for Web App

- [ ] Cell 23: Export 3 JSON files to `notebook/output/`

**`jobs.json`** — Array of job objects with all display fields:
```json
[
  {
    "id": "F44ED9E40A",
    "title": "System Engineer",
    "company": "Tech Firefly",
    "city": "Hyderabad",
    "state": "Telangana",
    "country": "IN",
    "remote": false,
    "description": "<p>We are looking for...</p>",
    "category": "Information Technology",
    "jobType": "Contract",
    "experience": "Mid-Senior level",
    "education": "Bachelor's Degree",
    "url": "https://apply.workable.com/j/F44ED9E40A"
  }
]
```

**`recs_baseline.json`** — Map of job ID to top-3 baseline recommendations:
```json
{
  "F44ED9E40A": [
    {"id": "0AA38013AC", "score": 0.82},
    {"id": "8D801CE251", "score": 0.74},
    {"id": "ANOTHER_ID", "score": 0.71}
  ]
}
```

**`recs_weighted.json`** — Same structure for weighted model:
```json
{
  "F44ED9E40A": [
    {"id": "DIFFERENT_ID", "score": 0.91},
    {"id": "0AA38013AC", "score": 0.88},
    {"id": "YET_ANOTHER", "score": 0.85}
  ]
}
```

- [ ] Cell 24: Print file sizes and sanity check (all job IDs in recs exist in jobs.json, each job has exactly 3 recs)

**Size estimates for 1,000 jobs:**
- `jobs.json`: ~2-5 MB (includes full HTML descriptions)
- `recs_baseline.json`: ~50 KB
- `recs_weighted.json`: ~50 KB

---

## Phase 2: Next.js Web App

### 2.1 Project Setup

**Directory:** `web/`

- [ ] Scaffold with `npx create-next-app@latest web --typescript --tailwind --eslint --app --src-dir --no-import-alias`
- [ ] Copy JSON files from `notebook/output/` to `web/public/data/`
- [ ] Configure `next.config.ts` for static export:

```typescript
// web/next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  images: { unoptimized: true },
};

export default nextConfig;
```

### 2.2 Data Layer

**File:** `web/src/lib/data.ts`

- [ ] Type definitions matching the JSON export schema
- [ ] Helper functions to load jobs, baseline recs, and weighted recs
- [ ] For static generation: read JSON files at build time via `fs`
- [ ] For client components: fetch from `/data/` at runtime

```typescript
// web/src/lib/types.ts
export interface Job {
  id: string;
  title: string;
  company: string;
  city: string;
  state: string;
  country: string;
  remote: boolean;
  description: string; // HTML
  category: string;
  jobType: string;
  experience: string;
  education: string;
  url: string;
}

export interface Recommendation {
  id: string;
  score: number;
}
```

### 2.3 Pages & Routing

#### Home Page (`web/src/app/page.tsx`)

- [ ] Server component that loads `jobs.json` at build time
- [ ] Passes job data to a `<JobBrowser>` client component
- [ ] Page title: "Job Recommendation Demo"

#### Job Browser Component (`web/src/components/JobBrowser.tsx`)

- [ ] `'use client'` component
- [ ] **Search bar** — filters jobs by title and company (case-insensitive substring match)
- [ ] **Category filter** — dropdown populated from unique categories in the dataset
- [ ] **Location filter** — dropdown or text input for city/state/country
- [ ] **Job type filter** — dropdown (Full-time, Contract, Part-time, etc.)
- [ ] **Results list** — paginated (20 per page), each item shows title, company, location, category, job type
- [ ] Clicking a job navigates to `/jobs/[id]`

#### Job Detail Page (`web/src/app/jobs/[id]/page.tsx`)

- [ ] Server component with `generateStaticParams` to pre-render all 1,000 job pages
- [ ] Displays: title, company, location (city, state, country), remote badge, job type, experience level, education, category
- [ ] Renders the full HTML description safely (using `dangerouslySetInnerHTML` since we control the source data)
- [ ] "Apply" link to the original Workable URL (opens in new tab)
- [ ] **Two recommendation sections side-by-side:**

```
┌─────────────────────────┬─────────────────────────┐
│   Baseline Model        │   Enhanced Model         │
│   (Title Similarity)    │   (Weighted Features)    │
│                         │                          │
│  ┌───────────────────┐  │  ┌───────────────────┐  │
│  │ Job Card 1        │  │  │ Job Card 1        │  │
│  │ Score: 0.82       │  │  │ Score: 0.91       │  │
│  └───────────────────┘  │  └───────────────────┘  │
│  ┌───────────────────┐  │  ┌───────────────────┐  │
│  │ Job Card 2        │  │  │ Job Card 2        │  │
│  │ Score: 0.74       │  │  │ Score: 0.88       │  │
│  └───────────────────┘  │  └───────────────────┘  │
│  ┌───────────────────┐  │  ┌───────────────────┐  │
│  │ Job Card 3        │  │  │ Job Card 3        │  │
│  │ Score: 0.71       │  │  │ Score: 0.85       │  │
│  └───────────────────┘  │  └───────────────────┘  │
└─────────────────────────┴─────────────────────────┘
```

- [ ] Each recommendation card shows: title, company, location, similarity score (as percentage), link to that job's detail page
- [ ] Visual indicator showing which features contributed to the weighted score (optional stretch)

### 2.4 Components

| Component | File | Purpose |
|---|---|---|
| `JobBrowser` | `web/src/components/JobBrowser.tsx` | Client component: search, filter, paginate jobs |
| `JobCard` | `web/src/components/JobCard.tsx` | Compact job card for listings and recommendations |
| `RecommendationPanel` | `web/src/components/RecommendationPanel.tsx` | Side-by-side model comparison on detail page |
| `SearchBar` | `web/src/components/SearchBar.tsx` | Text input with debounce |
| `FilterDropdown` | `web/src/components/FilterDropdown.tsx` | Reusable select/dropdown for category, type, etc. |
| `Pagination` | `web/src/components/Pagination.tsx` | Page navigation for job list |
| `Badge` | `web/src/components/Badge.tsx` | Small label for category, job type, remote, etc. |

### 2.5 Styling

- [ ] Tailwind CSS (included via create-next-app)
- [ ] Clean, professional look suitable for a presentation
- [ ] Responsive but desktop-first (presentation will be on a large screen)
- [ ] Color-code the two recommendation models so the audience can quickly distinguish them (e.g., blue for baseline, green for enhanced)
- [ ] Show similarity scores as progress bars or percentage badges

### 2.6 Presentation Features

- [ ] Header with project title and brief explanation of what the demo shows
- [ ] On the job detail page, a small info box explaining each model:
  - **Baseline:** "Recommends jobs with similar titles using TF-IDF cosine similarity"
  - **Enhanced:** "Combines description similarity (35%), title (25%), category (15%), location (10%), job type (8%), and experience level (7%)"
- [ ] Highlight differences — if a recommendation appears in one model but not the other, visually emphasize it

---

## Phase 3: Deployment

### 3.1 Build & Deploy to Vercel

- [ ] Run `next build` in `web/` — generates static `out/` directory
- [ ] Verify all 1,000 job pages are generated
- [ ] Deploy via Vercel CLI or Git integration:

```bash
cd web
npx vercel --prod
```

Or connect the GitHub repo and Vercel auto-deploys on push.

### 3.2 Size Budget

| Asset | Estimated Size | Vercel Limit |
|---|---|---|
| `jobs.json` | ~2-5 MB | No per-file limit on static assets |
| `recs_baseline.json` | ~50 KB | - |
| `recs_weighted.json` | ~50 KB | - |
| Static HTML (1,000 pages) | ~5-10 MB | - |
| JS/CSS bundles | ~200 KB | - |
| **Total** | **~8-16 MB** | 100 MB (Hobby plan) |

Well within Vercel's free tier limits.

---

## Technical Considerations

### Memory & Performance

- At 1,000 jobs, all similarity matrices are 1000x1000 = 1M entries. At float32, that's ~4 MB per matrix. 6 feature matrices = ~24 MB. Easily fits in Google Colab's free RAM.
- The full Workable XML is very large. Download once, cache locally. Parse with `lxml.etree.iterparse` using element clearing for constant memory.
- Sampling strategy matters: stratified sampling by `category` ensures the demo dataset has diverse job types, making the recommendation comparison more interesting.

### Edge Cases

- **Empty descriptions:** Some jobs may have minimal descriptions. The TF-IDF vector will be sparse/zero. Handle by ensuring at least the title contributes to the weighted score.
- **Duplicate/near-duplicate jobs:** The feed may contain re-postings. Deduplicate by title+company+city before sampling.
- **Missing fields:** `experience`, `education`, `postalcode` are often empty. Default to neutral values in similarity computation.
- **HTML in descriptions:** The web app renders descriptions with `dangerouslySetInnerHTML`. Since the data comes from Workable's feed (trusted source we control), this is acceptable. The HTML is standard formatting tags (p, ul, li, strong, h3).

### Rate Limiting

The Workable feed may rate-limit requests. The notebook should:
1. Check if the XML file already exists locally before downloading
2. If the download fails, provide instructions to download manually via browser
3. Support loading from a local file path as fallback

---

## Acceptance Criteria

### Notebook
- [ ] Parses Workable XML feed and samples 1,000 diverse jobs
- [ ] Builds baseline model (title-only cosine similarity)
- [ ] Builds weighted model with configurable weights across 6 features
- [ ] Computes 4+ offline comparison metrics between models
- [ ] Includes qualitative comparison panel with 10+ example jobs
- [ ] Exports 3 JSON files ready for the web app
- [ ] Runs end-to-end on Google Colab without errors

### Web App
- [ ] Job listing page with working search and filters
- [ ] Job detail page showing full description
- [ ] Two recommendation groups displayed side-by-side with model labels
- [ ] Each recommendation shows title, company, location, similarity score
- [ ] Navigation between job list and job details
- [ ] Clean, presentation-ready visual design
- [ ] Deploys to Vercel as a static site

### Presentation
- [ ] Models produce visibly different recommendations for many jobs
- [ ] The weighted model generally produces more relevant recommendations
- [ ] A presenter can click through jobs and demonstrate differences live

---

## File Structure

```
job-rec-demo/
├── docs/
│   └── plans/
│       └── 2026-02-13-feat-job-recommendation-demo-plan.md
├── notebook/
│   ├── requirements.txt
│   ├── job_recommendations.ipynb
│   ├── data/                    # gitignored
│   │   └── workable_feed.xml
│   └── output/                  # gitignored (large JSON)
│       ├── jobs.json
│       ├── recs_baseline.json
│       └── recs_weighted.json
├── web/
│   ├── package.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.ts (if needed)
│   ├── public/
│   │   └── data/                # copied from notebook/output/
│   │       ├── jobs.json
│   │       ├── recs_baseline.json
│   │       └── recs_weighted.json
│   └── src/
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── page.tsx
│       │   ├── globals.css
│       │   └── jobs/
│       │       └── [id]/
│       │           └── page.tsx
│       ├── components/
│       │   ├── JobBrowser.tsx
│       │   ├── JobCard.tsx
│       │   ├── RecommendationPanel.tsx
│       │   ├── SearchBar.tsx
│       │   ├── FilterDropdown.tsx
│       │   ├── Pagination.tsx
│       │   └── Badge.tsx
│       └── lib/
│           ├── types.ts
│           └── data.ts
├── .gitignore
└── README.md
```

---

## Implementation Order

1. **Notebook: Data ingestion & cleaning** (Cells 1-9)
2. **Notebook: Baseline model** (Cells 10-13)
3. **Notebook: Weighted model** (Cells 14-18)
4. **Notebook: Evaluation & comparison** (Cells 19-22)
5. **Notebook: JSON export** (Cells 23-24)
6. **Web app: Scaffold & data layer** (Next.js setup, types, data loading)
7. **Web app: Job listing page** (search, filters, pagination)
8. **Web app: Job detail page** (description, recommendation panels)
9. **Web app: Polish** (styling, presentation features, responsive tweaks)
10. **Deploy to Vercel**

---

## Dependencies & Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Workable XML feed rate-limited | Medium | Download once, cache locally. Provide manual download fallback. |
| Feed schema changes | Low | XML parsing handles missing fields gracefully with defaults |
| 1,000 static pages slow build | Low | 1,000 pages is well within Next.js build capacity |
| JSON files too large for Vercel | Very Low | At 1,000 jobs, total data is <16 MB — well under 100 MB limit |
| Google Colab memory limits | Low | 1,000x1,000 matrices are ~4 MB each, total compute ~24 MB |

---

## References

- [scikit-learn TfidfVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
- [scikit-learn cosine_similarity](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.cosine_similarity.html)
- [Next.js Static Exports](https://nextjs.org/docs/app/guides/static-exports)
- [Next.js generateStaticParams](https://nextjs.org/docs/app/api-reference/functions/generate-static-params)
- [Vercel Limits](https://vercel.com/docs/limits)
- [Workable XML Feed](https://www.workable.com/boards/workable.xml)
- [Evaluating Recommender Systems (Evidently AI)](https://www.evidentlyai.com/ranking-metrics/evaluating-recommender-systems)
