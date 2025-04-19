# Testing the Manga Translator

## Manual Testing Workflow

### 1. Basic Functionality Test

1. Open the frontend at http://localhost:3000
2. Upload a manga image (try sample images from `test_data/`)
3. Select Japanese as source language and English as target language
4. Click "Translate Manga"
5. Verify the progress bar appears and advances
6. Check the preview of the translated manga
7. Download the result and verify it contains translated text

### 2. Error Handling Test

1. Try uploading an unsupported file type (e.g., .txt file)
2. Verify appropriate error message is displayed
3. Try selecting the same language for source and target
4. Check if appropriate warnings appear

### 3. PDF Processing Test

1. Upload a multi-page manga PDF
2. Verify all pages are processed and translated
3. Check navigation between pages in the preview
4. Download and verify the complete PDF

## Common Issues and Solutions

### OCR Not Working Properly

- Check if Tesseract is installed correctly in the container
- Verify the image quality is good enough for OCR
- Try adjusting preprocessing parameters in OCR service

### Translation Issues

- Verify the language codes are mapped correctly
- Check if the translation model is available and downloaded
- Try with shorter text segments if there are timeout issues

### Performance Issues

- Increase worker resources in docker-compose.yml
- Consider using a more powerful machine for processing
- For production, set up multiple worker instances 