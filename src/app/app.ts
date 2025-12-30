import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpClientModule } from '@angular/common/http';

interface GeneratedImage {
  url: string;
  filename: string;
  created_at?: string;
}

interface UploadResponse {
  success: boolean;
  file_id: string;
  filename: string;
  url: string;
  has_face: boolean;
  message: string;
}

interface GenerateResponse {
  success: boolean;
  message: string;
  images: string[];
  metadata: any;
}

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, CommonModule, FormsModule, HttpClientModule],
  standalone: true,
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  private readonly API_URL = 'http://localhost:8001/api';
  
  // State signals
  protected uploadedImage = signal<string | null>(null);
  protected fileId = signal<string | null>(null);
  protected generatedImages = signal<GeneratedImage[]>([]);
  protected isUploading = signal(false);
  protected isGenerating = signal(false);
  protected hasFace = signal(false);
  protected statusMessage = signal('');
  
  // Form parameters
  protected prompt = signal('professional portrait, cinematic lighting, high quality');
  protected negativePrompt = signal('malformed, extra limbs, distorted, blurry, bad quality, ugly, deformed');
  protected strength = signal(0.35);
  protected guidanceScale = signal(7.5);
  protected steps = signal(30);
  protected numVariations = signal(3);
  protected sampler = signal('euler_a');
  
  protected samplers = ['euler_a', 'euler', 'ddim', 'dpm++'];
  
  constructor(private http: HttpClient) {}
  
  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      this.uploadImage(input.files[0]);
    }
  }
  
  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
  }
  
  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    
    if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
      this.uploadImage(event.dataTransfer.files[0]);
    }
  }
  
  uploadImage(file: File): void {
    if (!file.type.startsWith('image/')) {
      this.statusMessage.set('Please upload an image file');
      return;
    }
    
    this.isUploading.set(true);
    this.statusMessage.set('Uploading image...');
    
    const formData = new FormData();
    formData.append('file', file);
    
    this.http.post<UploadResponse>(`${this.API_URL}/upload`, formData).subscribe({
      next: (response) => {
        this.uploadedImage.set(`${this.API_URL.replace('/api', '')}${response.url}`);
        this.fileId.set(response.file_id);
        this.hasFace.set(response.has_face);
        this.statusMessage.set(response.message);
        this.isUploading.set(false);
      },
      error: (error) => {
        this.statusMessage.set(`Upload failed: ${error.error?.detail || error.message}`);
        this.isUploading.set(false);
      }
    });
  }
  
  generateImages(): void {
    if (!this.fileId()) {
      this.statusMessage.set('Please upload an image first');
      return;
    }
    
    this.isGenerating.set(true);
    this.statusMessage.set(`Generating ${this.numVariations()} variations...`);
    this.generatedImages.set([]);
    
    const formData = new FormData();
    formData.append('file_id', this.fileId()!);
    formData.append('prompt', this.prompt());
    formData.append('negative_prompt', this.negativePrompt());
    formData.append('strength', this.strength().toString());
    formData.append('guidance_scale', this.guidanceScale().toString());
    formData.append('num_inference_steps', this.steps().toString());
    formData.append('num_variations', this.numVariations().toString());
    
    this.http.post<GenerateResponse>(`${this.API_URL}/generate`, formData).subscribe({
      next: (response) => {
        const images = response.images.map(url => ({
          url: `${this.API_URL.replace('/api', '')}${url}`,
          filename: url.split('/').pop() || ''
        }));
        this.generatedImages.set(images);
        this.statusMessage.set(response.message);
        this.isGenerating.set(false);
      },
      error: (error) => {
        this.statusMessage.set(`Generation failed: ${error.error?.detail || error.message}`);
        this.isGenerating.set(false);
      }
    });
  }
  
  downloadImage(url: string, filename: string): void {
    fetch(url)
      .then(response => response.blob())
      .then(blob => {
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.click();
      });
  }
  
  reset(): void {
    this.uploadedImage.set(null);
    this.fileId.set(null);
    this.generatedImages.set([]);
    this.statusMessage.set('');
    this.hasFace.set(false);
  }
}
