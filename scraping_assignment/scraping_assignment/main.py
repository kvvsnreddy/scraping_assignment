"""Entry point: scrape -> clean -> validate -> deduplicate -> consolidate -> save."""
import argparse
import csv
import json
import logging
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import config
from processing.deduplication import find_duplicates
from processing.transform import CLEANERS
from processing.validation import validate_record
from scrapers.base_scraper import create_session
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper

logger = logging.getLogger("main")


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    for handler in (logging.StreamHandler(sys.stdout),
                    logging.FileHandler(log_dir / "scraper.log", mode="w", encoding="utf-8")):
        handler.setFormatter(fmt)
        root.addHandler(handler)


def clean_and_validate(source: str, raw_records: list):
    """Clean then validate one source. Returns (valid_records, stats_dict)."""
    cleaner = CLEANERS[source]
    rejected = Counter()
    valid, cleaned_count = [], 0
    for raw in raw_records:
        try:
            rec = cleaner(raw)
            cleaned_count += 1
        except Exception:
            logger.warning("Rejected (cleaning_error): %r", raw, exc_info=True)
            rejected["cleaning_error"] += 1
            continue
        problems = validate_record(rec)
        if problems:
            logger.warning("Rejected %s | %s | %s", source, problems, rec.get("name_or_title"))
            for p in problems:
                rejected[p] += 1
            rejected["_records"] += 1
        else:
            valid.append(rec)
    stats = {"collected": len(raw_records), "cleaned": cleaned_count,
             "rejected": len(raw_records) - len(valid),
             "rejected_by_reason": {k: v for k, v in rejected.items() if k != "_records"}}
    return valid, stats


def write_csv(records: list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=config.COLUMNS)
        writer.writeheader()
        writer.writerows(records)


def write_summary(stats: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4, ensure_ascii=False)


def run(args) -> dict:
    start_wall = datetime.now(timezone.utc)
    start = time.perf_counter()
    out_dir = Path(args.output_dir)

    session = create_session()
    scrapers = [
        BooksScraper(session, delay=args.delay, max_pages=args.max_pages,
                     fetch_details=not args.no_details),
        QuotesScraper(session, delay=args.delay, max_pages=args.max_pages),
    ]

    per_source, all_valid = {}, []
    for scraper in scrapers:  # each source isolated: one failure must not stop the other
        name = scraper.source_name
        try:
            raw = scraper.scrape()
        except Exception:
            logger.exception("Source %s failed entirely", name)
            raw = []
        valid, stats = clean_and_validate(name, raw)
        per_source[name] = stats
        all_valid.extend(valid)
        logger.info("%s: %d collected, %d valid, %d rejected",
                    name, stats["collected"], len(valid), stats["rejected"])

    unique, dupes = find_duplicates(all_valid)
    dupes_by_source = Counter(d["source"] for d in dupes)
    final_by_source = Counter(u["source"] for u in unique)
    for name, stats in per_source.items():
        stats["duplicates"] = dupes_by_source.get(name, 0)
        stats["final"] = final_by_source.get(name, 0)
    for d in dupes:
        logger.warning("Duplicate removed: %s | %s", d["source"], d["name_or_title"])

    write_csv(unique, out_dir / "final_dataset.csv")

    reasons = Counter()
    for s in per_source.values():
        reasons.update(s["rejected_by_reason"])
    total_collected = sum(s["collected"] for s in per_source.values())
    total_rejected = sum(s["rejected"] for s in per_source.values())
    summary = {
        "per_source": per_source,
        "total_collected": total_collected,
        "total_cleaned": sum(s["cleaned"] for s in per_source.values()),
        "total_rejected": total_rejected,
        "rejected_by_reason": dict(reasons),
        "duplicates_detected": len(dupes),
        "final_record_count": len(unique),
        "reconciles": total_collected - total_rejected - len(dupes) == len(unique),
        "start_time": start_wall.isoformat(timespec="seconds"),
        "end_time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "duration_seconds": round(time.perf_counter() - start, 1),
    }
    write_summary(summary, out_dir / "summary_report.json")
    logger.info("Done: %d final records in %.1fs", len(unique), summary["duration_seconds"])
    return summary


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Multi-source scraping pipeline")
    p.add_argument("--no-details", action="store_true",
                   help="skip book detail pages (faster; category/description stay empty)")
    p.add_argument("--delay", type=float, default=config.REQUEST_DELAY,
                   help="seconds between requests (default 0.5)")
    p.add_argument("--max-pages", type=int, default=None,
                   help="limit pages per source (for quick test runs)")
    p.add_argument("--output-dir", default=str(config.OUTPUT_DIR))
    return p.parse_args(argv)


if __name__ == "__main__":
    setup_logging(config.LOG_DIR)
    run(parse_args())
