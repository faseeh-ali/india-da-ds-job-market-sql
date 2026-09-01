USE india_job_market;

-- ============================================================
-- QUERY 1: Top skills ranked WITHIN each city (window function)
-- Business question: "What should I prioritize learning if I'm
-- job-hunting specifically in Bangalore vs Hyderabad?"
-- ============================================================
WITH skill_city_counts AS (
    SELECT
        j.city,
        s.skill_name,
        COUNT(*) AS demand_count
    FROM job_skills js
    JOIN jobs j   ON js.job_id = j.job_id
    JOIN skills s ON js.skill_id = s.skill_id
    GROUP BY j.city, s.skill_name
),
ranked AS (
    SELECT
        city,
        skill_name,
        demand_count,
        RANK() OVER (PARTITION BY city ORDER BY demand_count DESC) AS city_rank
    FROM skill_city_counts
)
SELECT city, skill_name, demand_count, city_rank
FROM ranked
WHERE city_rank <= 5
ORDER BY city, city_rank;


-- ============================================================
-- QUERY 2: Skill co-occurrence via self-join
-- Business question: "If a listing wants SQL, what's it most
-- likely to also want?" — tells you which skills to bundle when
-- upskilling, not just which to learn in isolation.
-- ============================================================
SELECT
    s1.skill_name AS skill_a,
    s2.skill_name AS skill_b,
    COUNT(*) AS co_occurrence_count,
    ROUND(
        100.0 * COUNT(*) / (SELECT COUNT(DISTINCT job_id) FROM job_skills), 1
    ) AS pct_of_all_postings
FROM job_skills js1
JOIN job_skills js2
    ON js1.job_id = js2.job_id
    AND js1.skill_id < js2.skill_id        -- avoid double-counting (A,B)/(B,A) and self-pairs
JOIN skills s1 ON js1.skill_id = s1.skill_id
JOIN skills s2 ON js2.skill_id = s2.skill_id
GROUP BY s1.skill_name, s2.skill_name
ORDER BY co_occurrence_count DESC
LIMIT 15;


-- ============================================================
-- QUERY 2b: Co-occurrence anchored to ONE specific skill (e.g. SQL)
-- More interview-ready framing: "X% of listings requiring SQL also require Y"
-- ============================================================
SELECT
    s2.skill_name AS paired_with_sql,
    COUNT(*) AS co_occurrence_count,
    ROUND(
        100.0 * COUNT(*) / (
            SELECT COUNT(*) FROM job_skills js
            JOIN skills s ON js.skill_id = s.skill_id
            WHERE s.skill_name = 'SQL'
        ), 1
    ) AS pct_of_sql_postings
FROM job_skills js1
JOIN skills s1 ON js1.skill_id = s1.skill_id AND s1.skill_name = 'SQL'
JOIN job_skills js2 ON js1.job_id = js2.job_id AND js2.skill_id != js1.skill_id
JOIN skills s2 ON js2.skill_id = s2.skill_id
GROUP BY s2.skill_name
ORDER BY co_occurrence_count DESC;


-- ============================================================
-- QUERY 3: Skill demand trend over time (month-over-month)
-- Business question: "Is demand for skill X rising or falling?"
-- NOTE: needs a wide enough date range / volume to be meaningful —
-- this is the query most worth re-running after merging in the
-- Kaggle dataset for scale (see README).
-- ============================================================
SELECT
    DATE_FORMAT(j.posted_date, '%Y-%m') AS posting_month,
    s.skill_name,
    COUNT(*) AS mentions,
    RANK() OVER (
        PARTITION BY DATE_FORMAT(j.posted_date, '%Y-%m')
        ORDER BY COUNT(*) DESC
    ) AS month_rank
FROM job_skills js
JOIN jobs j   ON js.job_id = j.job_id
JOIN skills s ON js.skill_id = s.skill_id
GROUP BY posting_month, s.skill_name
ORDER BY posting_month, month_rank;


-- ============================================================
-- QUERY 5 (THE CENTERPIECE): 2022 vs 2026 — which skills emerged,
-- which faded, in Indian DA/DS job postings.
-- Business question: "What changed in what companies actually ask
-- for, over ~4 years?" This is the finding that's genuinely hard
-- to find in someone else's portfolio project, because it requires
-- combining an archival dataset with a freshly-pulled one on purpose.
--
-- source = 'kaggle_2022'  -> archival Kaggle scrape (~2022)
-- source = 'indeed_2026'  -> live Indeed API pull (current)
-- ============================================================
WITH skill_share_by_era AS (
    SELECT
        j.source AS era,
        s.skill_name,
        COUNT(DISTINCT js.job_id) AS postings_with_skill,
        (SELECT COUNT(*) FROM jobs WHERE source = j.source) AS total_postings_in_era,
        ROUND(
            100.0 * COUNT(DISTINCT js.job_id) /
            (SELECT COUNT(*) FROM jobs WHERE source = j.source), 1
        ) AS pct_of_era
    FROM job_skills js
    JOIN jobs j   ON js.job_id = j.job_id
    JOIN skills s ON js.skill_id = s.skill_id
    GROUP BY j.source, s.skill_name
),
e2022 AS (SELECT * FROM skill_share_by_era WHERE era = 'kaggle_2022'),
e2026 AS (SELECT * FROM skill_share_by_era WHERE era = 'indeed_2026')
-- MySQL has no native FULL OUTER JOIN, so this is a LEFT JOIN unioned
-- with the mirror LEFT JOIN, which together cover both sides.
SELECT
    COALESCE(e2022.skill_name, e2026.skill_name) AS skill_name,
    COALESCE(e2022.pct_of_era, 0) AS pct_in_2022,
    COALESCE(e2026.pct_of_era, 0) AS pct_in_2026,
    COALESCE(e2026.pct_of_era, 0) - COALESCE(e2022.pct_of_era, 0) AS pct_point_change
FROM e2022
LEFT JOIN e2026 ON e2022.skill_name = e2026.skill_name
UNION
SELECT
    COALESCE(e2022.skill_name, e2026.skill_name),
    COALESCE(e2022.pct_of_era, 0),
    COALESCE(e2026.pct_of_era, 0),
    COALESCE(e2026.pct_of_era, 0) - COALESCE(e2022.pct_of_era, 0)
FROM e2026
LEFT JOIN e2022 ON e2022.skill_name = e2026.skill_name
ORDER BY pct_point_change DESC;


-- ============================================================
-- QUERY 4: Skill "reach" — % of ALL postings requiring each skill
-- Simple but the number you'll actually quote in interviews.
-- ============================================================
SELECT
    s.skill_name,
    COUNT(DISTINCT js.job_id) AS postings_requiring,
    (SELECT COUNT(*) FROM jobs) AS total_postings,
    ROUND(100.0 * COUNT(DISTINCT js.job_id) / (SELECT COUNT(*) FROM jobs), 1) AS pct_of_postings
FROM job_skills js
JOIN skills s ON js.skill_id = s.skill_id
GROUP BY s.skill_name
ORDER BY pct_of_postings DESC;
