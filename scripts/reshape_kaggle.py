"""
reshape_kaggle.py
------------------
Converts the Kaggle "Data Science / Data Analyst / ML Job Indeed" dataset
into the same shape as raw_jobs_seed.csv, tags every row source='kaggle_2022',
and appends it to your existing seed file.

USAGE:
    python3 reshape_kaggle.py path/to/kaggle_downloaded_file.csv

Run this from the scripts/ folder — it writes into ../data/raw_jobs_seed.csv
"""

import csv
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SEED_PATH = DATA_DIR / "raw_jobs_seed.csv"

# Indian cities to look for inside job_location strings like "Bangalore, Karnataka"
KNOWN_CITIES = [
    "Bangalore", "Bengaluru", "Mumbai", "Delhi", "Gurgaon", "Gurugram",
    "Noida", "Hyderabad", "Pune", "Chennai", "Kolkata", "Ahmedabad",
    "Jaipur", "Kochi", "Indore", "Chandigarh", "Remote",
]


def extract_city(location_str: str) -> str:
    if not location_str:
        return "Unknown"
    for city in KNOWN_CITIES:
        if city.lower() in location_str.lower():
            return "Bangalore" if city == "Bengaluru" else city
    # fall back to text before the first comma
    return location_str.split(",")[0].strip() or "Unknown"


def parse_relative_date(post_date_str: str, today_str: str) -> str:
    """Handles 'X days ago', 'Just posted', 'Today', '30+ days ago',
    or an already-absolute date. Falls back to blank if unparseable —
    never guess a fake date."""
    if not post_date_str:
        return ""
    post_date_str = post_date_str.strip().lower()

    # try to parse a reference "today" date; fall back to a fixed
    # assumption of mid-2022 since that's when this dataset was scraped
    try:
        ref_date = datetime.strptime(today_str.strip(), "%Y-%m-%d")
    except (ValueError, AttributeError):
        ref_date = datetime(2022, 7, 15)

    if "just posted" in post_date_str or post_date_str == "today":
        return ref_date.strftime("%Y-%m-%d")

    match = re.search(r"(\d+)\+?\s*day", post_date_str)
    if match:
        days_ago = int(match.group(1))
        return (ref_date - timedelta(days=days_ago)).strftime("%Y-%m-%d")

    # try parsing as an absolute date already
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%B %d, %Y", "%d %B %Y"):
        try:
            return datetime.strptime(post_date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return ""  # unparseable — leave blank, don't fabricate


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace('"', "'").replace("\n", " ").replace("\r", " ")
    return re.sub(r"\s+", " ", text).strip()


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 reshape_kaggle.py path/to/kaggle_file.csv")
        sys.exit(1)

    kaggle_path = Path(sys.argv[1])
    if not kaggle_path.exists():
        print(f"File not found: {kaggle_path}")
        sys.exit(1)

    reshaped_rows = []
    with open(kaggle_path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            job_id = f"KAGGLE_{i:05d}"
            title = clean_text(row.get("job_title", ""))
            company = clean_text(row.get("company", ""))
            city = extract_city(row.get("job_location", ""))
            description = clean_text(row.get("job_summary", ""))
            posted_date = parse_relative_date(
                row.get("post_date", ""), row.get("today", "")
            )

            if not title or not description:
                continue  # skip unusable rows rather than loading junk

            reshaped_rows.append({
                "job_id": job_id,
                "title": title,
                "company": company,
                "city": city,
                "posted_date": posted_date,
                "job_type": "",
                "source": "kaggle_2022",
                "description": description,
            })

    # Append to the existing seed file (don't overwrite the live 2026 rows)
    file_exists = SEED_PATH.exists()
    fieldnames = ["job_id", "title", "company", "city", "posted_date",
                  "job_type", "source", "description"]

    with open(SEED_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(reshaped_rows)

    print(f"Appended {len(reshaped_rows)} kaggle_2022 rows to {SEED_PATH}")
    print("Now re-run: python3 scripts/extract_skills.py")


if __name__ == "__main__":
    main()
