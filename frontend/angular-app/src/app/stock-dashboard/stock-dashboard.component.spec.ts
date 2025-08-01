import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StockDashboardComponent } from './stock-dashboard.component';

describe('StockDashboardComponent', () => {
  let component: StockDashboardComponent;
  let fixture: ComponentFixture<StockDashboardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StockDashboardComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(StockDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
