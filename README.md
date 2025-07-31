# 📊 Stock Analyzer Dashboard

An interactive full-stack web app for analyzing stock performance, with features like CSV uploads, valuation metrics, expert recommendations, buy/sell/top-up tracking, PE/EPS and DMA charts, and exportable reports.

---

## 📁 Project Structure

```
stock-analyzer/
├── backend/
│   ├── main.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── stock.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── finance_api.py
│   │   │   └── graphs.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── pdf_export.py
│   │   ├── models/
│   │   │   └── stock_model.py
├── frontend/
│   └── angular-app/
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── data/
│   ├── stocks.csv
│   ├── topups.csv
```

---

## 🚀 Features

- Upload stock holdings via CSV (symbol, quantity, average price)
- Live data from NSE APIs with fallback logic
- Intelligent recommendation engine (Buy/Hold/Sell/Top-Up/Exit)
- PE-EPS and DMA (50/200) charts with 1–5 year range
- Display shareholding pattern & quarterly EPS on hover
- Buy/Sell top-up functionality with gain/loss and history
- PDF report generator for top-up transactions
- Portfolio summary: Best and worst-case 3-year projections
- Dockerized for easy setup

---

## 🐳 Docker Setup (No Python/Node.js needed)

### Prerequisites
- Docker & Docker Compose installed

### Run App

```bash
git clone https://github.com/yourusername/stock-analyzer.git
cd stock-analyzer
docker-compose up --build
```

Visit Angular UI: http://localhost:4200

---

## 🧱 Dockerfile.backend

```Dockerfile
# Dockerfile.backend
FROM python:3.10-slim

WORKDIR /app

COPY backend/ /app/
COPY data/ /app/data/

RUN pip install --no-cache-dir fastapi uvicorn pandas numpy matplotlib     yfinance nsepython beautifulsoup4 requests fpdf

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🧱 Dockerfile.frontend

```Dockerfile
# Dockerfile.frontend
FROM node:18-alpine

WORKDIR /app

COPY frontend/angular-app /app

RUN npm install -g @angular/cli     && npm install

EXPOSE 4200

CMD ["ng", "serve", "--host", "0.0.0.0"]
```

---

## 🧩 docker-compose.yml

```yaml
version: "3.8"

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "4200:4200"
    depends_on:
      - backend
```

---

## 📥 API Endpoints

- `POST /upload` - Upload stock CSV
- `GET /list` - Get enriched stock list with valuation, projections, etc.
- `GET /chart/{symbol}/{years}` - Get PE/DMA chart data
- `GET /topup-report?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Get top-up history with gain/loss
- `GET /topup-pdf?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - PDF download of top-up history

---

## 📈 Example Usage

- Upload your holdings via `stocks.csv`
- Click + to add Buy/Sell with date and price
- Hover to see shareholding trend and EPS
- Sort, filter, and export data as CSV/PDF

---

## 📌 Notes

- Fallback to `nse_eq` if `nse_fno` fails
- PDF gain/loss uses latest price vs top-up price
- Supports both Buy and Sell in top-up

---

## 📄 License

Prakhar Dwivedi
