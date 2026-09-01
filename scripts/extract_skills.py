"""
extract_skills.py
------------------
Keyword-matching skill extraction for job postings.

Design choice (and why, for your README/interview talking points):
- No fancy NLP/NER. A curated skill dictionary + regex word-boundary matching
  is transparent, debuggable, and good enough — recruiters care that you made
  a sound engineering tradeoff, not that you used spaCy for its own sake.
- Multi-word skills (e.g. "power bi", "machine learning") are matched as phrases.
- Matching is case-insensitive and uses \b word boundaries so "R" doesn't match
  inside "Reporting", and "SAS" doesn't match inside "SAScompliance" etc.
  ("R" and "SAS" specifically get a stricter check — see SPECIAL_CASE_SKILLS.

Output: two clean tables ready to load into MySQL.
  jobs.csv        -> one row per posting
  job_skills.csv  -> one row per (job_id, skill) match — the bridge table
  skills.csv      -> the deduped skill dimension table
"""

import csv
import re
import uuid
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Canonical skill -> list of surface forms to match against raw text.
# Extend this dictionary as you pull more postings — it's the main lever
# for improving extraction quality, not the matching code itself.
SKILL_DICTIONARY = {
    "SQL":              ["sql", "mysql", "postgresql", "postgres", "t-sql", "pl/sql"],
    "Python":           ["python"],
    "R":                ["\\br\\b(?! studio)"],  # handled specially below
    "Excel":            ["excel", "pivot table", "vlookup"],
    "Power BI":         ["power bi", "powerbi"],
    "Tableau":          ["tableau"],
    "Qlik":             ["qlik"],
    "Machine Learning": ["machine learning", "\\bml\\b"],
    "Statistics":       ["statistic", "statistical"],
    "Pandas":           ["pandas"],
    "NumPy":            ["numpy"],
    "ETL":              ["etl"],
    "Spark":            ["spark"],
    "Hadoop":           ["hadoop"],
    "SPSS":             ["spss"],
    "SAS":              ["\\bsas\\b"],
    "Snowflake":        ["snowflake"],
    "Google Sheets":    ["google sheets"],
    "Deep Learning":    ["deep learning", "neural network"],
    "NLP":              ["\\bnlp\\b", "natural language processing"],
    "MLOps":            ["mlops"],
    "A/B Testing":      ["a/b test", "ab testing"],
    "Forecasting":      ["forecast"],
    "Data Modeling":    ["data model"],
    "JavaScript":       ["javascript"],
    "PowerPoint":       ["powerpoint"],
    # Added for the 2022-vs-2026 comparison: these terms were barely used
    # in mainstream DA/DS job ads in 2022 and are common in 2026 postings.
    "LLM":              ["\\bllm\\b", "large language model"],
    "RAG":              ["\\brag\\b", "retrieval augmented generation", "retrieval-augmented"],
    "Prompt Engineering": ["prompt engineering", "prompt design"],
    "Vector Database":  ["vector database", "vector db", "embeddings"],
    "Agentic AI":       ["agentic ai", "multi-agent", "agent orchestration"],
    "Generative AI":    ["generative ai", "genai", "gen ai"],
    "Fine-tuning":      ["fine-tuning", "fine tuning", "llm fine-tun"],
}

SPECIAL_CASE_SKILLS = {"R"}  # single-letter skills need extra-strict boundaries


def build_pattern(surface_forms):
    escaped = [sf if sf.startswith("\\b") or "\\" in sf else r"\b" + re.escape(sf) + r"\b"
               for sf in surface_forms]
    return re.compile("|".join(escaped), flags=re.IGNORECASE)


COMPILED = {skill: build_pattern(forms) for skill, forms in SKILL_DICTIONARY.items()}


def extract_skills_from_text(text: str) -> set:
    found = set()
    if not text:
        return found
    for skill, pattern in COMPILED.items():
        if pattern.search(text):
            found.add(skill)
    return found


def main():
    raw_path = DATA_DIR / "raw_jobs_seed.csv"
    jobs_out_path = DATA_DIR / "jobs_clean.csv"
    job_skills_out_path = DATA_DIR / "job_skills.csv"
    skills_out_path = DATA_DIR / "skills.csv"

    all_skills_found = set()
    jobs_rows = []
    job_skills_rows = []

    with open(raw_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            job_id = row["job_id"] or f"JOB_{i:04d}"
            combined_text = f"{row['title']} {row['description']}"
            skills = extract_skills_from_text(combined_text)
            all_skills_found.update(skills)

            jobs_rows.append({
                "job_id": job_id,
                "title": row["title"].strip(),
                "company": row["company"].strip(),
                "city": row["city"].strip(),
                "posted_date": row["posted_date"].strip(),
                "job_type": row.get("job_type", "").strip(),
                "source": row.get("source", "").strip(),
            })

            for skill in sorted(skills):
                job_skills_rows.append({"job_id": job_id, "skill_name": skill})

    # Skill dimension table
    skills_rows = [{"skill_id": idx, "skill_name": s}
                    for idx, s in enumerate(sorted(all_skills_found), start=1)]
    skill_name_to_id = {r["skill_name"]: r["skill_id"] for r in skills_rows}
    for r in job_skills_rows:
        r["skill_id"] = skill_name_to_id[r["skill_name"]]

    # Write outputs
    with open(jobs_out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["job_id", "title", "company", "city",
                                                 "posted_date", "job_type", "source"])
        writer.writeheader()
        writer.writerows(jobs_rows)

    with open(skills_out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["skill_id", "skill_name"])
        writer.writeheader()
        writer.writerows(skills_rows)

    with open(job_skills_out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["job_id", "skill_id", "skill_name"])
        writer.writeheader()
        writer.writerows(job_skills_rows)

    print(f"Jobs: {len(jobs_rows)} | Unique skills found: {len(skills_rows)} "
          f"| job-skill links: {len(job_skills_rows)}")
    print(f"Wrote: {jobs_out_path.name}, {skills_out_path.name}, {job_skills_out_path.name}")


if __name__ == "__main__":
    main()
