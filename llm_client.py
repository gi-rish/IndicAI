
import os
import json
import logging
import traceback
import httpx
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API key from environment variable or use hardcoded key for development
# IMPORTANT: This is a temporary solution for development only
# In production, always use environment variables or secure key management

# Hardcoded development key - replace with your valid OpenAI API key
# NOTE: This is a temporary development key format - replace with your actual key
DEV_API_KEY = "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"

# Get API key from environment variable or use hardcoded key
api_key = os.environ.get('OPENAI_API_KEY', '') or DEV_API_KEY

if not api_key:
    logger.warning("No OpenAI API key found in environment variables or hardcoded")
else:
    # Log the first few characters of the API key for debugging
    key_prefix = api_key[:8] + "..." if api_key else "None"
    logger.info(f"Using API key: {key_prefix}")
    
    # Check if we're using an Azure OpenAI key (starts with sk-proj-)
    is_azure_key = api_key.startswith('sk-proj-')
    logger.info(f"API key format detected: {'Azure OpenAI (sk-proj-)' if is_azure_key else 'Standard OpenAI (sk-)'}")

# System prompts for different stages of the microfinance loan process
SYSTEM_PROMPTS = {
    "default": "You are an AI assistant for a microfinance institution. Help users navigate the joint liability group loan process. Keep your answers brief and to the point.",
    
    "video_consent": "You are guiding a potential borrower through the video consent process for a joint liability group loan. Explain the importance of consent, what information will be collected, and how it will be used. Ensure the borrower understands their rights and the process clearly.",
    
    "otp_verification": "You are assisting with OTP verification for a joint liability group loan application. Guide the borrower through the verification process, explain why it's necessary for security, and help troubleshoot any issues they might encounter.",
    
    "document_capture": "You are helping a borrower capture their ID documents (Voter ID/PAN) for a joint liability group loan. Provide clear instructions on how to properly photograph or scan the documents, what parts need to be visible, and common mistakes to avoid.",
    
    "l1_submission": "You are assisting with the L1 (basic personal information) submission for a joint liability group loan. Guide the borrower through providing their personal details, explain what information is required and why, and help with any questions they might have about this stage.",
    
    "l2_submission": "You are helping with the L2 (financial information) submission for a joint liability group loan. Guide the borrower through providing their financial details, income sources, existing loans, and other relevant financial information required for assessment.",
    
    "l3_submission": "You are assisting with the L3 (group formation and guarantor details) submission for a joint liability group loan. Help the borrower understand the joint liability concept, the responsibilities of group members, and guide them through providing guarantor information.",
    
    "group_formation": "You are explaining the concept of joint liability groups to potential borrowers. Clarify how group formation works, the mutual responsibility aspects, benefits of group lending, and answer any questions about the group dynamics and responsibilities.",
    
    "loan_terms": "You are explaining the terms and conditions of microfinance joint liability group loans. Clearly communicate that loan amounts range from Rs. 30,000 to Rs. 50,000 for new customers and up to Rs. 70,000 for renewal customers. Also explain interest rates, repayment schedules, penalties for late payment, and other important terms borrowers should understand.",
    
    "application_status": "You are helping borrowers check the status of their joint liability group loan application. Guide them through the verification process, explain the current stage of their application, and provide information about next steps or any additional requirements.",
    
    "repayment_guidance": "You are providing guidance on loan repayment for joint liability group members. Explain repayment options, schedules, what happens if a group member cannot pay, and how to maintain good standing with the microfinance institution."
}

def get_gpt_response(history, prompt_type="default", max_tokens=150):
    """
    Get a response from GPT based on conversation history and a specific prompt type
    
    Args:
        history: List of conversation messages
        prompt_type: Type of system prompt to use (from SYSTEM_PROMPTS)
        max_tokens: Maximum number of tokens in the response
        
    Returns:
        GPT's response as a string
    """
    # Use the specified prompt type or fall back to default
    system_prompt = SYSTEM_PROMPTS.get(prompt_type, SYSTEM_PROMPTS["default"])
    
    # Prepare messages in the correct format
    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]
    
    # Add history messages in the correct format
    for msg in history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Skip API calls and use mock responses for development
    logger.info("Using mock responses for development (bypassing OpenAI API)")
    
    # Extract the last user message for context
    last_user_message = ""
    for msg in reversed(history):
        if msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break
    
    logger.info(f"Generating mock response for: {last_user_message}")
    
    # Generate appropriate responses based on prompt type and user message
    if prompt_type == "loan_terms":
        return "For joint liability group loans, we offer Rs. 30,000 to Rs. 50,000 for new customers and up to Rs. 70,000 for renewal customers. The interest rate is 24% per annum on a declining balance with weekly repayments."
    
    if prompt_type == "video_consent":
        return "Please explain to the applicant that we need to record a short video consent. Inform them that this video confirms their identity and willingness to apply for the loan. Assure them that this recording is secure and only used for verification purposes."
    
    if prompt_type == "otp_verification":
        return "Please inform the applicant that we'll send a one-time password (OTP) to their registered mobile number. Ask them to share this OTP with you to verify their phone number. This helps us ensure that we have the correct contact information for important loan updates."
    
    if prompt_type == "document_capture":
        return "Please ask the applicant to provide their ID document (Voter ID/PAN). Ensure the document is original, not damaged, and all text and photo are clearly visible. Take a photo in good lighting without glare or shadows."
    
    # Handle loan amount queries
    if "loan" in last_user_message.lower() and ("amount" in last_user_message.lower() or "kitna" in last_user_message.lower()):
        return "You may be eligible for a loan between Rs. 30,000 to Rs. 50,000 as a new customer, or up to Rs. 70,000 if you're a renewal customer with good repayment history."
    
    # Handle interest rate queries
    elif "interest" in last_user_message.lower() or "byaj" in last_user_message.lower():
        return "The current interest rate for microfinance joint liability group loans is 24% per annum on a declining balance."
    
    # Handle document queries
    elif "document" in last_user_message.lower() or "id" in last_user_message.lower():
        return "You'll need to provide a valid ID proof such as Voter ID or PAN card for the loan application. Please ensure the photograph and all text are clearly visible when uploading."
    
    # Handle group formation queries
    elif "group" in last_user_message.lower() or "joint" in last_user_message.lower():
        return "For a joint liability group loan, you'll need to form a group of 5-10 members. Each member is responsible for their own loan but also acts as a guarantor for other group members."
    
    # Handle application process queries
    elif "process" in last_user_message.lower() or "apply" in last_user_message.lower():
        return "The loan application process includes video consent, OTP verification, document capture, and submission of personal, financial, and group details (L1, L2, and L3 information)."
    
    # Default response
    else:
        return "I'm here to help with your microfinance joint liability group loan inquiry. I can provide information about loan amounts, interest rates, required documents, or the application process. How can I assist you today?"

def process_loan_application(applicant_data, stage):
    """
    Process a loan application at a specific stage and generate appropriate guidance
    
    Args:
        applicant_data: Dictionary containing applicant information
        stage: Current stage in the loan process (video_consent, otp_verification, etc.)
        
    Returns:
        Guidance for the current stage as a string
    """
    # Construct a message based on the stage and applicant data
    if stage == "video_consent":
        message = f"I need to record a video consent for {applicant_data.get('name', 'the applicant')}. What should I explain to them?"
    elif stage == "otp_verification":
        phone = applicant_data.get('phone', "the applicant's phone")
        message = f"We need to verify {phone} with OTP. How should I guide them?"
    elif stage == "document_capture":
        message = f"I need to capture {applicant_data.get('id_type', 'Voter ID/PAN')} for {applicant_data.get('name', 'the applicant')}. What instructions should I give?"
    elif stage == "l1_submission":
        message = f"I'm collecting L1 basic information for {applicant_data.get('name', 'the applicant')}. What details are needed?"
    elif stage == "l2_submission":
        message = f"I'm collecting L2 financial information for {applicant_data.get('name', 'the applicant')}. What should I ask about?"
    elif stage == "l3_submission":
        message = f"I'm collecting L3 group and guarantor details for {applicant_data.get('name', 'the applicant')} group. What information is required?"
    else:
        message = f"I need guidance on the {stage} stage for {applicant_data.get('name', 'the applicant')} joint liability group loan application."
    
    # Create a simple history with just this message
    history = [{"role": "user", "content": message}]
    
    # Get and return the response using the appropriate prompt type
    return get_gpt_response(history, prompt_type=stage)
