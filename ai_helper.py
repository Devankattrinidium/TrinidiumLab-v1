import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
QWEN_API_KEY = os.getenv("QWEN_API_KEY")

def generate_email_subject_and_body(name, context):
    PROMPT = f"""
You are a world-class cold email copywriter trained by Alex Hormozi, Iman Gadzhi, Daniel Fazio, and Luke Alexander.

Your task: Write a high-converting cold email in HTML format for a B2B service targeting dentists in Australia.

Offer:
- AI-Powered Lead Generation + Automated Appointment Booking
- Unique edge: We don’t just send leads. Our AI books real appointments straight into their calendar.

Use this **core lesson**:
> "If I gave you a bag for $1000, most would walk away. The smart ones ask — what's inside? Rich don’t ask what they’re losing. They ask what they’re gaining."

## Email Requirements:
- Personalize for: {name}
- Email tone: Polarizing, confident, bold, yet friendly
- Put VALUE in the first 2 lines (ex: "We help clinics get 10–20 bookings/month using AI")
- Use punchy, curious subject lines
- Length: Max 8-9 sentences
- Output format: JSON with HTML body and subject
- Don't include price in email unless its example like that bag.
- Use Dr. when addressing dentists but when addressing CLINICS dont use Dr.(eg: "Place" "City" "Dentistry" etc).
- You can use <strong> for words that need to be BOLD.
- Make sure to use <p>, <br>, etc. tags

## Style Example (Use Similar Tone and Flow):

SUBJECT: {name}, thoughts? or {name}, thoughts on automation? or {name}, curious about AI?

<p>Hey Dr. {name},</p>

<p>We help clinics get consistent bookings/month using AI — no more chase, no more missed appointments.</p>

<p>If I offered you a way to double your bookings without lifting a finger, would you ask what it costs? Or would you ask what it gains you?</p>

<p>Most clinics ask, “How much does it cost?”
Growth clinics ask, “How much does it make me?”</p>

<p>If your calendar booked 10 new patients next month — automatically — would that be worth 20 minutes of your time?</p>
<p>Let’s talk for 20 mins and I’ll show you how your clinic can stop chasing patients and start attracting them.</p>

- Devank Founder at <strong>Trinidium</strong>

Now, write a custom version for: {name}
Context: {context}

IMPORTANT: ONLY return a valid JSON object with "subject" and "body" keys. Do NOT include any other text, markdown, or explanation. The JSON must be the only output.

Return JSON like this:
{{"subject": "...", "body": "..."}}.
"""

    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "qwen/qwen3-14b",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": PROMPT}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

    if response.status_code != 200:
        raise Exception(f"API request failed: {response.text}")

    try:
        content = response.json()
    except Exception as e:
        raise Exception(f"Failed to parse API response as JSON: {response.text}") from e

    if "choices" not in content or not content["choices"]:
        raise Exception(f"Unexpected API response format: {content}")

    message_content = content["choices"][0]["message"]["content"]
    if not message_content:
        raise Exception(f"API returned empty message content: {content}")

    # Debug: print the raw message content for troubleshooting
    print("AI raw response:", message_content)

    # Try to extract JSON from the response, even if extra text is present
    try:
        start = message_content.find('{')
        end = message_content.rfind('}')
        if start != -1 and end != -1:
            json_str = message_content[start:end+1]
            return json.loads(json_str)
        else:
            raise Exception("No JSON object found in AI response.")
    except json.JSONDecodeError as e:
        raise Exception(f"Invalid JSON in API response: {message_content}") from e