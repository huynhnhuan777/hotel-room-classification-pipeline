import json
import random
import re
import time
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

INPUT_CSV = "hotels_input.csv"
OUT_CSV = "hotels_detail_output.csv"
OUT_JSONL = "hotels_detail_output.jsonl"

DEBUG_DIR = Path("debug_pages")
DEBUG_DIR.mkdir(exist_ok=True)

# nghỉ giữa các request để giảm rủi ro bị chặn
SLEEP_MIN = 2.5
SLEEP_MAX = 5.5

BOT_SIGNS = [
    "verify you are", "unusual traffic", "captcha", "robot",
    "chúng tôi phát hiện", "xác minh", "không phải robot",
    "access denied", "blocked", "sorry you have been blocked",
]


def canonicalize_url(url: str) -> str:
    """Bỏ query/fragment, giữ path .html."""
    u = urlparse(url)
    clean = urlunparse((u.scheme, u.netloc, u.path, "", "", ""))
    m = re.search(r"^(.*?\.html)", clean)
    return m.group(1) if m else clean


def looks_blocked(html: str) -> bool:
    t = (html or "").lower()
    return any(s in t for s in BOT_SIGNS)


def extract_jsonld_hotel(soup: BeautifulSoup) -> dict | None:
    """
    Tìm JSON-LD có @type LodgingBusiness/Hotel
    """
    for s in soup.select('script[type="application/ld+json"]'):
        txt = (s.string or "").strip()
        if not txt:
            continue
        try:
            obj = json.loads(txt)
        except Exception:
            continue

        candidates = []
        if isinstance(obj, dict):
            if isinstance(obj.get("@graph"), list):
                candidates.extend(obj["@graph"])
            else:
                candidates.append(obj)
        elif isinstance(obj, list):
            candidates.extend(obj)

        for c in candidates:
            if isinstance(c, dict) and c.get("@type") in ("LodgingBusiness", "Hotel"):
                return c
    return None


def parse_detail(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")

    out = {
        "detail_url": canonicalize_url(url),
        "phone": None,
        "name_detail": None,
        "ratingValue": None,
        "reviewCount": None,
        "priceRange": None,
        "streetAddress": None,
        "addressLocality": None,
        "addressRegion": None,
        "postalCode": None,
        "addressCountry": None,
        "lat": None,
        "lng": None,
        "amenities": None, 
        "_parse_status": None,
    }

    # phone
    tel = soup.select_one('a[href^="tel:"]')
    if tel and tel.get("href"):
        out["phone"] = tel["href"].replace("tel:", "").strip()

    # JSON-LD
    ld = extract_jsonld_hotel(soup)
    if not ld:
        out["_parse_status"] = "no_jsonld"
        return out

    out["_parse_status"] = "ok_jsonld"
    out["name_detail"] = ld.get("name")
    out["priceRange"] = ld.get("priceRange")

    ar = ld.get("aggregateRating") or {}
    out["ratingValue"] = ar.get("ratingValue")
    out["reviewCount"] = ar.get("reviewCount")

    addr = ld.get("address") or {}
    out["streetAddress"] = addr.get("streetAddress")
    out["addressLocality"] = addr.get("addressLocality")
    out["addressRegion"] = addr.get("addressRegion")
    out["postalCode"] = addr.get("postalCode")
    out["addressCountry"] = addr.get("addressCountry")

    geo = ld.get("geo") or {}
    out["lat"] = geo.get("latitude")
    out["lng"] = geo.get("longitude")

    amenities = []
    for af in (ld.get("amenityFeature") or []):
        if isinstance(af, dict) and af.get("name"):
            amenities.append(af["name"])
    out["amenities"] = ", ".join(amenities) if amenities else None

    return out


def fetch_html(session: requests.Session, url: str) -> tuple[int | None, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
    }
    r = session.get(url, headers=headers, timeout=35)
    return r.status_code, r.text


def main():
    df_in = pd.read_csv(INPUT_CSV)

    if "hotel_url" not in df_in.columns:
        raise ValueError("Input CSV phải có cột 'hotel_url'")

    session = requests.Session()
    results = []

    for idx, row in df_in.iterrows():
        raw_url = str(row["hotel_url"]).strip()

        if not raw_url.startswith("http"):
            out = row.to_dict()
            out.update({"_fetch_status": None, "_parse_status": "invalid_url"})
            results.append(out)
            continue

        url = canonicalize_url(raw_url)
        print(f"[{idx+1}/{len(df_in)}] GET {url}")

        try:
            status, html = fetch_html(session, url)

            if status in (403, 429) or looks_blocked(html):
                debug_name = f"blocked_{idx+1}.html"
                (DEBUG_DIR / debug_name).write_text(html or "", encoding="utf-8", errors="ignore")
                print(f"  -> BLOCK/VERIFY (status={status}). Saved debug_pages/{debug_name}")

                out = row.to_dict()
                out.update({
                    "detail_url": url,
                    "_fetch_status": status,
                    "_parse_status": "blocked_or_verify"
                })
                results.append(out)
                time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))
                continue

            detail = parse_detail(html, url)

            out = row.to_dict()
            out.update({"_fetch_status": status})
            out.update(detail)
            results.append(out)

        except Exception as e:
            print("  -> ERROR:", str(e)[:200])
            out = row.to_dict()
            out.update({"detail_url": url, "_fetch_status": None, "_parse_status": f"error:{type(e).__name__}"})
            results.append(out)

        time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))

    df_out = pd.DataFrame(results)
    df_out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\nSaved: {OUT_CSV} and {OUT_JSONL}")
    print("Debug blocked pages in:", str(DEBUG_DIR.resolve()))


if __name__ == "__main__":
    main()
