import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import time

# === Configuration ===
URL = "https://www.bursamalaysia.com/market_information/stock_prices_main.jsp?stock_code=0155"
FILE = "everydayPrice.txt"
HEADER = "Date,Open,High,Low,Close,Volume,LACP,Change,Percentage Change,Day Range,Year Range\n"

# === Helpers ===
def clean_num(val):
    if not val:
        return "0.000"
    val = val.replace(",", "").replace("(", "-").replace(")", "")
    try:
        return f"{float(val):.3f}"
    except:
        return "0.000"

def clean_int(val):
    if not val:
        return "0"
    val = val.replace(",", "")
    try:
        return str(int(val))
    except:
        return "0"

# === Core Scraper ===
def fetch_latest_data():
    print("🔍 Fetching live MGRC data from Bursa Malaysia (stock_prices_main.jsp)...")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.bursamalaysia.com/"
    }

    # Retry up to 3 times (handles temporary 403 or timeout)
    for attempt in range(3):
        try:
            r = requests.get(URL, headers=headers, timeout=30)
            r.raise_for_status()
            break
        except requests.exceptions.HTTPError as e:
            if r.status_code == 403:
                print(f"⚠️ 403 Forbidden (attempt {attempt+1}/3) – retrying in 5s...")
                time.sleep(5)
            else:
                raise
        except Exception as e:
            print(f"⚠️ Network error (attempt {attempt+1}/3): {e}")
            time.sleep(5)
    else:
        raise Exception("❌ Failed after 3 attempts – Bursa may be blocking bot traffic.")

    soup = BeautifulSoup(r.text, "html.parser")

    cells = [c.text.strip() for c in soup.find_all("td")]
    if not cells or len(cells) < 10:
        raise Exception("⚠️ Unable to parse Bursa page structure. HTML changed or market closed.")

    stock_name = cells[0]
    last_done = clean_num(cells[1])
    change = clean_num(cells[2])
    pct_change = cells[3].strip()
    volume = clean_int(cells[4])
    open_price = clean_num(cells[5])
    high = clean_num(cells[6])
    low = clean_num(cells[7])
    day_range = f"{low}-{high}"

    today = datetime.today().strftime("%d/%m/%Y")

    print(f"📊 {stock_name}: {last_done} ({change}, {pct_change})")

    return {
        "Date": today,
        "Open": open_price,
        "High": high,
        "Low": low,
        "Close": last_done,
        "Volume": volume,
        "LACP": last_done,
        "Change": change,
        "Pct": pct_change,
        "DayRange": day_range,
        "YearRange": "-",
    }

# === File Update ===
def update_file(row):
    if not os.path.exists(FILE):
        with open(FILE, "w", encoding="utf-8") as f:
            f.write(HEADER)

    with open(FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if any(row["Date"] in line for line in lines):
        print(f"✅ {row['Date']} already exists, skipping update.")
        return

    new_line = (
        f"{row['Date']},{row['Open']},{row['High']},{row['Low']},{row['Close']},"
        f"{row['Volume']},{row['LACP']},{row['Change']},{row['Pct']},"
        f"{row['DayRange']},{row['YearRange']}\n"
    )
    lines.insert(1, new_line)

    with open(FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"🆕 Added record for {row['Date']}")

# === Main Process ===
def main():
    today = datetime.today().strftime("%A")
    if today in ["Saturday", "Sunday"]:
        print("⏸ Market closed (Weekend). Skipping scrape.")
        return

    try:
        row = fetch_latest_data()
        update_file(row)
        print(f"✅ Update completed successfully ({row['Date']}).")
    except Exception as e:
        print(f"❌ Error: {e}")

# === Entry Point ===
if __name__ == "__main__":
    main()
