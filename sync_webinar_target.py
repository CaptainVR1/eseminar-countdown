#!/usr/bin/env python3
import argparse
import datetime as dt
import html
import json
import re
import sys
import urllib.request


MONTHS = {
    "فروردین": 1,
    "اردیبهشت": 2,
    "خرداد": 3,
    "تیر": 4,
    "مرداد": 5,
    "شهریور": 6,
    "مهر": 7,
    "آبان": 8,
    "آذر": 9,
    "دی": 10,
    "بهمن": 11,
    "اسفند": 12,
}

PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_digits(value: str) -> str:
    return value.translate(PERSIAN_DIGITS)


def normalize_text(value: str) -> str:
    value = normalize_digits(value)
    value = value.replace("ي", "ی").replace("ك", "ک")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def div(a: int, b: int) -> int:
    return a // b


def jalali_to_gregorian(jy: int, jm: int, jd: int):
    jy -= 979
    jm -= 1
    jd -= 1

    j_day_no = 365 * jy + div(jy, 33) * 8 + div((jy % 33 + 3), 4)
    if jm < 6:
        j_day_no += jm * 31
    else:
        j_day_no += 186 + (jm - 6) * 30
    j_day_no += jd

    g_day_no = j_day_no + 79
    gy = 1600 + 400 * div(g_day_no, 146097)
    g_day_no %= 146097

    leap = True
    if g_day_no >= 36525:
        g_day_no -= 1
        gy += 100 * div(g_day_no, 36524)
        g_day_no %= 36524
        if g_day_no >= 365:
            g_day_no += 1
        else:
            leap = False

    gy += 4 * div(g_day_no, 1461)
    g_day_no %= 1461

    if g_day_no >= 366:
        leap = False
        g_day_no -= 1
        gy += div(g_day_no, 365)
        g_day_no %= 365

    gd = g_day_no + 1
    g_days_in_month = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 0
    while gm < 12 and gd > g_days_in_month[gm]:
        gd -= g_days_in_month[gm]
        gm += 1

    return gy, gm + 1, gd


def extract_datetime_text(page_text: str) -> str:
    match = re.search(
        r"شروع وبینار\s*([0-9]+\s+[^\s]+\s+[0-9]+\s*-\s*ساعت\s*[0-9]{1,2}:[0-9]{2})",
        page_text,
    )
    if not match:
        raise ValueError("Could not find webinar start date/time in page text")
    return match.group(1).strip()


def parse_jalali_datetime(value: str):
    value = normalize_text(value)
    match = re.search(r"([0-9]+)\s+([^\s]+)\s+([0-9]+)\s*-\s*ساعت\s*([0-9]{1,2}):([0-9]{2})", value)
    if not match:
        raise ValueError(f"Invalid webinar datetime format: {value}")

    day = int(match.group(1))
    month_name = match.group(2)
    year = int(match.group(3))
    hour = int(match.group(4))
    minute = int(match.group(5))

    if month_name not in MONTHS:
        raise ValueError(f"Unsupported Jalali month name: {month_name}")
    month = MONTHS[month_name]

    gy, gm, gd = jalali_to_gregorian(year, month, day)
    iso = f"{gy:04d}-{gm:02d}-{gd:02d}T{hour:02d}:{minute:02d}:00+03:30"
    return iso


def extract_title(raw_html: str) -> str:
    match = re.search(r"<title>\s*(.*?)\s*</title>", raw_html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return "Webinar Countdown"
    title = normalize_text(html.unescape(match.group(1)))
    return title or "Webinar Countdown"


def fetch_url(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) CountdownSync/1.0",
            "Accept-Language": "fa,en-US;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = resp.read()
    return data.decode("utf-8", errors="ignore")


def build_json(url: str, raw_html: str):
    text_only = normalize_text(html.unescape(re.sub(r"<[^>]+>", " ", raw_html)))
    source_text = extract_datetime_text(text_only)
    target_iso = parse_jalali_datetime(source_text)
    title = extract_title(raw_html)

    return {
        "title": title,
        "webinar_url": url,
        "target_iso": target_iso,
        "source_time_text": source_text,
        "updated_at": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
    }


def main():
    parser = argparse.ArgumentParser(description="Sync webinar datetime into webinar-target.json")
    parser.add_argument("--url", required=True, help="Webinar page URL")
    parser.add_argument("--out", default="/srv/Eseminar/webinar-target.json", help="Output JSON path")
    args = parser.parse_args()

    raw_html = fetch_url(args.url)
    result = build_json(args.url, raw_html)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Updated {args.out}")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
