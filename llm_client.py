
from openai import OpenAI

client = OpenAI(api_key="")

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
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0.7,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            }
        ] + [
            {
                "role": msg["role"],
                "content": [{"type": "text", "text": msg["content"]}]
            } for msg in history
        ]
    )

    # Handle both new (list-based) and old (string) formats
    content = response.choices[0].message.content
    if isinstance(content, list):
        return content[0]["text"]
    return content  # it's already a plain string

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
