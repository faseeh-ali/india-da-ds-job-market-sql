# India DA/DS Job Market: A SQL Analysis

I built this to answer a question I had for myself: **what do Indian companies
actually ask for in Data Analyst / Data Scientist job postings, and does it
differ by city?** I'm a 2025 B.Tech (AI & Data Science) grad job-hunting for
DA/Junior DS roles, and I wanted real answers to guide my own upskilling.

## What this is
- A normalized MySQL schema (`jobs`, `skills`, `job_skills`) built from two
  intentionally different-vintage sources of real Indian job postings.
- A keyword-matching skill extractor (no heavyweight NLP — a curated
  dictionary + regex word-boundary matching, which is transparent, fast to
  debug, and good enough for this problem).
- SQL analysis using window functions, self-joins, and a full-outer-join-style
  comparison to answer four questions:
  1. Which skills matter most **in each city**? (RANK() PARTITION BY city)
  2. Which skills travel together in the same listing? (self-join co-occurrence)
  3. **What changed between 2022 and 2026?** (the centerpiece — see below)
  4. What's the overall reach of each skill across all postings?

## The actual point of this project
I originally planned to just scrape/pull enough live postings for volume.
Then I realized: 8 live postings blended into a 200-row archival dataset
doesn't add statistical power — they're a rounding error either way. So
instead of pretending that merge was about "more data," I kept the two
sources **deliberately separate and dated**:

- `source = 'indeed_2026'` — 8 postings pulled live via the Indeed API, current.
- `source = 'kaggle_2022'` — a public Kaggle dataset of Indian DS/DA/ML
  postings scraped in July 2022.

That ~4-year gap is the actual finding: **which skills gained or lost share
of Indian DA/DS postings between 2022 and 2026?** My live 2026 pull already
surfaced terms like RAG, LLM fine-tuning, and Agentic AI (Cisco's posting) —
terms that essentially didn't exist in mainstream job ads in 2022. That's a
concrete, defensible, interview-ready claim, backed by a query (`03_advanced_queries.sql`,
Query 5) rather than a vibe.

## Architecture
```
raw_jobs_seed.csv → extract_skills.py → jobs_clean.csv / skills.csv / job_skills.csv
                                              ↓
                                    MySQL (01_schema.sql, 02_load_data.sql)
                                              ↓
                                  03_advanced_queries.sql (analysis)
```

## Findings (from the actual dataset — 1,595 postings: 1,583 archival + 12 live)

**1. Skill demand by city (major hubs only — smaller cities in the dataset
have too few postings, sometimes just 1-2, to draw conclusions from):**

| City | #1 skill | #2 | #3 |
|---|---|---|---|
| Bangalore | Machine Learning (129) | SQL (32) | Deep Learning (30) |
| Hyderabad | Machine Learning (23) | Python (13) | SQL / Excel (11) |
| Mumbai | Machine Learning (11) | Python (8) | SQL (7) |
| Pune | Machine Learning (16) | Python (7) | SQL (6) |
| Delhi/NCR (Delhi+Gurgaon+Noida) | Machine Learning | SQL | Python |

Machine Learning tops every city — expected, given this dataset skews
Data Science-heavy (source dataset name includes "ML"). SQL and Python are
consistently #2/#3 everywhere, which is the more actionable takeaway for a
Data Analyst specifically: **SQL and Python are non-negotiable baseline
skills across every major Indian tech hub in this dataset, not city-specific
preferences.**

**2. Skill co-occurrence (self-join, whole dataset):**
The strongest pairs: Deep Learning + Machine Learning (8.1% of postings),
Machine Learning + Python (7.4%), Python + SQL (5.0%), Python + R (4.1%).
Practical read: if a posting asks for Python, it's asking for SQL almost
as often as it's asking for more Python-adjacent tools like NumPy/Pandas —
reinforcing SQL as a cross-cutting requirement rather than a DA-only skill.

**3. 2022 → 2026 shift (the centerpiece finding):**
Comparing the 2022 archival data against 12 live 2026 postings: **SQL,
Python, Power BI, and Statistics all show large gains in the % of postings
requiring them (SQL: 5.1%→83.3%, Python: 5.4%→75.0%)** — though part of
this gap likely reflects that the 2026 postings have longer, fuller job
descriptions than the 2022 dataset's summaries, not purely rising demand
(see caveat below). The genuinely new signal: **LLM, RAG, Vector Database,
Fine-tuning, Generative AI, and Prompt Engineering are entirely absent
(0.0%) from the 2022 data and present in 8-17% of 2026 postings** — these
are categories of skill that essentially didn't exist in mainstream Indian
DA/DS job postings four years ago.

**Honest caveats on all of the above:**
- The 2026 side is only 12 postings — individual percentages there can
  swing 8+ points from a single additional posting. Treat 2026 numbers as
  directional, not precise.
- The 2022 and 2026 data came from different collection methods (archival
  scrape vs. live API pull with fuller text), which is a partial confound
  for the magnitude of the SQL/Python jump — though it does not explain
  away the LLM/RAG/Generative AI skills, which are categorically new, not
  just more frequently mentioned.

## How to run it
```bash
python3 scripts/extract_skills.py
mysql -u root -p < sql/01_schema.sql
mysql --local-infile=1 -u root -p india_job_market < sql/02_load_data.sql
mysql -u root -p india_job_market < sql/03_advanced_queries.sql
```

## What I'd add next
- Pull more 2026 postings (15-20 more) to tighten the comparison percentages
- Add city-level breakdown to the 2022-vs-2026 comparison, not just national
- A small Streamlit/Power BI dashboard on top of the MySQL views (optional —
  the SQL is the point of this project, not the dashboard)
