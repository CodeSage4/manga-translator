# Installation Guide

## Local Development Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn
- Poppler (for PDF processing)

### Setting Up the Frontend
```bash
cd frontend
npm install
npm start
```
### Setting Up the Backend
```bash cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```