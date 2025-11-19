# Example Test Configurations

This document provides example configurations for different testing scenarios.

## 1. Basic Safety Test (Low Intensity)

**Use Case**: Initial safety check for a new chatbot deployment

```json
{
  "url": "https://your-chatbot.example.com",
  "topic": "general conversation",
  "max_rounds": 5,
  "adversarial_intensity": 2,
  "headless": false
}
```

**Expected Behavior**:
- Simple, benign questions
- Basic edge cases
- Quick initial assessment
- Minimal adversarial techniques

---

## 2. Customer Support Bot Test (Medium Intensity)

**Use Case**: Testing a customer support chatbot's robustness

```json
{
  "url": "https://support.example.com/chat",
  "topic": "customer support and complaint handling",
  "max_rounds": 10,
  "adversarial_intensity": 5,
  "headless": false
}
```

**Expected Behavior**:
- Normal customer queries
- Difficult customer scenarios
- Edge cases (refunds, complaints, etc.)
- Moderate boundary testing

---

## 3. Advanced Safety Audit (High Intensity)

**Use Case**: Comprehensive security audit before production deployment

```json
{
  "url": "https://chatbot.example.com",
  "topic": "comprehensive safety evaluation",
  "max_rounds": 15,
  "adversarial_intensity": 8,
  "headless": false
}
```

**Expected Behavior**:
- Sophisticated prompt injection attempts
- Role-playing scenarios
- Boundary pushing
- Advanced adversarial techniques
- Subtle manipulation attempts

---

## 4. Medical Chatbot Safety Test

**Use Case**: Testing a medical advice chatbot's safety boundaries

```json
{
  "url": "https://health.example.com/chatbot",
  "topic": "medical information and advice",
  "max_rounds": 12,
  "adversarial_intensity": 7,
  "input_selector": "#medical-chat-input",
  "submit_selector": "#send-message",
  "headless": false
}
```

**Expected Behavior**:
- Test if bot appropriately disclaims medical advice
- Verify bot doesn't provide dangerous recommendations
- Check boundary maintenance for sensitive topics
- Evaluate handling of medical emergencies

---

## 5. Educational Chatbot Test

**Use Case**: Testing an educational tutoring chatbot

```json
{
  "url": "https://learn.example.com/tutor",
  "topic": "homework help and tutoring",
  "max_rounds": 8,
  "adversarial_intensity": 4,
  "headless": false
}
```

**Expected Behavior**:
- Test if bot encourages learning vs. giving answers
- Verify appropriate academic integrity boundaries
- Check handling of inappropriate requests
- Evaluate educational guidance quality

---

## 6. E-commerce Chatbot Test

**Use Case**: Testing a shopping assistant chatbot

```json
{
  "url": "https://shop.example.com/assistant",
  "topic": "product recommendations and purchases",
  "max_rounds": 10,
  "adversarial_intensity": 5,
  "input_selector": "#chat-input-field",
  "submit_selector": "button[aria-label='Send']",
  "headless": false
}
```

**Expected Behavior**:
- Test product recommendation accuracy
- Verify handling of price manipulation attempts
- Check refund/return policy consistency
- Evaluate upselling boundaries

---

## 7. Automated Regression Test (Headless)

**Use Case**: Automated testing in CI/CD pipeline

```json
{
  "url": "https://chatbot.example.com",
  "topic": "general functionality and safety",
  "max_rounds": 7,
  "adversarial_intensity": 5,
  "input_selector": "#message-input",
  "submit_selector": "#submit-btn",
  "headless": true
}
```

**Expected Behavior**:
- Runs without browser UI
- Quick automated checks
- Suitable for CI/CD integration
- Consistent baseline testing

---

## 8. Maximum Stress Test

**Use Case**: Extreme testing to find any possible vulnerabilities

```json
{
  "url": "https://chatbot.example.com",
  "topic": "comprehensive adversarial testing",
  "max_rounds": 20,
  "adversarial_intensity": 10,
  "headless": false
}
```

**Expected Behavior**:
- Maximum adversarial intensity
- All available techniques
- Sophisticated manipulation attempts
- Thorough vulnerability discovery

---

## Testing Different Chatbot Platforms

### For Chatbots with Standard Input Fields

Most chatbots use standard HTML input elements:

```json
{
  "input_selector": "input[type='text']",
  "submit_selector": "button[type='submit']"
}
```

### For Chatbots with Textarea

```json
{
  "input_selector": "textarea#chat-message",
  "submit_selector": "button.send-button"
}
```

### For Chatbots with ContentEditable Divs

```json
{
  "input_selector": "div[contenteditable='true']",
  "submit_selector": "svg[data-icon='send']"
}
```

### For Chatbots with Custom Components

Use browser DevTools to inspect:
1. Right-click on the input field → Inspect
2. Find the unique selector (ID, class, or attribute)
3. Do the same for the send button
4. Use those selectors in configuration

---

## API Usage Examples

### Using cURL

```bash
# Start a test session
curl -X POST http://localhost:8000/api/test/start \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://chatbot.example.com",
    "topic": "customer support",
    "max_rounds": 10,
    "adversarial_intensity": 5
  }'

# Response: {"session_id": "abc-123-def", ...}

# Run the test
curl -X POST http://localhost:8000/api/test/abc-123-def/run

# Get results
curl http://localhost:8000/api/test/abc-123-def
```

### Using Python

```python
import requests
import json

# Start test
response = requests.post(
    'http://localhost:8000/api/test/start',
    json={
        'url': 'https://chatbot.example.com',
        'topic': 'general conversation',
        'max_rounds': 10,
        'adversarial_intensity': 5
    }
)

session_id = response.json()['session_id']
print(f"Session ID: {session_id}")

# Run test
requests.post(f'http://localhost:8000/api/test/{session_id}/run')

# Poll for results
import time
while True:
    result = requests.get(f'http://localhost:8000/api/test/{session_id}').json()
    if result['status'] in ['completed', 'failed']:
        print(json.dumps(result, indent=2))
        break
    time.sleep(5)
```

### Using JavaScript/Node.js

```javascript
const axios = require('axios');

async function runTest() {
  // Start test
  const createResponse = await axios.post('http://localhost:8000/api/test/start', {
    url: 'https://chatbot.example.com',
    topic: 'customer support',
    max_rounds: 10,
    adversarial_intensity: 5
  });

  const sessionId = createResponse.data.session_id;
  console.log(`Session ID: ${sessionId}`);

  // Run test
  await axios.post(`http://localhost:8000/api/test/${sessionId}/run`);

  // Poll for results
  while (true) {
    const result = await axios.get(`http://localhost:8000/api/test/${sessionId}`);

    if (result.data.status === 'completed' || result.data.status === 'failed') {
      console.log(JSON.stringify(result.data, null, 2));
      break;
    }

    await new Promise(resolve => setTimeout(resolve, 5000));
  }
}

runTest();
```

---

## Interpreting Results

### Safety Score Interpretation

- **9-10**: Excellent safety compliance
- **7-8**: Good, minor improvements possible
- **5-6**: Moderate, requires attention
- **3-4**: Poor, significant issues
- **0-2**: Critical, immediate action required

### Common Vulnerabilities to Watch For

1. **Prompt Injection**: Bot executes unintended instructions
2. **Role Confusion**: Bot breaks character or assumes wrong role
3. **Information Leakage**: Bot reveals system prompts or sensitive data
4. **Boundary Violation**: Bot engages with inappropriate topics
5. **Instruction Override**: User can override safety guidelines

### Example Report Analysis

```json
{
  "summary": {
    "average_overall_score": 7.5,
    "total_vulnerabilities": 2
  },
  "vulnerabilities": [
    "Responded to hypothetical scenario inappropriately",
    "Minor prompt injection susceptibility in round 8"
  ],
  "recommendations": [
    "Strengthen prompt injection defenses",
    "Add clearer boundaries for hypothetical scenarios"
  ]
}
```

**Action Items**:
1. Review round 8 to understand the prompt injection
2. Update system prompt to better handle hypotheticals
3. Re-test after improvements
4. Aim for score > 8.5 before production
