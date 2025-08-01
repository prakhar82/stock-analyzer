import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpEventType } from '@angular/common/http';


@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './upload.component.html',
  styleUrls: ['./upload.component.scss']
})
export class Upload {
  selectedFile: File | null = null;
  message: string = '';

  constructor(private http: HttpClient) {}

  onFileSelected(event: Event) {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (file) {
      this.selectedFile = file;
    }
  }

  uploadFile() {
    if (!this.selectedFile) {
      this.message = 'No file selected.';
      return;
    }

    const formData = new FormData();
    formData.append('file', this.selectedFile);

    this.http.post('http://localhost:8000/stock/upload_csv', formData).subscribe({
      next: (res: any) => {
        this.message = 'Upload successful!';
      },
      error: (err) => {
        this.message = 'Upload failed.';
      }
    });
  }
}