import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [sourceLang, setSourceLang] = useState('ja');
  const [targetLang, setTargetLang] = useState('en');
  const [processedImage, setProcessedImage] = useState('');
  const [boxesImage, setBoxesImage] = useState('');
  const [translatedTexts, setTranslatedTexts] = useState([]);
  const [statusLog, setStatusLog] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mangaContext, setMangaContext] = useState('');
  const [isVerticalText, setIsVerticalText] = useState(false);

  const languageOptions = [
    { value: 'ja', label: 'Japanese' },
    { value: 'en', label: 'English' }
  ];

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));
      setStatusLog([]);
      setError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setLoading(true);
    setError('');
    setProcessedImage('');
    setBoxesImage('');
    setTranslatedTexts([]);
    setStatusLog([]);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_lang', sourceLang);
    formData.append('target_lang', targetLang);
    formData.append('show_boxes', true);
    formData.append('manga_context', mangaContext);
    formData.append('is_vertical_text', isVerticalText);

    try {
      const response = await axios.post('http://localhost:8000/process/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setProcessedImage(`http://localhost:8000${response.data.processed_image}`);
      
      if (response.data.visualized_boxes_image) {
        setBoxesImage(`http://localhost:8000${response.data.visualized_boxes_image}`);
      }
      
      setTranslatedTexts(response.data.translated_texts || []);
      setStatusLog(response.data.status_log || []);
    } catch (err) {
      console.error('Error:', err);
      setError('Processing failed. Please check the file and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1 className="app-title">📘 Manga Translation System</h1>
        <p className="app-subtitle">OCR, Translation, and Image Processing for Manga</p>
      </header>

      <main className="main-content">
        <div className="upload-section">
          <form onSubmit={handleSubmit} className="upload-form">
            <div className="form-group">
              <label className="form-label">Upload Manga Panel:</label>
              <input
                type="file"
                accept=".png,.jpg,.jpeg"
                onChange={handleFileChange}
                className="form-input"
              />
            </div>

            <div className="form-options">
              <div className="form-group checkbox-group">
                <input
                  type="checkbox"
                  id="isVerticalText"
                  checked={isVerticalText}
                  onChange={(e) => setIsVerticalText(e.target.checked)}
                />
                <label htmlFor="isVerticalText" className="checkbox-label">
                  Optimize for vertical text
                </label>
              </div>

              <div className="form-group">
                <label className="form-label">Source Language:</label>
                <select
                  value={sourceLang}
                  onChange={(e) => setSourceLang(e.target.value)}
                  className="form-select"
                >
                  {languageOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Target Language:</label>
                <select
                  value={targetLang}
                  onChange={(e) => setTargetLang(e.target.value)}
                  className="form-select"
                >
                  {languageOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Manga Context (optional):</label>
              <textarea
                value={mangaContext}
                onChange={(e) => setMangaContext(e.target.value)}
                placeholder="Provide context about the manga to improve translation (e.g., character info, setting, plot details)"
                className="form-textarea"
                rows={3}
              />
            </div>

            <button type="submit" disabled={loading} className="submit-button">
              {loading ? (
                <span className="loading-spinner"></span>
              ) : (
                'Translate'
              )}
            </button>

            {error && <div className="error-message">{error}</div>}
          </form>

          {preview && (
            <div className="preview-container">
              <h3 className="section-title">Original Image:</h3>
              <img src={preview} alt="Preview" className="preview-image" />
            </div>
          )}
        </div>

        {statusLog.length > 0 && (
          <div className="status-log-container">
            <h3 className="section-title">Processing Steps:</h3>
            <ol className="status-log-list">
              {statusLog.map((step, index) => (
                <li key={index} className="status-item">{step}</li>
              ))}
            </ol>
          </div>
        )}

        <div className="results-section">
          {(processedImage || boxesImage) && (
            <div className="images-grid">
              {boxesImage && (
                <div className="image-container">
                  <h3 className="section-title">OCR Detection:</h3>
                  <div className="image-wrapper">
                    <img src={boxesImage} alt="OCR Boxes" className="result-image" />
                  </div>
                  <div className="image-actions">
                    <a href={boxesImage} download className="download-button">
                      Download OCR Image
                    </a>
                  </div>
                </div>
              )}
              
              {processedImage && (
                <div className="image-container">
                  <h3 className="section-title">Translated Image:</h3>
                  <div className="image-wrapper">
                    <img src={processedImage} alt="Translated" className="result-image" />
                  </div>
                  <div className="image-actions">
                    <a href={processedImage} download className="download-button">
                      Download Translated Image
                    </a>
                  </div>
                </div>
              )}
            </div>
          )}

          {translatedTexts.length > 0 && (
            <div className="translated-texts-container">
              <h3 className="section-title">Detected & Translated Texts:</h3>
              <ul className="translated-texts-list">
                {translatedTexts.map((item, idx) => (
                  <li key={idx} className={`translation-item ${item.is_vertical ? 'vertical-text' : ''}`}>
                    <div className="text-pair">
                      <div className="original-text">
                        <span className="text-label">Japanese{item.is_vertical ? ' (Vertical)' : ' (Horizontal)'}:</span>
                        <span className="text-content">{item.original_text}</span>
                      </div>
                      <div className="translation">
                        <span className="text-label">English:</span>
                        <span className="text-content">{item.text}</span>
                      </div>
                    </div>
                    {item.base_translation && item.base_translation !== item.text && (
                      <div className="base-translation">
                        <span className="text-label">Basic Translation:</span>
                        <span className="text-content">{item.base_translation}</span>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </main>

      <footer className="app-footer">
        <p>Manga Translation System &copy; {new Date().getFullYear()}</p>
      </footer>
    </div>
  );
}

export default App;