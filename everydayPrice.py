import requests
from datetime import datetime
import os

FILE = "everydayPrice.txt"
HEADER = "Date,Open,High,Low,Close,Volume,Change,Percentage Change,Day Range,Year Range\n"

def fetch_latest_data():
    print("Fetching live MGRC data from Bursa Malaysia JSON API…")
    url = "https://www.bursamalaysia.com/market_information/stock_prices?format=json"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()

    # Find MGRC (0155)
    stock = None
    for s in data.get("quotes", []):
        if s.get("stock_code") == "0155":
            stock = s
            break

    if not stock:
        raise Exception("MGRC (0155) not found in Bursa feed")

    # Extract fields
    today = datetime.today().strftime("%d/%m/%Y")
    open_ = stock.get("open_price", "0.000")
    high = stock.get("high_price", "0.000")
    low = stock.get("low_price", "0.000")
    close = stock.get("last_done_price", "0.000")
    volume = stock.get("volume", "0")
    change = stock.get("change", "0.000")
    pct = stock.get("percentage_change", "0.00%")
    day_range = f"{low}-{high}"
    year_range = f"{stock.get('fifty_two_week_low', '-')}-{stock.get('fifty_two_week_high', '-')}"

    return {
        "Date": today,
        "Open": open_,
        "High": high,
        "Low": low,
        "Close": close,
        "Volume": volume,
        "Change": change,
        "Pct": pct,
        "DayRange": day_range,
        "YearRange": year_range
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
