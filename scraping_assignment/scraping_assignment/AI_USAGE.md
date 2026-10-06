# AI Usage

> **Candidate: edit this file so it is true for YOU before submitting.** Replace the bracketed parts with your real prompts and your real findings.

## Tools used
- Claude (Anthropic) - generated the initial project code, tests and documentation from the two assignment PDFs.

## What it was used for
- Project structure, scrapers (pagination, selectors), cleaning/validation/deduplication modules, `main.py`, unit tests, README.

## Representative prompts
- "[paste your actual prompt here, e.g. 'code it' + the two assignment PDFs]"

## AI-assisted parts
Essentially all code was AI-generated and then reviewed by me: [state what YOU reviewed/ran/changed].

## Issues found in AI output / changes after review
- A unit test caught a bug in `clean_tags`: tags differing only by case (`Love`/`love`) were not de-duplicated because lowercasing happened after the set was built. Fixed by lowercasing first.
- [Add anything you find yourself.]

## Verification
- 19 offline unit tests (cleaning, validation, deduplication, parsing, pagination, failed-page handling).
- End-to-end run against a local fake server covering pagination, detail pages, a 404 page, duplicate removal and count reconciliation.
- **The live run against the real sites was not executed by the AI (no network in its sandbox).** [Add: you ran `python main.py` on <date>, got N rows, checked the CSV and that JSON counts match.]
