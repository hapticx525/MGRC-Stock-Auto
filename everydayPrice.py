import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

FILE = "everydayPrice.txt"
HEADER = "Date,Open,High,Low,Close,Volume,Change,Percentage Change,Day Range,Year Range\n"

def fetch_latest_data():
    print("🔍 Fetching live MGRC data from Bursa Malaysia (stock_prices_main.jsp)...")
    url = "https://www.bursamalaysia.com/market_information/stock_prices_main.jsp?stock_code=0155"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # find all <td> inside price table
    cells = [c.text.strip() for c in soup.find_all("td")]
    if not cells or len(cells) < 10:
        raise Exception("⚠️ Unable to parse Bursa page structure. HTML changed or market closed.")

    # Extract key data points
    stock_name = cells[0]
    last_done = cells[1]
    change = cells[2]
    pct_change = cells[3]
    volume = cells[4]
    open_price = cells[5]
    high = cells[6]
    low = cells[7]
    day_range = f"{low}-{high}"

    today = datetime.today().strftime("%d/%m/%Y")

    print(f"📊 {stock_name}: {last_done} ({change}, {pct_change})")

    return {
        "Date": today,
        "Open": open_price,
        "High": high,
        "Low": low,
        "Close": last_done,
        "Volume": volume.replace(",", ""),
        "Change": change,
        "Pct": pct_change,
        "DayRange": day_range,
        "YearRange": "-",  # not available on this endpoint
    }

def update_file(row):
    if not os.path.exists(FILE):
        with open(FILE, "w", encoding="utf-8") as f:
            f.write(HEADER)

    with open(FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if any(row["Date"] in line for line in lines):
        print(f"✅ {row['Date']} already exists, skipping update.")
        return

    new_line = f"{row['Date']},{row['Open']},{row['High']},{row['Low']},{row['Close']},{row['Volume']},{row['Change']},{row['Pct']},{row['DayRange']},{row['YearRange']}\n"
    lines.insert(1, new_line)

    with open(FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"🆕 Added record for {row['Date']}")

def main():
    today = datetime.today().strftime("%A")
    if today in ["Saturday", "Sunday"]:
        print("⏸ Market closed, skipping weekend.")
        return

    try:
        row = fetch_latest_data()
        update_file(row)
        print(f"✅ Update completed successfully ({row['Date']}).")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
