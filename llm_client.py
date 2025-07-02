
import os
import sys

# Try to get API key from environment variable
api_key = os.environ.get("OPENAI_API_KEY", "")

# Check if API key is available
if not api_key:
    # Try to load from .env file if python-dotenv is available
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.environ.get("OPENAI_API_KEY", "")
    except ImportError:
        pass

# Import and configure OpenAI for version 1.0.0+
from openai import OpenAI

# Initialize the client
client = OpenAI(api_key=api_key)

def get_gpt_response(history):
    # Verify API key is set before making the request
    if not client.api_key:
        raise ValueError("OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable.")

    # Format messages for newer OpenAI API version
    messages = [
        {
            "role": "system",
            "content": """You are an AI assistant for a microfinance loan process system for joint liability groups. Follow these EXACT guidelines:

1. LOAN AMOUNTS (ALWAYS USE THESE EXACT FIGURES):
   - New customers: Rs. 30,000 to Rs. 50,000 only
   - Renewal customers: Up to Rs. 70,000 only

2. ONBOARDING PROCESS (ALWAYS INCLUDE THESE STEPS):
   - Video consent
   - OTP verification
   - Voter ID/PAN capture
   - L1, L2, L3 details submission
   - Group Formation
   - Vo group verification
   - Bank Loan Approval
   - Group ESgin
   - Loan disbursement

3. QUERY TYPES TO HANDLE:
   - Loan origination queries
   - Loan renewal queries
   - Information retrieval queries

Keep answers brief, clear, and tailored to microfinance contexts in rural India. Assume users have limited financial literacy. NEVER provide loan amounts different from those specified above."""
        }
    ]
    
    for msg in history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        max_tokens=100, 
        temperature=0.7,
        messages=messages
    )
    
    # Return the content - in the newer OpenAI API version
    return response.choices[0].message.content