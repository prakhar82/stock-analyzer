import yfinance as yf
from datetime import date
from dateutil.relativedelta import relativedelta

def get_chart_data(symbol: str, years: int):
    end = date.today()
    start = end - relativedelta(years=years)
    data = yf.download(f"{symbol}.NS", start=start, end=end, progress=False)

    if data.empty:
        return {"date": [], "pe_eps": [], "50dma": [], "200dma": []}

    data['50dma'] = data['Close'].rolling(window=50).mean()
    data['200dma'] = data['Close'].rolling(window=200).mean()
    
    # EPS data might not be available; here we fake with constant EPS = 15 as fallback
    eps = 15

    data['pe_eps'] = data['Close'] / eps

    data = data.dropna()

    return {
        "date": data.index.strftime('%Y-%m-%d').tolist(),
        "pe_eps": data['pe_eps'].round(2).tolist(),
        "50dma": data['50dma'].round(2).tolist(),
        "200dma": data['200dma'].round(2).tolist(),
    }
