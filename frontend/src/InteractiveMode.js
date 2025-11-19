import React, { useState } from 'react';
import axios from 'axios';
import './InteractiveMode.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

function InteractiveMode() {
  const [url, setUrl] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sessionInfo, setSessionInfo] = useState(null);
  const [screenshot, setScreenshot] = useState(null);

  const handleOpenBrowser = async () => {
    if (!url) {
      setError('Please enter a URL');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Open interactive browser session
      const response = await axios.post(`${API_BASE_URL}/interactive/open`, {
        url: url
      });

      setSessionId(response.data.session_id);
      setSessionInfo(response.data);

      // Get initial screenshot if available
      if (response.data.screenshot) {
        setScreenshot(response.data.screenshot);
      }

      setError('');
    } catch (err) {
      console.error('Failed to open browser:', err);
      setError(err.response?.data?.detail || 'Failed to open browser session');
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshScreenshot = async () => {
    if (!sessionId) return;

    try {
      const response = await axios.get(`${API_BASE_URL}/interactive/${sessionId}/screenshot`);
      setScreenshot(response.data.screenshot);
    } catch (err) {
      console.error('Failed to refresh screenshot:', err);
      setError('Failed to refresh screenshot');
    }
  };

  const handleCloseBrowser = async () => {
    if (!sessionId) return;

    try {
      await axios.delete(`${API_BASE_URL}/interactive/${sessionId}`);
      setSessionId(null);
      setSessionInfo(null);
      setScreenshot(null);
      setError('Browser session closed');
    } catch (err) {
      console.error('Failed to close browser:', err);
      setError('Failed to close browser session');
    }
  };

  return (
    <div className="interactive-mode">
      <div className="header">
        <h1>Chatbot Testbed - Interactive Mode</h1>
        <p className="subtitle">Phase 1: Open and interact with chatbot websites</p>
      </div>

      <div className="main-content">
        {!sessionId ? (
          <div className="url-input-section">
            <div className="input-group">
              <label htmlFor="url-input">Enter Chatbot URL:</label>
              <input
                id="url-input"
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com/chatbot"
                disabled={loading}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleOpenBrowser();
                  }
                }}
              />
            </div>

            <button
              className="open-button"
              onClick={handleOpenBrowser}
              disabled={loading || !url}
            >
              {loading ? 'Opening Browser...' : 'Open Browser'}
            </button>

            {error && <div className="error-message">{error}</div>}

            <div className="instructions">
              <h3>Instructions:</h3>
              <ol>
                <li>Enter the URL of the webpage where the chatbot is deployed</li>
                <li>Click "Open Browser" to launch an interactive browser window</li>
                <li>The browser will open in a new window where you can see and interact with the chatbot in real-time</li>
                <li>You can manually test the chatbot by typing messages and observing responses</li>
              </ol>
            </div>
          </div>
        ) : (
          <div className="session-active">
            <div className="session-info">
              <h2>Browser Session Active</h2>
              <div className="info-item">
                <strong>Session ID:</strong> <code>{sessionId}</code>
              </div>
              {sessionInfo && (
                <>
                  <div className="info-item">
                    <strong>URL:</strong> <a href={sessionInfo.url} target="_blank" rel="noopener noreferrer">{sessionInfo.url}</a>
                  </div>
                  <div className="info-item">
                    <strong>Page Title:</strong> {sessionInfo.title}
                  </div>
                  <div className="info-item status-success">
                    <strong>Status:</strong> {sessionInfo.message}
                  </div>
                </>
              )}
            </div>

            <div className="actions">
              <button
                className="refresh-button"
                onClick={handleRefreshScreenshot}
              >
                Refresh Screenshot
              </button>
              <button
                className="close-button"
                onClick={handleCloseBrowser}
              >
                Close Browser
              </button>
            </div>

            {screenshot && (
              <div className="screenshot-section">
                <h3>Current View:</h3>
                <img
                  src={`data:image/png;base64,${screenshot}`}
                  alt="Browser screenshot"
                  className="screenshot"
                />
              </div>
            )}

            {error && <div className="error-message">{error}</div>}

            <div className="notice">
              <p>The browser window is now open and visible on your screen. You can interact with it directly!</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default InteractiveMode;
