import { Routes } from '@angular/router';
import { StockDashboardComponent } from './stock-dashboard/stock-dashboard.component';
import { Upload } from './upload/upload.component';
import { StockChartComponent } from './stock-chart/stock-chart.component'; // ✅ Add this line

export const appRoutes: Routes = [
  { path: 'dashboard', component: StockDashboardComponent },
  { path: 'upload', component: Upload },
  { path: 'chart/:symbol/:years', component: StockChartComponent }, // ✅ Add this route
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: '**', redirectTo: 'dashboard' }
];
