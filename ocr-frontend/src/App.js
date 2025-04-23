import React, { useState } from 'react';
import axios from 'axios';
import './App.css'; // Import the CSS file

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [sourceLang, setSourceLang] = useState('ja');
  const [targetLang, setTargetLang] = useState('en');
  const [processedImage, setProcessedImage] = useState('');
  const [translatedTexts, setTranslatedTexts] = useState([]);
  const [statusLog, setStatusLog] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const languageOptions = [
    { value: 'en', label: 'English' },
    { value: 'ja', label: 'Japanese' }
  ];

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setPreview(URL.createObjectURL(selectedFile));
    setStatusLog([]);
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
    setTranslatedTexts([]);
    setStatusLog([]);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_lang', sourceLang);
    formData.append('target_lang', targetLang);

    try {
      const response = await axios.post('http://localhost:8000/process/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setProcessedImage(`http://localhost:8000${response.data.processed_image}`);
      setTranslatedTexts(response.data.translated_texts || []);
      setStatusLog(response.data.status_log || []);
    } catch (err) {
      setError('Processing failed. Please check the file and try again.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <h1 className="app-title">📘 Manga Panel Translator</h1>

      <form onSubmit={handleSubmit} className="upload-form">
        <div className="form-group">
          <label className="form-label">Upload File (.png, .jpg, .jpeg):</label>
          <input
            type="file"
            accept=".png,.jpg,.jpeg"
            onChange={handleFileChange}
            className="form-input"
          />
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

        <button type="submit" disabled={loading} className="submit-button">
          {loading ? 'Processing...' : 'Translate'}
        </button>

        {error && <div className="error-message">{error}</div>}
      </form>

      {preview && (
        <div className="preview-container">
          <h3>Original Preview:</h3>
          <img src={preview} alt="Preview" className="preview-image" />
        </div>
      )}

      {statusLog.length > 0 && (
        <div className="status-log-container">
          <h3>Processing Steps:</h3>
          <ol className="status-log-list">
            {statusLog.map((step, index) => (
              <li key={index}>{step}</li>
            ))}
          </ol>
        </div>
      )}

      {processedImage && (
        <div className="result-container">
          <h2>Processed Image:</h2>
          <img src={processedImage} alt="Processed" className="processed-image" />
          <div>
            <a href={processedImage} download className="download-button">
              Download Processed Image
            </a>
          </div>

          {translatedTexts.length > 0 && (
            <div className="translated-texts-container">
              <h3>Detected & Translated Texts:</h3>
              <ul className="translated-texts-list">
                {translatedTexts.map((item, idx) => (
                  <li key={idx}>
                    <strong>{item.text}</strong> (x: {item.position.x}, y: {item.position.y})
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
