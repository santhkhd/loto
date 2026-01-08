import requests
from bs4 import BeautifulSoup, Tag
import json
import re
import time
from datetime import datetime
import os

def get_last_n_result_links(n=50):
    MAIN_URL = "https://www.kllotteryresult.com/"
    links = []
    seen = set()
    next_url = MAIN_URL
    today = datetime.now().date()
    while next_url and len(links) < n:
        res = requests.get(next_url)
        soup = BeautifulSoup(res.text, "html.parser")
        for a in soup.find_all("a", href=True):
            if re.search(r'/kerala-lottery-result-[A-Z]+-\d+', a['href']):
                url = a['href']
                if not isinstance(url, str):
                    continue
                if not url.startswith("http"):
                    url = "https://www.kllotteryresult.com" + url
                if url in seen:
                    continue
                try:
                    page_res = requests.get(url)
                    page_soup = BeautifulSoup(page_res.text, "html.parser")
                except Exception:
                    continue
                date_str = None
                for tag in ["h1", "title", "h2", "h3"]:
                    t = page_soup.find(tag)
                    if t and t.text:
                        m = re.search(r"(\d{2})[./-](\d{2})[./-](\d{4})", t.text)
                        if m:
                            date_str = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
                            break
                if date_str:
                    try:
                        result_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        # Exclude today's date
                        if result_date < today:
                            links.append(url)
                            seen.add(url)
                            if len(links) >= n:
                                break
                    except Exception:
                        continue
        next_link = soup.find("a", string=re.compile("Older Posts|Next", re.I))
        next_href = next_link.get('href') if isinstance(next_link, Tag) else None
        if next_href and isinstance(next_href, str) and len(links) < n:
            if not next_href.startswith("http"):
                next_url = "https://www.kllotteryresult.com" + next_href
            else:
                next_url = next_href
            time.sleep(1)
        else:
            next_url = None
    return links

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
    "5th_prize": "5th Prize", "6th_prize": "6th Prize", "7th_prize": "7th_prize",
    "8th_prize": "8th Prize", "9th_prize": "9th Prize"
}

def is_result_real(prizes):
    """Check if the result actually contains winning numbers, not just placeholders."""
    if not prizes:
        return False
    
    # Check 1st prize specifically
    first_prize = prizes.get("1st_prize", {})
    winners = first_prize.get("winners", [])
    
    if not winners:
        return False
        
    # If winners contain placeholders like '***' or 'Please wait', it's not real yet
    for w in winners:
        if "***" in w or "Please wait" in w:
            return False
            
    # Check if we have at least one valid-looking lottery number (e.g., "AB 123456")
    has_real_number = False
    for p_id, p_data in prizes.items():
        for w in p_data.get("winners", []):
            if re.search(r'\d{6}', w):
                has_real_number = True
                break
        if has_real_number: break
        
    return has_real_number

def process_result_page(result_url):
    try:
        result_res = requests.get(result_url)
        result_soup = BeautifulSoup(result_res.text, "html.parser")
    except Exception as e:
        print(f"Error fetching or parsing {result_url}: {e}")
        return

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
    print(f"Processing '{title_text}' from {result_url}")

    date_match = re.search(r"(\d{2})[./-](\d{2})[./-](\d{4})", title_text)
    draw_date = f"{date_match.group(3)}-{date_match.group(2)}-{date_match.group(1)}" if date_match else "Unknown-Date"

    draw_number_match = re.search(r"\(([^)]+)\)", title_text)
    draw_number = draw_number_match.group(1) if draw_number_match else "XX"

    lottery_name_match = re.search(r"([A-Za-z\s]+)\s*\(", title_text)
    lottery_name = lottery_name_match.group(1).strip().upper() if lottery_name_match else "Unknown"
    
    # Extract lottery code from URL
    lottery_code_match = re.search(r'/kerala-lottery-result-([A-Z]+)-', result_url)
    lottery_code = lottery_code_match.group(1) if lottery_code_match else "XX"

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

    # If no prizes found, initialize with default structure
    if not prizes:
        for key, label in standard_labels.items():
            prizes[key] = {
                "amount": prize_amounts.get(key, 0),
                "label": label,
                "winners": ["Please wait, results will be published at 3 PM."]
            }
    else:
        # Add "Please wait" message to any prize category that has no winners
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
    
    # Generate filename in the correct format (e.g., SS-485-2025-09-16.json)
    # Remove the duplicate lottery code from draw_number if present
    clean_draw_number = draw_number
    if draw_number.startswith(lottery_code + "-"):
        clean_draw_number = draw_number[len(lottery_code) + 1:]
    
    filename = f"{lottery_code}-{clean_draw_number}-{draw_date}.json"
    filepath = f"note/{filename}"
    
    try:
        # ONLY save if the result is "real" (contains actual winning numbers)
        if is_result_real(prizes):
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Saved: {filepath}\n")
        else:
            print(f"Skipping {filename}: Results are not yet fully published (placeholders found).\n")
    except Exception as e:
        print(f"Error saving {filepath}: {e}")


# --- MAIN EXECUTION ---
# Define the list of URLs to process
urls_to_process = [
    'https://www.kllotteryresult.com/kerala-lottery-result-KR-730',
    'https://www.kllotteryresult.com/kerala-lottery-result-SK-26', 
    'https://www.kllotteryresult.com/kerala-lottery-result-SM-28', 
    'https://www.kllotteryresult.com/kerala-lottery-result-BT-28', 
    'https://www.kllotteryresult.com/kerala-lottery-result-SS-493',
    'https://www.kllotteryresult.com/kerala-lottery-result-DL-26',
    'https://www.kllotteryresult.com/kerala-lottery-result-KN-597',
    'https://www.kllotteryresult.com/kerala-lottery-result-SK-27', 
    'https://www.kllotteryresult.com/kerala-lottery-result-KR-731', 
    'https://www.kllotteryresult.com/kerala-lottery-result-SM-29', 
    'https://www.kllotteryresult.com/kerala-lottery-result-KN-596',
    'https://www.kllotteryresult.com/kerala-lottery-result-DL-25',
    'https://www.kllotteryresult.com/kerala-lottery-result-SS-492',
    'https://www.kllotteryresult.com/kerala-lottery-result-BT-27', 
    'https://www.kllotteryresult.com/kerala-lottery-result-SM-27', 
    'https://www.kllotteryresult.com/kerala-lottery-result-KR-729',
    'https://www.kllotteryresult.com/kerala-lottery-result-SK-25', 
    'https://www.kllotteryresult.com/kerala-lottery-result-KN-595', 
    'https://www.kllotteryresult.com/kerala-lottery-result-DL-24', 
    'https://www.kllotteryresult.com/kerala-lottery-result-SS-491', 
    'https://www.kllotteryresult.com/kerala-lottery-result-BT-26', 
    'https://www.kllotteryresult.com/kerala-lottery-result-SM-26', 
    'https://www.kllotteryresult.com/kerala-lottery-result-KR-728',
    'https://www.kllotteryresult.com/kerala-lottery-result-SK-24', 
    'https://www.kllotteryresult.com/kerala-lottery-result-KN-594', 
    'https://www.kllotteryresult.com/kerala-lottery-result-DL-23', 
    'https://www.kllotteryresult.com/kerala-lottery-result-SS-490',
    'https://www.kllotteryresult.com/kerala-lottery-result-BT-25', 
    'https://www.kllotteryresult.com/kerala-lottery-result-SM-25', 
    'https://www.kllotteryresult.com/kerala-lottery-result-KR-727',
    'https://www.kllotteryresult.com/kerala-lottery-result-SK-23',
    'https://www.kllotteryresult.com/kerala-lottery-result-KN-593',
    'https://www.kllotteryresult.com/kerala-lottery-result-DL-22', 
    'https://www.kllotteryresult.com/kerala-lottery-result-SS-489',
    'https://www.kllotteryresult.com/kerala-lottery-result-BT-24', 
    'https://www.kllotteryresult.com/kerala-lottery-result-SM-24', 
    'https://www.kllotteryresult.com/kerala-lottery-result-KR-726', 
    'https://www.kllotteryresult.com/kerala-lottery-result-SK-22', 
    'https://www.kllotteryresult.com/kerala-lottery-result-KN-592',
    'https://www.kllotteryresult.com/kerala-lottery-result-DL-21',
    'https://www.kllotteryresult.com/kerala-lottery-result-SS-488',
    'https://www.kllotteryresult.com/kerala-lottery-result-BT-23', 
    'https://www.kllotteryresult.com/kerala-lottery-result-SM-23', 
    'https://www.kllotteryresult.com/kerala-lottery-result-KR-725',
    'https://www.kllotteryresult.com/kerala-lottery-result-BR-105',
    'https://www.kllotteryresult.com/kerala-lottery-result-SK-21', 
    'https://www.kllotteryresult.com/kerala-lottery-result-DL-20',
    'https://www.kllotteryresult.com/kerala-lottery-result-SS-487', 
    'https://www.kllotteryresult.com/kerala-lottery-result-BT-22', 
    'https://www.kllotteryresult.com/kerala-lottery-result-SM-22',
    'https://www.kllotteryresult.com/kerala-lottery-result-SK-20', 
    'https://www.kllotteryresult.com/kerala-lottery-result-KN-591',
    'https://www.kllotteryresult.com/kerala-lottery-result-DL-19',
    'https://www.kllotteryresult.com/kerala-lottery-result-SS-486', 
    'https://www.kllotteryresult.com/kerala-lottery-result-BT-21', 
    'https://www.kllotteryresult.com/kerala-lottery-result-SM-21',
    'https://www.kllotteryresult.com/kerala-lottery-result-KR-724', 
    'https://www.kllotteryresult.com/kerala-lottery-result-SK-19', 
    'https://www.kllotteryresult.com/kerala-lottery-result-KN-590',
    'https://www.kllotteryresult.com/kerala-lottery-result-DL-18',
    'https://www.kllotteryresult.com/kerala-lottery-result-SS-485', 
    'https://www.kllotteryresult.com/kerala-lottery-result-BT-20',
    'https://www.kllotteryresult.com/kerala-lottery-result-SM-20', 
    'https://www.kllotteryresult.com/kerala-lottery-result-KR-723',
    'https://www.kllotteryresult.com/kerala-lottery-result-SK-18',
    'https://www.kllotteryresult.com/kerala-lottery-result-KN-589',
    'https://www.kllotteryresult.com/kerala-lottery-result-DL-17',
    'https://www.kllotteryresult.com/kerala-lottery-result-SS-484', 
    'https://www.kllotteryresult.com/kerala-lottery-result-BT-19', 
    'https://www.kllotteryresult.com/kerala-lottery-result-SM-19',
    'https://www.kllotteryresult.com/kerala-lottery-result-KR-722',
    'https://www.kllotteryresult.com/kerala-lottery-result-KN-588', 
    'https://www.kllotteryresult.com/kerala-lottery-result-DL-16', 
    'https://www.kllotteryresult.com/kerala-lottery-result-SS-483', 
    'https://www.kllotteryresult.com/kerala-lottery-result-BT-18', 
    'https://www.kllotteryresult.com/kerala-lottery-result-SM-18', 
    'https://www.kllotteryresult.com/kerala-lottery-result-KR-721', 
    'https://www.kllotteryresult.com/kerala-lottery-result-SK-17', 
    'https://www.kllotteryresult.com/kerala-lottery-result-KN-587',
    'https://www.kllotteryresult.com/kerala-lottery-result-DL-15'
]

# Process each URL
print("Starting to download lottery results...")
for i, url in enumerate(urls_to_process, 1):
    print(f"Processing {i}/{len(urls_to_process)}: {url}")
    process_result_page(url)
    time.sleep(1)  # Be respectful to the server

print("All lottery results have been downloaded to the 'note' folder.")