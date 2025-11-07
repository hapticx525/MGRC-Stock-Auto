import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import os

# Bursa MGRC page
URL = "https://www.bursamalaysia.com/bm/trade/trading_resources/listing_directory/company-profile?stock_code=0155"
FILE = "everydayPrice.txt"

HEADER = "Date,Open,High,Low,Close,Volume,LACP,Change,Percentage Change,Day Range,Year Range\n"

def clean_num(val):
    if not val: return "0.000"
    val = val.replace(",", "").replace("(", "-").replace(")", "")
    try:
        return f"{float(val):.3f}"
    except:
        return "0.000"

def clean_int(val):
    if not val: return "0"
    val = val.replace(",", "")
    try:
        return str(int(val))
    except:
        return "0"

def parse_page():
    r = requests.get(URL, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    # Grab first row, first cell from table
    first_date_cell = soup.select_one("table tbody tr td")
    if not first_date_cell:
        raise Exception("Date cell not found in table")
    raw_date = first_date_cell.text.strip()
    dt = datetime.strptime(raw_date, "%d %b %Y")
    date_out = dt.strftime("%d/%m/%Y")

    # Extract table
    table = soup.find("table")
    if not table: raise Exception("Table not found")
    rows = table.find_all("tr")

    data = {}
    for row in rows:
        th = row.find("th")
        td = row.find("td")
        if not th or not td: continue
        key = th.text.strip().lower()
        val = td.text.strip()

        if "open" in key: data["Open"] = clean_num(val)
        elif "high" in key: data["High"] = clean_num(val)
        elif "low" in key: data["Low"] = clean_num(val)
        elif "close" in key: data["Close"] = clean_num(val)
        elif "volume" in key: data["Volume"] = clean_int(val)
        elif "previous" in key or "lacp" in key: data["LACP"] = clean_num(val)
        elif "change" == key: data["Change"] = clean_num(val)
        elif "%" in key: data["Pct"] = val.replace(" ", "")
        elif "day range" in key: data["DayRange"] = val
        elif "52 weeks" in key: data["YearRange"] = val

    return {
        "Date": date_out,
        "Open": data.get("Open", "0.000"),
        "High": data.get("High", "0.000"),
        "Low": data.get("Low", "0.000"),
        "Close": data.get("Close", "0.000"),
        "Volume": data.get("Volume", "0"),
        "LACP": data.get("LACP", "0.000"),
        "Change": data.get("Change", "0.000"),
        "Pct": data.get("Pct", "0.000%"),
        "DayRange": data.get("DayRange", "-"),
        "YearRange": data.get("YearRange", "-"),
    }

def update_file(row):
    new_line = f"{row['Date']},{row['Open']},{row['High']},{row['Low']},{row['Close']},{row['Volume']},{row['LACP']},{row['Change']},{row['Pct']},{row['DayRange']},{row['YearRange']}\n"

    # Read old file
    if os.path.exists(FILE):
        with open(FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = [HEADER]

    # If today's date already exists, skip
    if any(line.startswith(row['Date']) for line in lines[1:]):
        print(f"{row['Date']} already exists. No update.")
        return

    # Prepend new line after header
    out_lines = [lines[0], new_line] + lines[1:]

    with open(FILE, "w", encoding="utf-8") as f:
        f.writelines(out_lines)

    print(f"Added row for {row['Date']}")

def main():
    row = parse_page()
    update_file(row)

if __name__ == "__main__":
    main()
