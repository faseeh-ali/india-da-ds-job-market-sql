-- ============================================================
-- Load cleaned CSVs into MySQL.
-- Run from the mysql CLI with --local-infile=1, e.g.:
--   mysql --local-infile=1 -u root -p india_job_market < sql/02_load_data.sql
-- Adjust the file paths to wherever you cloned the repo.
-- ============================================================

USE india_job_market;

LOAD DATA LOCAL INFILE 'data/jobs_clean.csv'
INTO TABLE jobs
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(job_id, title, company, city, posted_date, job_type, source);

LOAD DATA LOCAL INFILE 'data/skills.csv'
INTO TABLE skills
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(skill_id, skill_name);

LOAD DATA LOCAL INFILE 'data/job_skills.csv'
INTO TABLE job_skills
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(job_id, skill_id, @skill_name_ignored);

-- Sanity checks
SELECT COUNT(*) AS total_jobs FROM jobs;
SELECT COUNT(*) AS total_skills FROM skills;
SELECT COUNT(*) AS total_links FROM job_skills;
