# Manga Translator

An application for automatically translating manga images and PDFs using OCR and machine translation.

## Features

- Upload manga images (JPG, PNG) and PDF files
- OCR text extraction with Tesseract
- Translation between multiple languages
- Text re-insertion with formatting preservation
- PDF processing with page-by-page translation
- PDF preview with pagination controls
- Progress tracking for large files
- Preview and download of translated manga

## Prerequisites

- Docker and Docker Compose
- 8GB+ RAM (for running OCR and translation models)
- Poppler (for PDF processing with pdf2image)

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/manga-translator.git
cd manga-translator
```

### 2. Start the application

```bash
docker-compose up -d
```

The first startup may take several minutes as it builds the containers and downloads necessary dependencies.

### 3. Access the application

Open your browser and navigate to:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs

## PDF Processing

The application supports manga in PDF format with the following workflow:
1. PDF files are split into individual pages using pdf2image
2. Each page is processed with OCR to extract text
3. Extracted text is translated to the target language
4. Translated text is rendered back onto each page
5. Pages are recombined into a single translated PDF

For best results with PDF files:
- Ensure the PDF contains high-quality scans
- Select the correct source language for optimal OCR
- PDFs with complex layouts may require longer processing time

## Development

### Running services individually

#### Frontend

```bash
cd frontend
npm install
npm start
```

#### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Worker

```bash
cd backend
celery -A app.tasks worker --loglevel=info
```

## Architecture

- **Frontend**: React.js with Tailwind CSS
- **Backend**: FastAPI with PostgreSQL
- **Processing**: Celery workers with Redis queue
- **OCR**: Tesseract & OpenCV
- **Translation**: MarianMT models
- **PDF Processing**: pdf2image & ReportLab
- **Storage**: Local filesystem or cloud (S3/GCP)

## License

MIT 