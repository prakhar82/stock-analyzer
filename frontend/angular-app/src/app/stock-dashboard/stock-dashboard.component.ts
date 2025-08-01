import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { StockService, Stock, PortfolioSummary } from '../services/stock.service';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

// Define interface for the response from getStocks and uploadStockCSV
interface StockListResponse {
  stocks: Stock[];
  portfolio_summary: PortfolioSummary;
}

type SortableField = keyof Stock | 'profit_loss';

@Component({
  selector: 'app-stock-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './stock-dashboard.component.html',
  styleUrls: ['./stock-dashboard.component.scss']
})
export class StockDashboardComponent implements OnInit {
  stocks: Stock[] = [];
  uploadMessage: { [symbol: string]: string } = {};

  portfolioSummary: PortfolioSummary = {
    total_investment: 0,
    '3yr_total_best': 0,
    '3yr_total_worst': 0
  };
  sortField: string = 'symbol';
  sortDirection: 'asc' | 'desc' = 'asc';
  filterText: string = '';

  csvUploadMessage: string = '';

  startDate: string = '';
  endDate: string = '';

  selectedFile: File | null = null;

  openTopup: string | null = null;
  topupData: { [symbol: string]: { quantity: number; price: number; date: string; entry_type: string } } = {};

  openFiidi: string | null = null;

  constructor(private stockService: StockService) {}

  ngOnInit(): void {
    this.fetchStocks();
  }

  fetchStocks(): void {
    this.stockService.getStocks().subscribe((response) => {
      this.stocks = response.stocks.map(stock => ({
        ...stock,
        profit_loss: stock.current_price * stock.quantity - stock.investment
      }));

      this.portfolioSummary = response.portfolio_summary;

      for (let stock of this.stocks) {
        if (!this.topupData[stock.symbol]) {
          this.topupData[stock.symbol] = { quantity: 0, price: 0, date: '', entry_type: 'Buy' };
        }
      }
    });
  }

  sortBy(field: string): void {
    if (this.sortField === field) {
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortField = field;
      this.sortDirection = 'asc';
    }
  }

  onFileSelected(event: any): void {
    this.selectedFile = event.target.files[0];
  }

  uploadFile(): void {
    if (this.selectedFile) {
      this.stockService.uploadStockCSV(this.selectedFile).subscribe({
        next: (response: StockListResponse) => {
          this.stocks = response.stocks;
          this.portfolioSummary = response.portfolio_summary;
          this.csvUploadMessage = 'Upload successful!';
          for (let stock of this.stocks) {
            if (!this.topupData[stock.symbol]) {
            this.topupData[stock.symbol] = { quantity: 0, price: 0, date: '', entry_type: 'Buy' };
            }
          }
        },
        error: () => {
          this.csvUploadMessage = 'Upload failed.';
        }
      });
    }
  }

  

  sortedStocks(): Stock[] {
    return this.stocks.slice().sort((a, b) => {
      const valueA = a[this.sortField as keyof Stock] ?? 0;
      const valueB = b[this.sortField as keyof Stock] ?? 0;

      if (typeof valueA === 'number' && typeof valueB === 'number') {
        return this.sortDirection === 'asc' ? valueA - valueB : valueB - valueA;
      }

      const aStr = String(valueA).toLowerCase();
      const bStr = String(valueB).toLowerCase();
      return this.sortDirection === 'asc'
        ? aStr.localeCompare(bStr)
        : bStr.localeCompare(aStr);
    });
  }

  toggleTopup(symbol: string, event: Event): void {
    event.stopPropagation();
    this.openTopup = this.openTopup === symbol ? null : symbol;
  }

  
  submitTopup(symbol: string): void {
  const data = this.topupData[symbol];
  if (!data.quantity || !data.price || !data.date || !data.entry_type) return;

  this.stockService.topupStock(symbol, data).subscribe({
    next: (response: StockListResponse) => {
      this.stocks = response.stocks;
      this.portfolioSummary = response.portfolio_summary;
      this.uploadMessage[symbol] = `Top-up for ${symbol} added successfully ✅`;

      // Keep the entry_type default to "Buy" after reset
      this.topupData[symbol] = { quantity: 0, price: 0, date: '', entry_type: 'Buy' };
    },
    error: () => {
      this.uploadMessage[symbol] = `Failed to add top-up for ${symbol} ❌`;
    }
  });
  }






  toggleFiidi(symbol: string, event: Event): void {
    event.stopPropagation();
    this.openFiidi = this.openFiidi === symbol ? null : symbol;
  }

  downloadCSV(): void {
    const header = Object.keys(this.stocks[0]).filter(k => k !== 'topups');
    const csvRows = [
      header.join(','),
      ...this.stocks.map(stock => header.map(h => (stock as any)[h]).join(','))
    ];
    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'portfolio.csv';
    link.click();
  }

  downloadPDF(): void {
  const doc = new jsPDF();

  const headers = [['Symbol', 'Current Price', 'Quantity', 'Avg Price', 'Investment', 'Valuation', 'Recommendation', '3yr Best', '3yr Worst']];

  const data = this.stocks.map(stock => [
    stock.symbol,
    stock.current_price,
    stock.quantity,
    stock.average_price,
    stock.investment,
    stock.valuation,
    stock.recommendation,
    stock['3yr_best_case_value'],
    stock['3yr_worst_case_value'],
  ]);

  autoTable(doc, {
    head: headers,
    body: data,
  });

  doc.save('stock-portfolio.pdf');
}

downloadTopupReport(startDate: string, endDate: string): void {
  this.stockService.downloadTopupPdf(startDate, endDate).subscribe(blob => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `topup_report_${startDate}_to_${endDate}.pdf`;
    link.click();
    window.URL.revokeObjectURL(url);
  });
}


}


