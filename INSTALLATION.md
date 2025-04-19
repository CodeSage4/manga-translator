# Installation Guide

## Local Development Setup

### Prerequisites

- Node.js (v14+)
- Python (v3.8+)
- Docker and Docker Compose
- Redis
- Tesseract OCR
- Poppler (for PDF processing)

### Setting Up the Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```
   The frontend will be available at http://localhost:3000

### Setting Up the Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at http://localhost:8000

### Installing PDF Dependencies

The application requires Poppler for PDF processing. Install it based on your operating system:

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y poppler-utils
```

#### macOS
```bash
brew install poppler
```

#### Windows
1. Download the latest poppler release from: https://github.com/oschwartz10612/poppler-windows/releases
2. Extract it to a directory (e.g., C:\poppler)
3. Add the bin directory to your PATH: 
   ```
   set PATH=%PATH%;C:\poppler\bin
   ```
4. Or set the path in your .env file:
   ```
   POPPLER_PATH=C:\poppler\bin
   ```

### Setting Up Redis

Redis is required for the Celery task queue:

```bash
# Install Redis (Ubuntu/Debian)
sudo apt-get install redis-server

# Install Redis (macOS with Homebrew)
brew install redis

# Start Redis
redis-server
```

### Setting Up Celery Worker

```bash
cd backend
celery -A app.tasks worker --loglevel=info
```

## Docker Setup (Recommended)

For the easiest setup, use Docker Compose:

1. Make sure Docker and Docker Compose are installed
2. Run the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. Start the application:
   ```bash
   docker-compose up -d
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs

## Troubleshooting

### Common Issues

1. **Port conflicts**: If ports 3000 or 8000 are already in use, modify the port mappings in docker-compose.yml

2. **Missing Tesseract languages**: Install additional language packs:
   ```bash
   sudo apt-get install tesseract-ocr-jpn tesseract-ocr-eng tesseract-ocr-chi-sim
   ```

3. **Worker not processing tasks**: Ensure Redis is running and accessible

4. **PDF processing errors**: Make sure Poppler is correctly installed and visible in your PATH. Check the POPPLER_PATH environment variable if using custom installation locations. 