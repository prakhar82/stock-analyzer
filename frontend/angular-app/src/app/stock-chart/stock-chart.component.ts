import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgChartsModule } from 'ng2-charts';
import type { ChartData, ChartOptions } from 'chart.js';

@Component({
  selector: 'app-stock-chart',
  standalone: true,
  imports: [CommonModule, FormsModule, NgChartsModule],
  templateUrl: './stock-chart.component.html',
  styleUrls: ['./stock-chart.component.scss']
})
export class StockChartComponent implements OnInit {
  symbol = '';
  yearRange = 1;
  loading = true;
  errorMessage = '';
  chartLabels: string[] = [];
  lineChartData: ChartData<'line'> = { labels: [], datasets: [] };
  lineChartOptions: ChartOptions = { responsive: true };
  lineChartType: 'line' = 'line';

  constructor(private route: ActivatedRoute, private http: HttpClient) {}

  ngOnInit(): void {
    this.symbol = this.route.snapshot.paramMap.get('symbol')!;
    this.yearRange = Number(this.route.snapshot.paramMap.get('year'));
    this.loadChartData();
  }

  loadChartData() {
    this.loading = true;
    this.http.get<any>(`http://127.0.0.1:8000/stock/chart-data/${this.symbol}/${this.yearRange}`).subscribe({
      next: (data) => {
        this.chartLabels = data.date;
        this.lineChartData = {
          labels: data.date,
          datasets: [
            {
              label: 'Close Price',
              data: data.close,
              borderColor: '#42A5F5',
              fill: false,
            },
            {
              label: '50 DMA',
              data: data['50dma'],
              borderColor: '#66BB6A',
              fill: false,
            },
            {
              label: '200 DMA',
              data: data['200dma'],
              borderColor: '#FFA726',
              fill: false,
            }
          ]
        };
        this.loading = false;
      },
      error: (err) => {
        this.errorMessage = 'Error loading chart data.';
        this.loading = false;
      }
    });
  }
}
