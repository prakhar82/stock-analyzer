import requests
from bs4 import BeautifulSoup
import re
import traceback
import random
from nsepython import nse_fno, nse_eq
import diskcache as dc

# Initialize cache
cache = dc.Cache('./cache')


# -------------------------------
# Cached function (30 min expiry)
# -------------------------------
@cache.memoize(expire=1800)  # 30 minutes
def get_stock_info_base(symbol: str) -> dict:
    print(f"[CACHE MISS] Fetching live NSE + Screener data for {symbol}")
    price = None
    source = "nse_fno"
    pe_ratio = None
    eps = None
    valuation = "Unknown"

    try:
        quote = nse_fno(symbol)
        if quote and isinstance(quote, dict) and "data" in quote and quote["data"]:
            price = quote["data"][0].get("lastPrice")
            pe_ratio = quote["data"][0].get("pE")
            eps = quote["data"][0].get("eps")
        else:
            print(f"[DEBUG] nse_fno empty for {symbol}, trying nse_eq")
    except Exception as e:
        print(f"[ERROR] nse_fno failed for {symbol}: {e}")
        traceback.print_exc()

    if price is None or price == 0:
        try:
            quote = nse_eq(symbol)
            price = quote["priceInfo"]["lastPrice"]
            pe_ratio = quote.get("metadata", {}).get("pdSectorPe")
            eps = quote.get("metadata", {}).get("eps")
            source = "nse_eq"
        except Exception as e:
            print(f"[ERROR] nse_eq failed for {symbol}: {e}")
            traceback.print_exc()
            try:
                symbol_ns = symbol if symbol.endswith('.NS') else symbol + '.NS'
                quote = nse_eq(symbol_ns)
                price = quote["priceInfo"]["lastPrice"]
                pe_ratio = quote.get("metadata", {}).get("pdSectorPe")
                eps = quote.get("metadata", {}).get("eps")
                source = "nse_eq_with_NS"
            except Exception as e2:
                print(f"[ERROR] nse_eq with .NS failed for {symbol_ns}: {e2}")
                traceback.print_exc()
                return {"symbol": symbol, "error": "Not found in nse_fno or nse_eq"}

    try:
        pe = float(pe_ratio)
        if pe < 20:
            valuation = "Undervalued"
        elif pe > 35:
            valuation = "Overvalued"
        else:
            valuation = "Fair"
    except Exception:
        valuation = "Unknown"

    fiidi_trend = fetch_fiidi_trend_screener(symbol)
    if not fiidi_trend:
        fiidi_trend = {
            "quarters": [], "fii": [], "dii": [], "status": "stable"
        }

    company_name = get_company_name(symbol)

    return {
        "symbol": symbol,
        "company_name": company_name,
        "current_price": round(price, 2),
        "valuation": valuation,
        "data_source": source,
        "fiidi_trend": fiidi_trend
    }


# -------------------------------
# Dynamic (per user) response
# -------------------------------
def get_stock_info(symbol: str, qty: int = 0, avg_price: float = 0.0) -> dict:
    base = get_stock_info_base(symbol)
    if "error" in base:
        return base

    price = base["current_price"]
    investment = qty * avg_price
    current_value = qty * price
    change = price - avg_price if avg_price else 0
    change_percent = (change / avg_price * 100) if avg_price else 0

    best_multiplier = random.uniform(2.0, 3.5)
    worst_multiplier = random.uniform(0.5, 1.2)
    best_case = round(current_value * best_multiplier, 2)
    worst_case = round(current_value * worst_multiplier, 2)

    recommendation = get_ai_recommendation(symbol, base["valuation"], price, avg_price)

    return {
        **base,
        "quantity": qty,
        "average_price": avg_price,
        "investment": round(investment, 2),
        "current_value": round(current_value, 2),
        "change": round(change, 2),
        "change_percent": round(change_percent, 2),
        "recommendation": recommendation,
        "institutional_recommendation": recommendation,
        "3yr_best_case_value": best_case,
        "3yr_worst_case_value": worst_case,
    }


# -------------------------------
# Screener FII/DII Trend
# -------------------------------
def fetch_fiidi_trend_screener(symbol: str) -> dict:
    url = f"https://www.screener.in/company/{symbol}/consolidated/"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        quarter_headers = soup.select("table.data-table th")
        quarters = [
            th.get_text(strip=True)
            for th in quarter_headers
            if re.match(r"[A-Za-z]{3} \d{2}", th.get_text(strip=True))
        ][:4]

        fii_row = None
        dii_row = None
        for tr in soup.select("table.data-table tr"):
            tds = tr.find_all("td")
            if not tds:
                continue
            label = tds[0].get_text(strip=True).lower()
            if "foreign institutional investors" in label or "fii" in label:
                fii_row = [float(td.get_text(strip=True).replace('%', '') or 0) for td in tds[1:5]]
            elif "domestic institutional investors" in label or "dii" in label:
                dii_row = [float(td.get_text(strip=True).replace('%', '') or 0) for td in tds[1:5]]

        if not fii_row or not dii_row:
            return {}

        fii_status = "increase" if fii_row[0] > fii_row[1] else "decrease"
        dii_status = "increase" if dii_row[0] > dii_row[1] else "decrease"
        status = "stable"
        if fii_status == "increase" or dii_status == "increase":
            status = "increase"
        elif fii_status == "decrease" or dii_status == "decrease":
            status = "decrease"

        return {
            "quarters": quarters,
            "fii": fii_row,
            "dii": dii_row,
            "status": status
        }

    except Exception as e:
        print(f"[ERROR] Failed to fetch FII/DII data from Screener for {symbol}: {e}")
        traceback.print_exc()
        return {}


# -------------------------------
# AI Recommendation
# -------------------------------
def get_ai_recommendation(symbol: str, valuation: str, price: float, avg_price: float) -> str:
    if not avg_price or not price:
        return "HOLD"

    if valuation == "Undervalued" and price < 0.8 * avg_price:
        return "Strong Buy"
    elif valuation == "Undervalued" and price < avg_price:
        return "Buy"
    elif valuation == "Overvalued" and price > 1.3 * avg_price:
        return "Strong Sell"
    elif valuation == "Overvalued" and price > avg_price:
        return "Sell"
    elif price > 2 * avg_price:
        return "EXIT"
    elif price > 1.5 * avg_price:
        return "PARTIAL EXIT"
    elif price < 0.85 * avg_price:
        return "TOP-UP"
    else:
        return "HOLD"


# -------------------------------
# Screener Company Name
# -------------------------------
def get_company_name(symbol: str) -> str:
    try:
        url = f"https://www.screener.in/company/{symbol}/"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        name_tag = soup.select_one("h1")
        if name_tag:
            return name_tag.get_text(strip=True)
    except Exception as e:
        print(f"[ERROR] Could not fetch company name for {symbol}: {e}")
    return ""
