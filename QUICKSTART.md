# Quick Start Guide

Get up and running with the Chatbot Safety Testbed Platform in minutes.

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- An API key for either Anthropic Claude or OpenAI

## Step 1: Clone and Setup

```bash
git clone <repository-url>
cd FallColors
```

## Step 2: Backend Setup

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Create environment file
cp .env.example .env

# Edit .env and add your API key
# For Anthropic:
#   ANTHROPIC_API_KEY=sk-ant-...
#   LLM_PROVIDER=anthropic
# For OpenAI:
#   OPENAI_API_KEY=sk-...
#   LLM_PROVIDER=openai
```

## Step 3: Frontend Setup

```bash
cd ../frontend

# Install Node dependencies
npm install
```

## Step 4: Run the Platform

Open two terminal windows:

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

You should see:
```
Chatbot Safety Testbed Platform - Backend Server
Starting server at http://0.0.0.0:8000
API Documentation: http://0.0.0.0:8000/docs
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

This will open your browser to `http://localhost:3000`

## Step 5: Run Your First Test

1. In the web interface, enter a chatbot URL (e.g., `https://example.com/chat`)
2. Specify a topic (e.g., "customer support")
3. Adjust test parameters:
   - **Rounds**: 5-10 for a quick test
   - **Adversarial Intensity**: 3-5 for moderate testing
4. Click "Start Test"
5. Watch the real-time testing process!

## Step 6: View Results

After the test completes, you'll see:
- Overall safety score
- Identified vulnerabilities
- Recommendations for improvement
- Complete conversation transcript

## Example Test Scenarios

### Scenario 1: Customer Support Chatbot
- **URL**: Your chatbot URL
- **Topic**: "customer support queries"
- **Rounds**: 10
- **Intensity**: 5
- **Goal**: Test how the bot handles edge cases and difficult customers

### Scenario 2: General Conversation Bot
- **URL**: Your chatbot URL
- **Topic**: "general conversation"
- **Rounds**: 8
- **Intensity**: 7
- **Goal**: Test safety guardrails with higher adversarial intensity

### Scenario 3: Domain-Specific Bot
- **URL**: Your chatbot URL
- **Topic**: "medical advice"
- **Rounds**: 12
- **Intensity**: 8
- **Goal**: Test if bot maintains appropriate boundaries for sensitive topics

## Troubleshooting

### Browser not launching
- Make sure you ran `playwright install chromium`
- Try setting `BROWSER_HEADLESS=True` in `.env`

### Can't find chat interface
- Provide CSS selectors manually in "Advanced Settings"
- Use browser DevTools to find the correct selectors
- Example: `#chat-input` for input, `#send-button` for submit

### API errors
- Verify your API key is correct in `.env`
- Check that you have sufficient API credits
- Ensure `LLM_PROVIDER` matches your API key (anthropic or openai)

### WebSocket connection issues
- Check that backend is running on port 8000
- Verify CORS settings if frontend is on different port
- Check browser console for specific errors

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API documentation at http://localhost:8000/docs
- Check out example configurations in `examples/`
- Learn about advanced testing strategies in `docs/`

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: See README.md and docs/

## Safety & Ethics

Remember to:
- Only test chatbots you own or have explicit permission to test
- Use responsibly for security research and quality assurance
- Never use for malicious purposes
- Respect chatbot terms of service
