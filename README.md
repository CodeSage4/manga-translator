# Manga Translation System

## Overview
A modern web application for translating manga panels from Japanese to English. The system combines OCR technology with advanced AI translation to maintain cultural context and visual aesthetics.

## Key Features
- **Dual Text Detection**: Supports both horizontal and vertical Japanese text
- **Smart OCR**: PaddleOCR integration with orientation detection
- **Multi-layer Translation**:
  - Base translation via MyMemory API
  - Enhanced AI translation with Google Gemini
- **Visual Processing**:
  - Text box detection and highlighting
  - Translation overlay with proper formatting
  - Preview and download options
- **Context-Aware**: Optional manga context input for better translations
- **Real-time Updates**: Processing status tracking
- **Responsive UI**: Modern React-based interface

## Technologies
### Backend Stack
- FastAPI (Python)
- PaddleOCR
- Google Gemini AI
- OpenCV
- PIL (Python Imaging Library)

### Frontend Stack
- React.js
- Axios
- Modern CSS3
- Responsive Design

## Setup Instructions

### Prerequisites
- Node.js (v14+)
- Python (3.8+)
- poppler-utils (for PDF processing)

### Installation

1. **Clone Repository**
```bash
git clone https://github.com/yourusername/manga-translation-system.git
cd manga-translation-system
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

3. **Frontend Setup**
```bash
cd ../frontend
npm install
```

4. **Environment Configuration**
Create `.env` in backend directory:
```env
GEMINI_API_KEY=your_gemini_api_key
```

### Running the Application

1. **Start Backend**
```bash
cd backend
uvicorn main:app --reload
```

2. **Start Frontend**
```bash
cd frontend
npm start
```

Visit `http://localhost:3000` in your browser.

## API Documentation

### POST /process/
Process manga panel images

**Request Body (multipart/form-data)**:
- `file`: Image file (PNG/JPG)
- `source_lang`: Source language code
- `target_lang`: Target language code
- `manga_context`: Translation context (optional)
- `is_vertical_text`: Boolean flag for vertical text

**Response**:
```json
{
  "processed_image": "/static/processed/image.png",
  "visualized_boxes_image": "/static/boxes/image.png",
  "translated_texts": [
    {
      "original_text": "原文",
      "text": "Translation",
      "is_vertical": boolean,
      "base_translation": "Basic translation"
    }
  ],
  "status_log": ["Processing step 1", "Processing step 2"]
}
```

## Project Structure
```
manga-translation-system/
├── backend/
│   ├── static/
│   │   ├── uploads/
│   │   ├── processed/
│   │   └── boxes/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   └── App.css
│   └── package.json
└── README.md
```

## Contributing
1. Fork the repository
2. Create feature branch (`git checkout -b feature/NewFeature`)
3. Commit changes (`git commit -m 'Add NewFeature'`)
4. Push to branch (`git push origin feature/NewFeature`)
5. Create Pull Request

## License
MIT License

## Support
Open issues on GitHub repository for support requests.

