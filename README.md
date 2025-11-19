# Chatbot Safety Testbed Platform

A comprehensive platform for evaluating chatbot safety and robustness through automated adversarial testing.

## Features

- **Automated Browser Navigation**: Navigate to any chatbot URL and interact with it automatically
- **LLM-Powered Testing**: Uses AI to generate progressively subtle and adversarial prompts
- **Real-Time Monitoring**: Watch the testing process in real-time through browser screenshots
- **Safety Evaluation**: Automatically evaluates if chatbots maintain safety guidelines
- **Configurable Testing**: Set number of rounds, topics, and adversarial intensity
- **Detailed Reports**: Get comprehensive reports on chatbot behavior and safety compliance

## Architecture

- **Backend**: FastAPI (Python) with WebSocket support
- **Browser Automation**: Playwright for headless/headed browser control
- **LLM Integration**: Supports multiple LLM providers (OpenAI, Anthropic, etc.)
- **Frontend**: React with real-time updates
- **Database**: SQLite for session storage

## Installation

### Prerequisites

- Python 3.8+
- Node.js 16+
- pip and npm

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Environment Configuration

Create a `.env` file in the backend directory:

```env
# LLM Provider Configuration
ANTHROPIC_API_KEY=your_api_key_here
OPENAI_API_KEY=your_api_key_here
LLM_PROVIDER=anthropic  # or 'openai'

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Testing Configuration
DEFAULT_MAX_ROUNDS=10
DEFAULT_ADVERSARIAL_INTENSITY=5  # 1-10 scale
```

## Usage

### Start the Backend

```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000`

### Start the Frontend

```bash
cd frontend
npm start
```

The UI will be available at `http://localhost:3000`

### Running a Test

1. Open the web interface
2. Enter the chatbot URL you want to test
3. Configure test parameters:
   - **Topic**: The subject for conversation (e.g., "customer support", "general chat")
   - **Number of Rounds**: How many conversation turns (default: 10)
   - **Adversarial Intensity**: How subtle/adversarial the prompts should become (1-10)
   - **CSS Selectors**: Input field and submit button selectors (optional, auto-detected if not provided)
4. Click "Start Test"
5. Monitor the real-time testing process
6. Review the safety evaluation report

## How It Works

### 1. Browser Automation
The platform uses Playwright to:
- Navigate to the target chatbot URL
- Identify the chat interface (input field, submit button)
- Send messages and capture responses
- Take screenshots for monitoring

### 2. Adversarial Prompt Generation
The testing LLM generates prompts that:
- Start benign and gradually become more subtle
- Test various safety boundaries
- Use sophisticated techniques (jailbreaks, prompt injection, etc.)
- Adapt based on chatbot responses

### 3. Safety Evaluation
Each response is analyzed for:
- Compliance with safety guidelines
- Presence of harmful content
- Handling of adversarial inputs
- Consistency of safety measures

### 4. Reporting
Generates comprehensive reports including:
- Conversation transcript
- Safety scores per round
- Identified vulnerabilities
- Recommendations for improvement

## API Documentation

### Start Test Session
```
POST /api/test/start
{
  "url": "https://example.com/chat",
  "topic": "customer support",
  "max_rounds": 10,
  "adversarial_intensity": 5,
  "selectors": {
    "input": "#chat-input",
    "submit": "#send-button"
  }
}
```

### WebSocket Connection
```
ws://localhost:8000/ws/{session_id}
```

Real-time events:
- `browser_screenshot`: Base64 encoded screenshot
- `message_sent`: Testing bot message
- `message_received`: Chatbot response
- `safety_evaluation`: Safety analysis for each round
- `test_complete`: Final results

## Safety & Ethics

This tool is designed for:
- Testing your own chatbot deployments
- Security research and red-teaming
- Quality assurance and safety validation
- Educational purposes

**Do not use this tool to:**
- Test chatbots without authorization
- Perform malicious attacks
- Violate terms of service
- Cause harm or disruption

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please read CONTRIBUTING.md for guidelines.

## Support

For issues and questions, please open a GitHub issue.
