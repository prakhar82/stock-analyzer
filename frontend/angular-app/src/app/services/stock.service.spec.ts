import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

// Export interfaces here — no imports from this file itself
export interface TopupEntry {
  date: string;
  quantity: number;
  price: number;
  gain_loss_percent: number;
}

export interface FiidiTrend {
  quarters: string[];
  fii: number[];
  dii: number[];
  status: 'increase' | 'decrease' | 'stable';
}

export interface Stock {
  symbol: string;
  name?: string;             // Optional stock name if available
  current_price: number;
  quantity: number;
  average_price: number;
  investment: number;
  valuation: string;
  recommendation: string;
  '3yr_best_case_value': number;
  '3yr_worst_case_value': number;
  topups?: TopupEntry[];
  fiidi_trend?: FiidiTrend;
}

export interface PortfolioSummary {
  total_investment: number;
  '3yr_total_best': number;
  '3yr_total_worst': number;
}

@Injectable({
  providedIn: 'root'
})
export class StockService {
  private baseUrl = 'http://localhost:8000/stock';

  constructor(private http: HttpClient) {}

  getStocks(): Observable<{ stocks: Stock[]; portfolio_summary: PortfolioSummary }> {
    return this.http.get<{ stocks: Stock[]; portfolio_summary: PortfolioSummary }>(`${this.baseUrl}/list`);
  }

  uploadStockCSV(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.baseUrl}/upload_csv`, formData);
  }

  topupStock(symbol: string, data: { quantity: number; price: number; date: string }): Observable<any> {
    return this.http.post(`${this.baseUrl}/topup`, { symbol, ...data });
  }

  

}
