-- ============================================================
-- India DA/DS Job Market — Schema
-- Normalized: jobs (fact) + skills (dimension) + job_skills (bridge)
-- Why not one flat table: skills are many-to-many with jobs. A flat
-- table forces repeating rows per skill (breaks jobs-level aggregates
-- like COUNT(DISTINCT job_id)) or a comma-packed skills column (breaks
-- every SQL feature you want to show off: joins, RANK, self-joins).
-- ============================================================

CREATE DATABASE IF NOT EXISTS india_job_market;
USE india_job_market;

DROP TABLE IF EXISTS job_skills;
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS skills;

CREATE TABLE jobs (
    job_id       VARCHAR(50)  PRIMARY KEY,
    title        VARCHAR(255) NOT NULL,
    company      VARCHAR(255),
    city         VARCHAR(100),
    posted_date  DATE,
    job_type     VARCHAR(50),
    source       VARCHAR(50),          -- 'indeed_api' or 'kaggle'
    INDEX idx_city (city),
    INDEX idx_posted_date (posted_date)
);

CREATE TABLE skills (
    skill_id     INT PRIMARY KEY,
    skill_name   VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE job_skills (
    job_id       VARCHAR(50) NOT NULL,
    skill_id     INT NOT NULL,
    PRIMARY KEY (job_id, skill_id),
    FOREIGN KEY (job_id)   REFERENCES jobs(job_id)   ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE,
    INDEX idx_skill (skill_id)
);
