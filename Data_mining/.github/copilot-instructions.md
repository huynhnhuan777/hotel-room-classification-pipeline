<!-- Copilot instructions for AI coding agents working on this repository -->
# Copilot / AI Agent Instructions

This repository contains small Python scripts for crawling hotels data from hotels.com using Selenium and saving normalized JSON/CSV outputs. The goal of these instructions is to help an AI agent be immediately productive when making changes.

**High-level architecture & purpose**
- Single-repo scripts (not a service): main scripts are `hotels_login_and_save_cookie.py`, `hotels_crawl_hcm.py`, `merge_hcm_data.py`, and `normalize_hotels_data.py`.
- Data flow: automated login -> capture API responses (Selenium performance logs + CDP) -> extract hotel objects -> append to `hotels_data_hcm.jsonl` -> merge into `hotels_data_full.jsonl` -> normalize to CSV.
- Persistence: intermediate files are JSONL (`hotels_data_hcm.jsonl`, `hotels_data_full.jsonl`) and small JSON trackers (`seen_requests.json`), plus `hotels_cookies.pkl`, `hotels_localstorage.json`, `hotels_sessionstorage.json`.

**Key files to read & edit**
- `hotels_login_and_save_cookie.py` — manual login flow; saves cookies and storage snapshots used by crawls.
- `hotels_crawl_hcm.py` — main crawling logic: enables performance logs, monitors entries, uses `Network.getResponseBody` to fetch API responses, extracts hotels and writes JSONL incrementally. Look here for `api_keywords`, `TARGET_NEW_COUNT`, and `HCM_LISTINGS` configuration.
- `merge_hcm_data.py` — merges `hotels_data_hcm.jsonl` into `hotels_data_full.jsonl` and creates backups.
- `normalize_hotels_data.py` — converts JSONL -> CSV and defines the canonical 22 output fields.
- `test_extract_hotels.py` — unit tests for extraction logic (use this to validate parsing changes).

**Repository conventions & important patterns**
- Immediately persist on discovery: crawling code appends each hotel to JSONL as soon as it's parsed to avoid data loss.
- Deduping by `hotelId` and `requestId`: `seen_requests.json` and existing `hotels_data_full.jsonl` are authoritative sources used to avoid reprocessing.
- Performance-log based capture: the crawler relies on Selenium performance logs + CDP (`driver.execute_cdp_cmd('Network.getResponseBody', ...)`). When modifying, keep robust checks for buffer resets and incremental processing (track `last_log_index`).
- Config knobs live in scripts (not a config file): change `TARGET_NEW_COUNT` and `HCM_LISTINGS` directly in `hotels_crawl_hcm.py`.

**Developer workflows & commands**
- Install deps: `pip install -r requirements.txt` (devs use local Chrome + matching ChromeDriver or `webdriver-manager`).
- Manual login step: run `python hotels_login_and_save_cookie.py` and perform manual sign-in in opened browser to obtain `hotels_cookies.pkl` and storage dumps.
- Crawl: run `python hotels_crawl_hcm.py` (ensure saved cookies and storage files present). Monitor console logs for `Performance log buffer reset` or CDP failures.
- Merge and normalize:
  - `python merge_hcm_data.py`
  - `python normalize_hotels_data.py --input hotels_data_full.jsonl --output hotels_data_complete.csv`
- Tests: run `pytest -q` to run `test_extract_hotels.py` and any added tests.

**Safety / non-goals**
- Do not commit `hotels_cookies.pkl`, `hotels_localstorage.json`, or `hotels_sessionstorage.json` to VCS. Treat cookies/storage as secrets.
- Avoid changing the immediate-persist approach unless a migration plan is added: incremental flushes are deliberate to prevent data loss during long crawls.

**When changing parsing logic**
- Update `test_extract_hotels.py` with sample responses that reflect different shapes (e.g., `results`, `hotelList`, nested `lead` price) and run `pytest`.
- Ensure new fields are added to `normalize_hotels_data.py` output mapping and documented in README.

**Examples of TODOs an agent might perform**
- Add resilience for buffer resets: ensure `last_log_index` is persisted and recovered if logs shrink.
- Add more `api_keywords` in `hotels_crawl_hcm.py` if new endpoints appear.
- Improve `extract_hotel_data()` parsing to handle missing `price.lead` or alternate shapes — include unit tests.

If anything here is unclear or missing (for example, more examples of API response shapes or expected CSV columns), tell me which area to expand and I will iterate.
