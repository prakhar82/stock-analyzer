from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import csv
import os
import traceback
import numpy as np
from typing import Dict, Any
from cachetools import TTLCache, cached
from fastapi.responses import FileResponse
from app.utils.pdf_export import get_topup_data_filtered, generate_topup_pdf,get_topup_data_with_gainloss



from app.services.finance_api import get_stock_info
from app.services.graphs import get_chart_data

router = APIRouter()

# Define paths

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data"))
STOCK_CSV = os.path.join(BASE_DIR, "stocks.csv")
TOPUP_DIR = os.path.join(BASE_DIR, "topups")
os.makedirs(TOPUP_DIR, exist_ok=True)

# Cache setup: cache up to 10 results, expire after 120 seconds
stock_cache = TTLCache(maxsize=10, ttl=120)

def convert_numpy_types(data):
    if isinstance(data, dict):
        return {k: convert_numpy_types(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_numpy_types(v) for v in data]
    elif isinstance(data, (np.integer, np.floating)):
        return data.item()
    else:
        return data

@router.get("/chart-data/{symbol}/{years}")
def get_chart(symbol: str, years: int = 1):
    try:
        return get_chart_data(symbol, years)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@cached(stock_cache)
def get_cached_stock_list() -> Dict[str, Any]:
    if not os.path.exists(STOCK_CSV):
        raise HTTPException(status_code=404, detail="Stock CSV not found")

    df = pd.read_csv(STOCK_CSV)
    stocks = []
    total_best = 0
    total_worst = 0
    total_investment = 0

    for _, row in df.iterrows():
        symbol = row["symbol"]
        base_qty = int(row["quantity"])
        base_avg_price = float(row["averageprice"])

        topup_file = os.path.join(TOPUP_DIR, f"{symbol}.csv")
        topups = []
        total_qty = base_qty
        total_cost = base_qty * base_avg_price

        if os.path.exists(topup_file):
            try:
                with open(topup_file, "r") as f:
                    reader = csv.DictReader(f)
                    for trow in reader:
                        qty = int(trow["quantity"])
                        price = float(trow["price"])
                        date = trow.get("date", "")
                        entry_type = trow.get("entry_type", "Buy").capitalize()

                        # Adjust quantity and cost based on entry_type
                        if entry_type == "Sell":
                            total_qty -= qty
                            total_cost -= qty * price
                        else:
                            total_qty += qty
                            total_cost += qty * price

                        topups.append({
                            "quantity": qty,
                            "price": price,
                            "date": date,
                            "entry_type": entry_type  # ✅ Fix: include entry_type
                        })
            except Exception as e:
                print(f"[ERROR] Error reading top-up file for {symbol}: {e}")

        final_avg_price = total_cost / total_qty if total_qty > 0 else 0.0

        info = get_stock_info(symbol, total_qty, final_avg_price)
        if "error" in info:
            continue

        current_price = info.get("current_price", 0)

        for t in topups:
            try:
                gain_loss = ((current_price - t["price"]) / t["price"]) * 100
                t["gain_loss_percent"] = round(gain_loss, 2)
            except ZeroDivisionError:
                t["gain_loss_percent"] = 0.0

        investment = round(total_cost, 2)
        total_investment += investment

        info.update({
            "quantity": total_qty,
            "average_price": round(final_avg_price, 2),
            "investment": investment,
            "topups": topups
        })

        total_best += info.get("3yr_best_case_value", 0)
        total_worst += info.get("3yr_worst_case_value", 0)

        stocks.append(info)

    return convert_numpy_types({
        "stocks": stocks,
        "portfolio_summary": {
            "3yr_total_best": round(total_best, 2),
            "3yr_total_worst": round(total_worst, 2),
            "total_investment": round(total_investment, 2)
        }
    })

@router.get("/list")
def list_stocks():
    try:
        return get_cached_stock_list()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload_csv")
async def upload_csv(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        with open(STOCK_CSV, "wb") as f:
            f.write(contents)
        stock_cache.clear()  # Invalidate cache after update
        return list_stocks()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/topup")
async def topup(data: dict):
    try:
        symbol = data["symbol"]
        qty = int(data["quantity"])
        price = float(data["price"])
        entry_type = data.get("entry_type", "Buy").capitalize()  # Buy/Sell
        date = data.get("date", "")

        if not os.path.exists(STOCK_CSV):
            raise HTTPException(status_code=404, detail="stocks.csv not found")

        df = pd.read_csv(STOCK_CSV)
        if symbol not in df["symbol"].values:
            raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found in stocks.csv")

        topup_file = os.path.join(TOPUP_DIR, f"{symbol}.csv")
        file_exists = os.path.exists(topup_file)

        with open(topup_file, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["quantity", "price", "entry_type", "date"])
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "quantity": qty,
                "price": price,
                "entry_type": entry_type,
                "date": date
            })

        stock_cache.clear()
        return list_stocks()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download-topup-pdf")
def download_topup_pdf(start_date: str, end_date: str):
    try:

        topup_data = get_topup_data_with_gainloss(start_date, end_date)
        output_path = os.path.join(TOPUP_DIR, "topup_report.pdf")
        
        generate_topup_pdf(topup_data, start_date, end_date, output_path)

        return FileResponse(output_path, filename="topup_report.pdf", media_type="application/pdf")
    except Exception as e:
        return {"detail": f"Error generating PDF: {e}"}
