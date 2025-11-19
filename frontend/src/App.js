import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/api';

function App() {
  const [testConfig, setTestConfig] = useState({
    url: '',
    topic: '',
    maxRounds: 10,
    adversarialIntensity: 5,
    inputSelector: '',
    submitSelector: '',
    headless: false
  });

  const [sessionId, setSessionId] = useState(null);
  const [testStatus, setTestStatus] = useState('idle'); // idle, running, completed, failed
  const [events, setEvents] = useState([]);
  const [currentScreenshot, setCurrentScreenshot] = useState(null);
  const [conversation, setConversation] = useState([]);
  const [finalReport, setFinalReport] = useState(null);
  const [sessions, setSessions] = useState([]);

  const wsRef = useRef(null);
  const eventsEndRef = useRef(null);

  // Fetch previous sessions on mount
  useEffect(() => {
    fetchSessions();
  }, []);

  // Scroll to bottom of events
  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const fetchSessions = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/test`);
      setSessions(response.data);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setTestConfig(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const startTest = async () => {
    try {
      // Reset state
      setEvents([]);
      setConversation([]);
      setFinalReport(null);
      setCurrentScreenshot(null);

      // Create test session
      const createResponse = await axios.post(`${API_BASE_URL}/test/start`, {
        url: testConfig.url,
        topic: testConfig.topic,
        max_rounds: parseInt(testConfig.maxRounds),
        adversarial_intensity: parseInt(testConfig.adversarialIntensity),
        input_selector: testConfig.inputSelector || null,
        submit_selector: testConfig.submitSelector || null,
        headless: testConfig.headless
      });

      const newSessionId = createResponse.data.session_id;
      setSessionId(newSessionId);
      setTestStatus('running');

      addEvent('info', `Test session created: ${newSessionId}`);

      // Connect WebSocket
      const ws = new WebSocket(`${WS_BASE_URL}/ws/${newSessionId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        addEvent('info', 'Connected to real-time updates');
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketEvent(data);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        addEvent('error', 'WebSocket connection error');
      };

      ws.onclose = () => {
        addEvent('info', 'WebSocket connection closed');
      };

      // Start the test
      await axios.post(`${API_BASE_URL}/test/${newSessionId}/run`);
      addEvent('success', 'Test started successfully');

    } catch (error) {
      console.error('Failed to start test:', error);
      addEvent('error', `Failed to start test: ${error.message}`);
      setTestStatus('failed');
    }
  };

  const handleWebSocketEvent = (event) => {
    const { type, data } = event;

    switch (type) {
      case 'test_started':
        addEvent('info', `Testing chatbot at: ${data.url}`);
        break;

      case 'browser_started':
        addEvent('info', 'Browser launched');
        break;

      case 'navigation_complete':
        addEvent('success', 'Successfully navigated to chatbot');
        break;

      case 'interface_found':
        addEvent('success', `Chat interface detected`);
        addEvent('info', `Input: ${data.input_selector}`);
        addEvent('info', `Submit: ${data.submit_selector}`);
        break;

      case 'screenshot':
        setCurrentScreenshot(data.image);
        break;

      case 'round_started':
        addEvent('info', `--- Round ${data.round}/${data.total_rounds} ---`);
        break;

      case 'prompt_generated':
        addEvent('info', `Test Prompt: ${data.prompt}`);
        break;

      case 'message_sent':
        addEvent('tester', data.message);
        break;

      case 'message_received':
        addEvent('chatbot', data.message);
        setConversation(prev => [...prev, {
          round: data.round,
          tester: events.find(e => e.type === 'tester')?.message,
          chatbot: data.message
        }]);
        break;

      case 'safety_evaluation':
        const eval_data = data.evaluation;
        addEvent('evaluation', `Safety Score: ${eval_data.overall_score}/10 - ${eval_data.passed ? 'PASSED' : 'FAILED'}`);
        if (eval_data.vulnerabilities && eval_data.vulnerabilities.length > 0) {
          addEvent('warning', `Vulnerabilities: ${eval_data.vulnerabilities.join(', ')}`);
        }
        break;

      case 'round_complete':
        addEvent('success', `Round ${data.round} completed`);
        break;

      case 'test_complete':
        addEvent('success', '=== Test Completed ===');
        setFinalReport(data.report);
        setTestStatus('completed');
        fetchSessions();
        break;

      case 'test_failed':
        addEvent('error', `Test failed: ${data.error}`);
        setTestStatus('failed');
        fetchSessions();
        break;

      case 'browser_stopped':
        addEvent('info', 'Browser closed');
        if (wsRef.current) {
          wsRef.current.close();
        }
        break;

      default:
        console.log('Unknown event type:', type);
    }
  };

  const addEvent = (type, message) => {
    setEvents(prev => [...prev, {
      type,
      message,
      timestamp: new Date().toLocaleTimeString()
    }]);
  };

  const loadSession = async (sessionId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/test/${sessionId}`);
      const session = response.data;

      // Display session results
      setSessionId(sessionId);
      setTestStatus(session.status);
      setConversation(session.conversation || []);
      setFinalReport({
        summary: {
          average_overall_score: session.overall_safety_score,
          total_vulnerabilities: session.vulnerabilities_found?.length || 0
        },
        vulnerabilities: session.vulnerabilities_found || [],
        recommendations: session.recommendations || []
      });

      // Populate events from conversation
      setEvents([]);
      session.conversation?.forEach((round, idx) => {
        addEvent('info', `--- Round ${idx + 1} ---`);
        addEvent('tester', round.tester);
        addEvent('chatbot', round.chatbot);
        if (round.safety_evaluation) {
          addEvent('evaluation', `Safety Score: ${round.safety_evaluation.overall_score}/10`);
        }
      });

    } catch (error) {
      console.error('Failed to load session:', error);
      alert('Failed to load session');
    }
  };

  const deleteSession = async (sessionId) => {
    if (!window.confirm('Are you sure you want to delete this session?')) {
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/test/${sessionId}`);
      fetchSessions();
      if (sessionId === sessionId) {
        setSessionId(null);
        setTestStatus('idle');
        setEvents([]);
        setConversation([]);
        setFinalReport(null);
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
      alert('Failed to delete session');
    }
  };

  return (
    <div className="App">
      <header className="header">
        <h1>🤖 Chatbot Safety Testbed Platform</h1>
        <p>Automated evaluation of chatbot safety and robustness</p>
      </header>

      <div className="container">
        {/* Left Panel - Configuration */}
        <div className="panel config-panel">
          <h2>Test Configuration</h2>

          <div className="form-group">
            <label>Chatbot URL *</label>
            <input
              type="text"
              name="url"
              value={testConfig.url}
              onChange={handleInputChange}
              placeholder="https://example.com/chat"
              disabled={testStatus === 'running'}
            />
          </div>

          <div className="form-group">
            <label>Topic *</label>
            <input
              type="text"
              name="topic"
              value={testConfig.topic}
              onChange={handleInputChange}
              placeholder="e.g., customer support, general conversation"
              disabled={testStatus === 'running'}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Rounds (1-20)</label>
              <input
                type="number"
                name="maxRounds"
                value={testConfig.maxRounds}
                onChange={handleInputChange}
                min="1"
                max="20"
                disabled={testStatus === 'running'}
              />
            </div>

            <div className="form-group">
              <label>Adversarial Intensity (1-10)</label>
              <input
                type="number"
                name="adversarialIntensity"
                value={testConfig.adversarialIntensity}
                onChange={handleInputChange}
                min="1"
                max="10"
                disabled={testStatus === 'running'}
              />
            </div>
          </div>

          <details className="advanced-settings">
            <summary>Advanced Settings (Optional)</summary>
            <div className="form-group">
              <label>Input Field CSS Selector</label>
              <input
                type="text"
                name="inputSelector"
                value={testConfig.inputSelector}
                onChange={handleInputChange}
                placeholder="e.g., #chat-input"
                disabled={testStatus === 'running'}
              />
            </div>

            <div className="form-group">
              <label>Submit Button CSS Selector</label>
              <input
                type="text"
                name="submitSelector"
                value={testConfig.submitSelector}
                onChange={handleInputChange}
                placeholder="e.g., #send-button"
                disabled={testStatus === 'running'}
              />
            </div>

            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  name="headless"
                  checked={testConfig.headless}
                  onChange={handleInputChange}
                  disabled={testStatus === 'running'}
                />
                Run in headless mode (no browser window)
              </label>
            </div>
          </details>

          <button
            className="btn btn-primary"
            onClick={startTest}
            disabled={testStatus === 'running' || !testConfig.url || !testConfig.topic}
          >
            {testStatus === 'running' ? '🔄 Testing...' : '▶ Start Test'}
          </button>

          {/* Previous Sessions */}
          <div className="sessions-list">
            <h3>Previous Sessions</h3>
            {sessions.length === 0 ? (
              <p className="no-sessions">No previous sessions</p>
            ) : (
              <div className="sessions">
                {sessions.map(session => (
                  <div key={session.session_id} className="session-item">
                    <div className="session-info">
                      <strong>{session.topic}</strong>
                      <span className={`status status-${session.status}`}>
                        {session.status}
                      </span>
                      {session.overall_safety_score && (
                        <span className="score">
                          Score: {session.overall_safety_score.toFixed(1)}/10
                        </span>
                      )}
                    </div>
                    <div className="session-actions">
                      <button
                        className="btn-small"
                        onClick={() => loadSession(session.session_id)}
                      >
                        View
                      </button>
                      <button
                        className="btn-small btn-danger"
                        onClick={() => deleteSession(session.session_id)}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Middle Panel - Live Events */}
        <div className="panel events-panel">
          <h2>Live Events {testStatus === 'running' && <span className="pulse">●</span>}</h2>

          <div className="events-log">
            {events.length === 0 ? (
              <p className="placeholder">Events will appear here when test is running...</p>
            ) : (
              events.map((event, idx) => (
                <div key={idx} className={`event event-${event.type}`}>
                  <span className="timestamp">[{event.timestamp}]</span>
                  <span className="message">{event.message}</span>
                </div>
              ))
            )}
            <div ref={eventsEndRef} />
          </div>

          {/* Browser Screenshot */}
          {currentScreenshot && (
            <div className="screenshot-container">
              <h3>Browser View</h3>
              <img
                src={`data:image/png;base64,${currentScreenshot}`}
                alt="Browser screenshot"
                className="screenshot"
              />
            </div>
          )}
        </div>

        {/* Right Panel - Results */}
        <div className="panel results-panel">
          <h2>Results & Analysis</h2>

          {finalReport ? (
            <div className="report">
              <div className="report-summary">
                <h3>Summary</h3>
                <div className="metric">
                  <label>Overall Safety Score</label>
                  <div className={`score-badge score-${getScoreClass(finalReport.summary.average_overall_score)}`}>
                    {finalReport.summary.average_overall_score?.toFixed(1) || 'N/A'}/10
                  </div>
                </div>
                <div className="metric">
                  <label>Vulnerabilities Found</label>
                  <div className="count">{finalReport.summary.total_vulnerabilities || 0}</div>
                </div>
              </div>

              {finalReport.vulnerabilities && finalReport.vulnerabilities.length > 0 && (
                <div className="report-section">
                  <h3>⚠️ Vulnerabilities</h3>
                  <ul>
                    {finalReport.vulnerabilities.map((vuln, idx) => (
                      <li key={idx} className="vulnerability">{vuln}</li>
                    ))}
                  </ul>
                </div>
              )}

              {finalReport.recommendations && finalReport.recommendations.length > 0 && (
                <div className="report-section">
                  <h3>💡 Recommendations</h3>
                  <ul>
                    {finalReport.recommendations.map((rec, idx) => (
                      <li key={idx} className="recommendation">{rec}</li>
                    ))}
                  </ul>
                </div>
              )}

              {conversation.length > 0 && (
                <div className="report-section">
                  <h3>📝 Conversation Transcript</h3>
                  <div className="conversation">
                    {conversation.map((round, idx) => (
                      <div key={idx} className="conversation-round">
                        <div className="round-header">Round {round.round}</div>
                        <div className="message message-tester">
                          <strong>Tester:</strong> {round.tester}
                        </div>
                        <div className="message message-chatbot">
                          <strong>Chatbot:</strong> {round.chatbot}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="placeholder">Results will appear here after test completion...</p>
          )}
        </div>
      </div>
    </div>
  );
}

function getScoreClass(score) {
  if (score >= 8) return 'good';
  if (score >= 6) return 'medium';
  return 'poor';
}

export default App;
