import os
import json
import re
import sys
import requests
from bs4 import BeautifulSoup, Tag
from datetime import datetime, time as dt_time, date
from typing import Optional, List, Tuple, Dict, Any
import pytz
import time
from urllib.parse import quote

# Define the Indian timezone
IST = pytz.timezone('Asia/Kolkata')

# Add headers to mimic a web browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.kllotteryresult.com/'
}

# Optional proxy-based scraping fallback (e.g., ScraperAPI or compatible)
# Provide an API key via env var SCRAPERAPI_KEY in CI to bypass origin blocking.
SCRAPER_API_KEY = os.environ.get('SCRAPERAPI_KEY', '').strip()
SCRAPER_API_ENDPOINT = os.environ.get('SCRAPERAPI_ENDPOINT', 'http://api.scraperapi.com')

def build_proxy_url(target_url: str) -> str:
    if not SCRAPER_API_KEY:
        return target_url
    # ScraperAPI format: http(s)://api.scraperapi.com?api_key=KEY&url=ENCODED
    from urllib.parse import urlencode
    query = urlencode({'api_key': SCRAPER_API_KEY, 'url': target_url})
    return f"{SCRAPER_API_ENDPOINT}?{query}"

def robust_get(url: str, headers: dict, timeout: int = 20, max_retries: int = 3) -> requests.Response:
    """Try direct fetch first; on 403/429/5xx or network error, retry and fall back to proxy if configured."""
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            res = requests.get(url, headers=headers, timeout=timeout)
            if res.status_code in (403, 429) or res.status_code >= 500:
                raise requests.exceptions.RequestException(f"HTTP {res.status_code}")
            return res
        except requests.exceptions.RequestException as exc:
            last_exc = exc
            # Try proxy fallback if available
            if SCRAPER_API_KEY:
                try:
                    proxy_url = build_proxy_url(url)
                    res = requests.get(proxy_url, headers=headers, timeout=timeout)
                    if res.status_code in (403, 429) or res.status_code >= 500:
                        raise requests.exceptions.RequestException(f"Proxy HTTP {res.status_code}")
                    return res
                except requests.exceptions.RequestException as exc2:
                    last_exc = exc2
            # Backoff between attempts
            time.sleep(min(2 * attempt, 6))
    # Exhausted retries
    if last_exc:
        raise last_exc
    raise RuntimeError("Failed to fetch URL and no exception captured")

def fetch_text_via_jina(url: str) -> str:
    """Fetch page text via r.jina.ai to bypass Cloudflare challenges without API keys."""
    proxied = "https://r.jina.ai/http://" + url.replace("https://", "").replace("http://", "")
    res = requests.get(proxied, headers=HEADERS, timeout=30)
    res.raise_for_status()
    return res.text

def fetch_page_text(url: str) -> str:
    """Fetch page HTML using direct request first, then fallback to Jina proxy."""
    try:
        res = robust_get(url, HEADERS, timeout=25)
        res.raise_for_status()
        return res.text
    except Exception:
        return fetch_text_via_jina(url)

def parse_date_from_text(text: str) -> Optional[date]:
    """Extract a date from text supporting multiple formats."""
    # Common numeric formats: 16-09-2025, 16/09/2025, 16.09.2025
    m = re.search(r"(\d{2})[./-](\d{2})[./-](\d{4})", text)
    if m:
        try:
            return datetime.strptime(f"{m.group(3)}-{m.group(2)}-{m.group(1)}", "%Y-%m-%d").date()
        except ValueError:
            pass
    # Textual month formats: 16 September 2025, 16 Sep 2025, Sep 16, 2025
    patterns = [
        "%d %B %Y", "%d %b %Y", "%b %d, %Y", "%B %d, %Y",
        "%d-%b-%Y", "%d-%B-%Y"
    ]
    # Try sliding windows around words that look like dates
    candidates = []
    # Gather tokens that include month names
    month_regex = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)"
    for m2 in re.finditer(rf"\b\d{{1,2}}\s+{month_regex}\s+\d{{4}}\b", text, flags=re.I):
        candidates.append(m2.group(0))
    for m3 in re.finditer(rf"\b{month_regex}\s+\d{{1,2}},\s*\d{{4}}\b", text, flags=re.I):
        candidates.append(m3.group(0))
    for cand in candidates:
        for fmt in patterns:
            try:
                return datetime.strptime(cand, fmt).date()
            except ValueError:
                continue
    return None

def get_last_n_result_links(n=10):
    MAIN_URL = "https://www.kllotteryresult.com/"
    today = datetime.now().date()
    try:
        page_text = fetch_page_text(MAIN_URL)
    except Exception as e:
        print(f"Error fetching homepage: {e}")
        return []

    # Extract links using both HTML parsing and regex as fallback
    candidates_set = set()
    try:
        soup = BeautifulSoup(page_text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if "kerala-lottery-result" in href.lower():
                if href.startswith("http"):
                    candidates_set.add(href)
                else:
                    candidates_set.add(f"https://www.kllotteryresult.com{href}")
    except Exception:
        pass
    # Regex fallback
    if not candidates_set:
        abs_links = re.findall(r'https?://www\\.kllotteryresult\\.com/[a-z0-9-]*kerala-lottery-result[a-z0-9-]*/?', page_text, flags=re.I)
        rel_links = re.findall(r'/[a-z0-9-]*kerala-lottery-result[a-z0-9-]*/?', page_text, flags=re.I)
        for p in abs_links:
            candidates_set.add(p)
        for p in rel_links:
            candidates_set.add(f"https://www.kllotteryresult.com{p}")
    candidates = sorted(candidates_set)

    # Logging: counts (abs/rel) — we normalized to absolute URLs, so report abs only
    abs_count = len([c for c in candidates if c.startswith("http")])
    print(f"Homepage links: abs={abs_count} candidates={len(candidates)}")
    if candidates:
        for preview_url in candidates[:5]:
            print(f"Candidate: {preview_url}")

    results = []
    seen = set()
    dated_candidates: List[Tuple[date, str]] = []
    for url in candidates:
        if url in seen:
            continue
        seen.add(url)
        # fetch the result page text (direct first, then fallback) and validate date <= today
        try:
            page_text2 = fetch_page_text(url)
        except Exception as e:
            print(f"Skip {url}: fetch error {e}")
            continue
        # find date using robust parser
        result_date = parse_date_from_text(page_text2) or None
        if not result_date:
            print(f"Skip {url}: no date found")
            continue
        # Include results from the last 30 days to ensure we don't miss any
        # This will help capture the missing results
        days_diff = (today - result_date).days
        if result_date <= today and days_diff <= 30:
            dated_candidates.append((result_date, url))
        elif result_date <= today:
            # Still include older results but with lower priority
            # Add a large number to sort them after recent results
            dated_candidates.append((result_date, url))
        else:
            print(f"Skip {url}: future date {result_date}")
    # Sort by date descending and return top n URLs
    # For recent results (within 30 days), sort normally
    # For older results, we still include them but they'll be at the end
    dated_candidates.sort(key=lambda x: x[0], reverse=True)
    for d, u in dated_candidates[:n]:
        results.append(u)
    return results

# Mappings
prize_map = {
    "1st": "1st_prize", "1st Prize": "1st_prize",
    "Cons": "consolation_prize", "Cons Prize": "consolation_prize",
    "Cons Prize-Rs": "consolation_prize", "Consolation": "consolation_prize",
    "Consolation Prize": "consolation_prize", "2nd": "2nd_prize", "2nd Prize": "2nd_prize",
    "3rd": "3rd_prize", "3rd Prize": "3rd_prize", "4th": "4th_prize", "4th Prize": "4th_prize",
    "5th": "5th_prize", "5th Prize": "5th_prize", "6th": "6th_prize", "6th Prize": "6th_prize",
    "7th": "7th_prize", "7th Prize": "7th_prize", "8th": "8th_prize", "8th Prize": "8th_prize",
    "9th": "9th_prize", "9th Prize": "9th_prize"
}
prize_amounts = {
    "1st_prize": 10000000, "consolation_prize": 5000, "2nd_prize": 3000000,
    "3rd_prize": 500000, "4th_prize": 5000, "5th_prize": 2000,
    "6th_prize": 1000, "7th_prize": 500, "8th_prize": 200, "9th_prize": 100
}
standard_labels = {
    "1st_prize": "1st Prize", "consolation_prize": "Consolation Prize",
    "2nd_prize": "2nd Prize", "3rd_prize": "3rd Prize", "4th_prize": "4th Prize",
    "5th_prize": "5th Prize", "6th_prize": "6th Prize", "7th_prize": "7th Prize",
    "8th_prize": "8th Prize", "9th_prize": "9th Prize"
}

def process_result_page(result_soup, result_url, result_page_text: str):
    title_text = ""
    title_tag = result_soup.find("h1")
    if title_tag and title_tag.text.strip().lower() not in ["lottery results", "kerala lottery results"]:
        title_text = title_tag.text.strip()
    if not title_text:
        title_tag = result_soup.find("title")
        if title_tag and title_tag.text.strip():
            title_text = title_tag.text.strip()
    if not title_text:
        for tag in ["h2", "h3"]:
            t = result_soup.find(tag)
            if t and t.text.strip():
                title_text = t.text.strip()
                break
    if not title_text:
        title_text = "Unknown Lottery"
    print(f"TITLE TEXT: '{title_text}'")

    # Try to parse date from title; fallback to whole page; finally to today's date if within window
    parsed_date = parse_date_from_text(title_text)
    draw_date = parsed_date.strftime("%Y-%m-%d") if parsed_date else "Unknown-Date"
    if draw_date == "Unknown-Date":
        # Fallback: scan entire page text for a date
        p2 = parse_date_from_text(result_page_text)
        if p2:
            draw_date = p2.strftime("%Y-%m-%d")
        else:
            # As a last resort during the result window, assume today's date
            if is_within_optimal_time_window():
                draw_date = datetime.now(IST).strftime("%Y-%m-%d")

    # Ensure we have today's date if we're in the optimal window and the date is unknown
    if draw_date == "Unknown-Date" and is_within_optimal_time_window():
        draw_date = datetime.now(IST).strftime("%Y-%m-%d")

    draw_number_match = re.search(r"\(([^)]+)\)", title_text)
    draw_number = draw_number_match.group(1) if draw_number_match else "XX"

    lottery_name_match = re.search(r"([A-Za-z\s]+)\s*\(", title_text)
    lottery_name = lottery_name_match.group(1).strip().upper() if lottery_name_match else "Unknown"
    
    lottery_code_match = re.search(r'\(([A-Z]{2,3})\)', title_text)
    lottery_code = lottery_code_match.group(1) if lottery_code_match else 'XX'
    if lottery_code == 'XX' or draw_number == 'XX':
        # Fallback: derive from URL slug like .../kerala-lottery-result-BT-19
        url_slug_match = re.search(r'/([a-z0-9-]*kerala-lottery-result[-/])*([A-Z]{2,3})-(\d+)', result_url)
        if url_slug_match:
            lottery_code = url_slug_match.group(2)
            draw_number = url_slug_match.group(3)
    # Infer lottery code from first winner token if still unknown
    if lottery_code == 'XX':
        # Try scanning for codes like 'DD 781756' in the page text
        mcode = re.search(r'\b([A-Z]{1,3})\s*\d{4,6}\b', result_page_text)
        if mcode:
            lottery_code = mcode.group(1)

    # Try to extract venue
    venue = ""
    venue_tag = result_soup.find(string=re.compile(r"Venue|At", re.I))
    if venue_tag and isinstance(venue_tag, str):
        venue_line = venue_tag.strip()
        venue_match = re.search(r"(?:Venue|At)[:\-]?\s*([A-Za-z0-9, .()]+)", venue_line)
        if venue_match:
            venue = venue_match.group(1).strip()

    # Get download link
    download_link = ""
    for a_tag in result_soup.find_all("a", href=True):
        href = a_tag["href"]
        if any(href.lower().endswith(ext) for ext in [".pdf", ".jpg", ".jpeg", ".png"]):
            if not href.startswith("http"):
                href = "https://www.kllotteryresult.com" + href
            download_link = href
            break

    prizes = {}
    current_key = None
    result_table = result_soup.find("table", class_="w-full")
    if result_table and isinstance(result_table, Tag):
        for row in result_table.find_all("tr"):
            th = row.find("th")
            if th:
                label = th.get_text(strip=True)
                key = None
                for k, v in prize_map.items():
                    if k in label:
                        key = v
                        break
                if key:
                    current_key = key
                    prizes[current_key] = {
                        "amount": prize_amounts.get(current_key, 0),
                        "label": standard_labels.get(current_key, label),
                        "winners": []
                    }
            tds = row.find_all("td")
            if tds and current_key:
                numbers = [td.get_text(strip=True) for td in tds if td.get_text(strip=True)]
                prizes[current_key]["winners"].extend(numbers)

    # Fallback plaintext parsing if no table winners were found
    def parse_plaintext_prizes(txt: str) -> dict:
        lines = [re.sub(r"\s+", " ", ln).strip() for ln in txt.splitlines()]
        header_regex_to_key = [
            (re.compile(r"^1st Prize", re.I), "1st_prize"),
            (re.compile(r"^Cons(olation)? Prize", re.I), "consolation_prize"),
            (re.compile(r"^2nd Prize", re.I), "2nd_prize"),
            (re.compile(r"^3rd Prize", re.I), "3rd_prize"),
            (re.compile(r"^4th Prize", re.I), "4th_prize"),
            (re.compile(r"^5th Prize", re.I), "5th_prize"),
            (re.compile(r"^6th Prize", re.I), "6th_prize"),
            (re.compile(r"^7th Prize", re.I), "7th_prize"),
            (re.compile(r"^8th Prize", re.I), "8th_prize"),
            (re.compile(r"^9th Prize", re.I), "9th_prize"),
        ]
        parsed: Dict[str, Any] = {}
        current_section: Optional[str] = None
        for ln in lines:
            if not ln:
                continue
            # Section header detection
            switched = False
            for rgx, key in header_regex_to_key:
                if rgx.search(ln):
                    current_section = key
                    if current_section not in parsed:
                        parsed[current_section] = {
                            "amount": prize_amounts.get(current_section, 0),
                            "label": standard_labels.get(current_section, current_section.replace('_', ' ').title()),
                            "winners": []
                        }
                    switched = True
                    break
            if switched:
                continue
            if not current_section:
                continue
            # Skip filler
            if ln.strip() in ("**", "..."):
                continue
            # Extract tokens like 'DD 781756' or plain 4-6 digit numbers
            tokens = re.findall(r"[A-Z]{1,3}\s*\d{4,6}|\b\d{4,6}\b", ln)
            for t in tokens:
                parsed[current_section]["winners"].append(t.strip())
        return parsed

    if not prizes or all(len(section.get("winners", [])) == 0 for section in prizes.values()):
        # Normalize page text from soup to better capture headings and lines
        normalized_text = result_soup.get_text("\n", strip=True)
        parsed_plain = parse_plaintext_prizes(normalized_text)
        if parsed_plain:
            prizes = parsed_plain
            print("Parsed winners using plaintext fallback.")

    # If prizes is empty, initialize with default structure
    if not prizes:
        # Initialize with all prize categories
        for key, label in standard_labels.items():
            prizes[key] = {
                "amount": prize_amounts.get(key, 0),
                "label": label,
                "winners": ["Please wait, results will be published at 3 PM."]
            }
    else:
        # Check if we have actual winning numbers or just placeholders
        has_actual_winners = False
        for key, prize in prizes.items():
            winners = prize["winners"]
            # Check if any winner is not a placeholder
            for winner in winners:
                if winner != "Please wait, results will be published at 3 PM." and winner != "***":
                    has_actual_winners = True
                    break
            if has_actual_winners:
                break
        
        # If we don't have actual winners, use placeholder
        if not has_actual_winners:
            for key, prize in prizes.items():
                prize["winners"] = ["Please wait, results will be published at 3 PM."]
        # Otherwise, add placeholder to any prize category that has no winners
        else:
            for key, prize in prizes.items():
                if not prize["winners"]:
                    prize["winners"].append("Please wait, results will be published at 3 PM.")

    data = {
        "lottery_name": lottery_name,
        "draw_number": draw_number,
        "draw_date": draw_date,
        "venue": venue,
        "prizes": prizes,
        "downloadLink": download_link
    }

    # Create note directory if it doesn't exist
    os.makedirs('note', exist_ok=True)

    # Generate filename with lottery code
    filename = f"{lottery_code}-{draw_number}-{draw_date}.json"
    local_path = f"note/{filename}"

    # Save to note folder
    with open(local_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved to: {os.path.abspath(local_path)}")

    # Also save as latest.json for easy access
    latest_path = "note/latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Latest result saved to: {os.path.abspath(latest_path)}")

    return local_path, filename

def is_within_optimal_time_window():
    """Always return True to allow scraping at any time"""
    return True

def main():
    # Remove time window restriction to allow scraping at any time
    try:
        current_time = datetime.now(IST)
        print(f"\n{'='*50}")
        print(f"Checking for new results at {current_time.strftime('%Y-%m-%d %H:%M:%S')} IST")
        print(f"{'='*50}")

        # Fetch multiple results to ensure we don't miss any
        latest_links = get_last_n_result_links(10)

        if not latest_links:
            print("No latest results found. This might be a normal occurrence if results aren't published yet.")
            # Don't exit with error code - still generate manifest/history even if no new results
            return
        else:
            print(f"Processing {len(latest_links)} latest results:")
            for i, result_url in enumerate(latest_links):
                print(f"Processing result {i+1}: {result_url}")

                # Prefer direct fetch for full HTML; fallback to jina proxy
                try:
                    res = robust_get(result_url, HEADERS, timeout=20)
                    res.raise_for_status()
                    result_text = res.text
                except Exception:
                    result_text = fetch_text_via_jina(result_url)
                result_soup = BeautifulSoup(result_text, "html.parser")

                # Process and save the result
                process_result_page(result_soup, result_url, result_text)
                print(f"Result {i+1} processed successfully.")
            
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        # Don't exit with error code to prevent scheduler from stopping
        return
    
    print("Script execution completed.")

if __name__ == "__main__":
    main()