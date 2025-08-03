from fpdf import FPDF
import os

import os
import csv
from datetime import datetime
from typing import List, Dict

from app.services.finance_api import get_stock_info_base  # adjust import path

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/topups"))


def get_current_prices(symbols: List[str]) -> Dict[str, float]:
    prices = {}
    for symbol in symbols:
        try:
            info = get_stock_info_base(symbol)
            if "current_price" in info:
                prices[symbol] = info["current_price"]
        except Exception as e:
            print(f"[ERROR] Fetching price failed for {symbol}: {e}")
    return prices

def get_topup_data_with_gainloss(start_date: str, end_date: str) -> List[Dict]:
    raw_topups = get_topup_data_filtered(start_date, end_date)
    symbols = list(set(t["symbol"] for t in raw_topups))
    current_prices = get_current_prices(symbols)

    enriched_topups = []

    for row in raw_topups:
        price = row["price"]
        symbol = row["symbol"]
        qty = row["quantity"]
        entry_type = row.get("entry_type", "Buy").strip().capitalize()
        current_price = current_prices.get(symbol, price)
        gain_loss_percent = ((current_price - price) / price) * 100

        investment = price * qty if entry_type == "Buy" else -1 * price * qty

        enriched_topups.append({
            **row,
            "average_price": price,
            "gain_loss_percent": gain_loss_percent,
            "investment": investment,
        })
    return enriched_topups



def get_topup_data_filtered(start_date: str, end_date: str) -> List[Dict]:
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    filtered_topups = []

    for file in os.listdir(DATA_DIR):
        if not file.endswith(".csv"):
            continue
        symbol = file.replace(".csv", "")
        filepath = os.path.join(DATA_DIR, file)
        with open(filepath, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    row_date = datetime.strptime(row["date"], "%Y-%m-%d")
                    if start <= row_date <= end:
                        filtered_topups.append({
                            "symbol": symbol,
                            "date": row["date"],
                            "quantity": int(row["quantity"]),
                            "price": float(row["price"]),
                            "entry_type": row.get("entry_type", "Buy").strip().capitalize()
                        })
                except Exception:
                    continue
    return filtered_topups



def safe_unicode(text):
    """Replace unsupported characters for latin-1 PDF."""
    return str(text).replace("₹", "Rs.")


class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Top-up History Report", ln=True, align="C")
        self.ln(5)
        
def generate_topup_pdf(topup_data, start_date, end_date, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=safe_unicode(f"Top-up History Report ({start_date} to {end_date})"), ln=True, align='C')
    pdf.ln(10)

    # ✅ Table headers (bold)
    headers = ["Stock", "Date", "Type", "Quantity", "Avg Price", "Gain/Loss %"]
    col_width = 40
    pdf.set_font("Arial", "B", 11)
    for header in headers:
        pdf.cell(col_width, 10, safe_unicode(header), border=1, align='C')
    pdf.ln()

    total_invested = 0

    # ✅ Table body
    pdf.set_font("Arial", "", 10)
    for row in topup_data:
        pdf.cell(col_width, 10, safe_unicode(row["symbol"]), border=1)
        pdf.cell(col_width, 10, safe_unicode(row["date"]), border=1)

        # ✅ Colored 'Type' (Buy/Sell)
        entry_type = row["entry_type"]
        if entry_type.lower() == "buy":
            pdf.set_text_color(0, 128, 0)  # Green
        else:
            pdf.set_text_color(255, 0, 0)  # Red
        pdf.cell(col_width, 10, safe_unicode(entry_type), border=1)
        pdf.set_text_color(0, 0, 0)  # Reset color

        pdf.cell(col_width, 10, safe_unicode(str(row["quantity"])), border=1)
        pdf.cell(col_width, 10, safe_unicode(f"{row['average_price']:.2f}"), border=1)

        # ✅ Gain/Loss with color
        gain_loss = float(row.get("gain_loss_percent", 0))
        gain_color = (0, 128, 0) if gain_loss >= 0 else (255, 0, 0)
        pdf.set_text_color(*gain_color)
        pdf.cell(col_width, 10, safe_unicode(f"{gain_loss:.2f}%"), border=1)
        pdf.set_text_color(0, 0, 0)
        pdf.ln()

        total_invested += row.get("investment", 0)

    # ✅ Summary line
    pdf.ln(10)
    summary_color = (0, 128, 0) if total_invested >= 0 else (255, 0, 0)
    pdf.set_text_color(*summary_color)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt=safe_unicode(f"Net Investment (Buy - Sell): Rs. {total_invested:.2f}"), ln=True, align='C')
    pdf.set_text_color(0, 0, 0)

    pdf.output(output_path)

