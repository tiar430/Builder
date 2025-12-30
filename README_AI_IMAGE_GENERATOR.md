# 🎨 AI Image Generator - Img2Img dengan Face Restoration

Web App untuk generate AI image variations menggunakan Stable Diffusion dengan face preservation dan restoration otomatis.

## ✨ Fitur Utama

### 🖼️ Image Generation
- **Img2Img Transformation**: Upload gambar dan transform dengan AI
- **Multiple Variations**: Generate 1-5 variasi berbeda dalam satu kali proses
- **Face Detection**: Deteksi wajah otomatis menggunakan OpenCV
- **Face Restoration**: Enhancement wajah otomatis dengan bilateral filtering dan sharpening
- **Parameter Control**: Kontrol penuh atas strength, guidance scale, steps, dan sampler

### 🎛️ Parameter yang Dapat Dikontrol

1. **Prompt**: Deskripsi style yang diinginkan (contoh: "professional portrait, cinematic lighting")
2. **Negative Prompt**: Hal yang ingin dihindari (contoh: "malformed, distorted, blurry")
3. **Strength** (0.2-0.45): Seberapa banyak transformasi (lebih rendah = lebih preservasi wajah)
4. **Guidance Scale** (6-9): Seberapa ketat mengikuti prompt
5. **Inference Steps** (20-40): Quality vs speed tradeoff
6. **Number of Variations** (1-5): Berapa banyak variasi yang ingin digenerate

### 📱 Mobile Optimized
- Responsive design untuk Samsung Z Fold 4
- Touch-friendly controls
- Drag & drop image upload
- Smooth animations dan transitions

## 🏗️ Arsitektur Sistem

```
┌─────────────────────────────────────────────────┐
│         Samsung Z Fold 4 Browser                │
│              (Android)                          │
└────────────────┬────────────────────────────────┘
                 │ HTTP/REST API
                 ▼
┌─────────────────────────────────────────────────┐
│         Angular Frontend (Port 3000)            │
│  • Image Upload Component                       │
│  • Parameter Controls                           │
│  • Results Gallery                              │
│  • Download Functionality                       │
└────────────────┬────────────────────────────────┘
                 │ REST API
                 ▼
┌─────────────────────────────────────────────────┐
│         FastAPI Backend (Port 8001)             │
│  • Image Upload & Validation                    │
│  • Face Detection (OpenCV)                      │
│  • Image Preprocessing                          │
│  • Face Enhancement                             │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│       Hugging Face Inference API (FREE)         │
│  • Stable Diffusion 2.1                         │
│  • Text-to-Image Generation                     │
└─────────────────────────────────────────────────┘
```

## 🚀 Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Hugging Face Hub**: Free AI model inference
- **OpenCV**: Face detection dan image processing
- **Pillow (PIL)**: Image manipulation
- **NumPy**: Array operations

### Frontend
- **Angular 20**: Modern web framework
- **Tailwind CSS**: Utility-first CSS framework
- **TypeScript**: Type-safe JavaScript
- **RxJS**: Reactive programming

### Infrastructure
- **Supervisor**: Process management
- **Nginx**: Reverse proxy
- **MongoDB**: Database (optional untuk history)

## 📦 Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Hugging Face Account (gratis)

### 1. Clone & Install Dependencies

```bash
# Backend
cd /app/backend
pip install -r requirements.txt

# Frontend
cd /app
npm install
```

### 2. Configuration

Create `/app/backend/.env`:
```env
HUGGINGFACE_TOKEN=your_hf_token_here
ALLOWED_ORIGINS=http://localhost:3000
PORT=8001
```

### 3. Start Services

```bash
# Start all services with Supervisor
sudo supervisorctl start all

# Check status
sudo supervisorctl status

# View logs
tail -f /var/log/supervisor/backend.out.log
tail -f /var/log/supervisor/frontend.out.log
```

## 🎯 Cara Penggunaan

### 1. Akses Web App
Buka browser di Samsung Z Fold 4:
```
http://localhost:3000
```

### 2. Upload Gambar
- Klik area upload atau drag & drop gambar
- Supports: PNG, JPG, WEBP (max 10MB)
- Sistem akan otomatis detect wajah jika ada

### 3. Configure Parameters
- **Prompt**: Masukkan deskripsi style yang diinginkan
- **Strength**: 0.35 (recommended untuk face preservation)
- **Guidance Scale**: 7.5 (recommended)
- **Steps**: 30 (balance quality dan speed)
- **Variations**: 3 (generate 3 variasi)

### 4. Generate
- Klik tombol "✨ Generate Images"
- Tunggu proses (±30-60 detik untuk 3 variasi)
- Hasil akan muncul di panel kanan

### 5. Download
- Hover gambar hasil
- Klik tombol "Download"
- Gambar tersimpan di device

## 🔧 API Endpoints

### Health Check
```bash
GET /api/health
```

Response:
```json
{
  "status": "healthy",
  "service": "AI Image Generator",
  "version": "1.0.0",
  "hf_token_configured": true
}
```

### Upload Image
```bash
POST /api/upload
Content-Type: multipart/form-data

file: <image_file>
```

Response:
```json
{
  "success": true,
  "file_id": "uuid-here",
  "filename": "uuid.jpg",
  "url": "/uploads/uuid.jpg",
  "size": {"width": 1024, "height": 768},
  "has_face": true,
  "message": "Face detected"
}
```

### Generate Images
```bash
POST /api/generate
Content-Type: multipart/form-data

file_id: <uuid>
prompt: "professional portrait"
negative_prompt: "malformed, distorted"
strength: 0.35
guidance_scale: 7.5
num_inference_steps: 30
num_variations: 3
```

Response:
```json
{
  "success": true,
  "message": "Successfully generated 3 variations",
  "images": [
    "/outputs/uuid_var1.png",
    "/outputs/uuid_var2.png",
    "/outputs/uuid_var3.png"
  ],
  "metadata": {
    "prompt": "professional portrait",
    "has_face": true,
    "timestamp": "2025-12-30T18:00:00"
  }
}
```

### Get History
```bash
GET /api/history
```

### Clear Images
```bash
DELETE /api/clear
```

## 🎨 Face Enhancement Pipeline

1. **Face Detection**: OpenCV Haar Cascade
2. **Face Region Extraction**: Dengan margin 50px
3. **Bilateral Filtering**: Smoothing sambil preserve edges
4. **Sharpening**: Kernel convolution
5. **Color Correction**: CLAHE pada LAB color space
6. **Region Replacement**: Paste enhanced face back

## 💡 Tips & Best Practices

### Untuk Hasil Terbaik:
1. **Upload gambar berkualitas tinggi** (min 512x512px)
2. **Gunakan lighting yang baik** pada gambar input
3. **Wajah menghadap kamera** (frontal view)
4. **Strength 0.2-0.45** untuk preserve face structure
5. **Clear prompt** yang descriptive

### Contoh Prompt yang Baik:
```
✅ "professional business portrait, studio lighting, high quality, detailed"
✅ "cinematic portrait, dramatic lighting, film grain, professional"
✅ "natural portrait, soft lighting, outdoor, bokeh background"

❌ "make it better" (terlalu vague)
❌ "change face" (tidak descriptive)
```

### Performance Tips:
- **Steps 20-25**: Fast, decent quality
- **Steps 30**: Balanced (recommended)
- **Steps 35-40**: Best quality, slower

## 🔒 Free Tier Limits

### Hugging Face Inference API (FREE):
- ✅ Unlimited requests dengan rate limiting
- ✅ Stable Diffusion 2.1 model
- ✅ Text-to-Image generation
- ⚠️ Request timeout: 60 seconds
- ⚠️ Queue time: bisa bervariasi

### Tips Mengelola Free Tier:
1. Generate beberapa variasi sekaligus (efisien)
2. Gunakan steps 20-30 (lebih cepat)
3. Jika timeout, coba lagi atau reduce steps

## 🐛 Troubleshooting

### Backend Tidak Start
```bash
# Check logs
tail -f /var/log/supervisor/backend.err.log

# Common issue: Missing dependencies
pip install -r /app/backend/requirements.txt

# Restart
sudo supervisorctl restart backend
```

### Frontend Tidak Start
```bash
# Check logs
tail -f /var/log/supervisor/frontend.err.log

# Install dependencies
cd /app && npm install

# Restart
sudo supervisorctl restart frontend
```

### Face Detection Tidak Bekerja
- Pastikan wajah terlihat jelas (min 30x30px)
- Wajah menghadap kamera (frontal)
- Lighting cukup (tidak terlalu gelap)

### Generation Timeout
- Reduce `num_inference_steps` (coba 20-25)
- Reduce `num_variations` (coba 1-2)
- Coba lagi (Hugging Face bisa sedang busy)

### CORS Error
- Check `/app/backend/.env` - pastikan `ALLOWED_ORIGINS` include frontend URL
- Restart backend: `sudo supervisorctl restart backend`

## 📊 Performance Benchmarks

| Configuration | Time per Image | Total (3 vars) |
|--------------|----------------|----------------|
| Steps: 20    | ~10-15s        | ~30-45s       |
| Steps: 30    | ~15-20s        | ~45-60s       |
| Steps: 40    | ~20-25s        | ~60-75s       |

*Note: Waktu bisa bervariasi tergantung Hugging Face server load*

## 🔄 Update & Maintenance

### Update Dependencies
```bash
# Backend
cd /app/backend
pip install --upgrade huggingface-hub pillow opencv-python-headless

# Frontend
cd /app
npm update
```

### Clear Cache
```bash
# Clear generated images
curl -X DELETE http://localhost:8001/api/clear

# Clear uploads
rm -rf /app/backend/uploads/*
rm -rf /app/backend/outputs/*
```

## 📝 Project Structure

```
/app/
├── backend/
│   ├── server.py           # FastAPI main application
│   ├── .env               # Environment variables
│   ├── requirements.txt   # Python dependencies
│   ├── uploads/          # Uploaded images directory
│   └── outputs/          # Generated images directory
│
├── src/
│   └── app/
│       ├── app.ts        # Angular main component
│       ├── app.html      # Angular template
│       └── app.css       # Angular styles
│
├── angular.json          # Angular configuration
├── package.json          # Node.js dependencies
├── tailwind.config.js    # Tailwind CSS config
└── README_AI_IMAGE_GENERATOR.md  # This file
```

## 🎓 Credits & Technologies

- **Stable Diffusion 2.1**: StabilityAI
- **Hugging Face**: Model hosting dan inference
- **OpenCV**: Computer vision library
- **FastAPI**: Modern web framework
- **Angular**: Frontend framework
- **Tailwind CSS**: Styling

## 📄 License

MIT License - Free to use untuk personal dan commercial projects.

## 🆘 Support

Jika menemukan issue atau butuh bantuan:
1. Check troubleshooting section di atas
2. Check logs di `/var/log/supervisor/`
3. Verify semua services running: `sudo supervisorctl status`

---

**Built with ❤️ untuk Samsung Z Fold 4**

**Status: 🟢 Production Ready**
