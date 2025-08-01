import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

// Export these interfaces
export interface Stock {
  symbol: string;
  company_name?: string;  // <-- add this to match backend field
  current_price: number;
  quantity: number;
  average_price: number;
  investment: number;
  valuation: string;
  recommendation: string;
  '3yr_best_case_value': number;
  '3yr_worst_case_value': number;
  topups?: any[];
  fiidi_trend?: any;
  profit_loss?: number;
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

  topupStock(symbol: string, data: { quantity: number; price: number; date: string; entry_type: string }): Observable<any> {
  return this.http.post(`${this.baseUrl}/topup`, { symbol, ...data });
  }

  downloadTopupPdf(startDate: string, endDate: string): Observable<Blob> {
  const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
  return this.http.get(`${this.baseUrl}/download-topup-pdf?${params.toString()}`, {
    responseType: 'blob' // Important for handling binary files like PDF
  });
}
}
