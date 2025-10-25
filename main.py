import argparse
import requests
import json
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

# --- Configuration ---
# Load API Key from .env file (required for local CLI use)
load_dotenv()
API_KEY = os.environ.get("GOOGLE_API_KEY", "")

MODEL_NAME = "gemini-2.5-flash-preview-09-2025"
API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/"
API_URL = f"{API_BASE_URL}{MODEL_NAME}:generateContent?key={API_KEY}"

# --- Utility Functions (Same as in main.py) ---

def clean_and_format_sources(grounding_metadata):
    """
    Extracts and formats source URIs and titles from grounding metadata.
    Returns a string listing the sources.
    """
    sources = []
    if grounding_metadata and grounding_metadata.get('groundingAttributions'):
        for attribution in grounding_metadata['groundingAttributions']:
            web = attribution.get('web')
            if web and web.get('uri') and web.get('title'):
                uri = web['uri']
                title = web['title']
                domain = urlparse(uri).netloc
                sources.append(f"- {title}\n  (Source: {domain})")
    
    if sources:
        return "\n\n--- Sources ---\n" + "\n".join(sources)
    return ""

def generate_content_with_gemini(prompt, system_prompt, temperature, use_grounding):
    """
    Makes the API call to the Gemini model with optional grounding.
    """
    if not API_KEY:
        return "Error: GOOGLE_API_KEY not found. Please set it in your .env file.", {}
        
    headers = {'Content-Type': 'application/json'}
    
    # Build the payload (using defaults from your Streamlit app)
    payload = {
        "contents": [{ "parts": [{ "text": prompt }] }],
        "systemInstruction": {
            "parts": [{ "text": system_prompt }]
        },
        "config": {
            "temperature": temperature
        }
    }

    if use_grounding:
        payload["tools"] = [{"google_search": {}}]

    print(f"-> Sending request to Gemini with grounding: {use_grounding}")
    
    try:
        # Note: Added simple retry logic for robustness (Exponential backoff is a best practice)
        for attempt in range(3):
            response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
            if response.status_code != 429: # Not a rate limit error
                break
            print(f"Rate limit hit (429). Retrying in {2**attempt} seconds...")
            time.sleep(2**attempt)
            
        response.raise_for_status()
        result = response.json()
        
        candidate = result.get('candidates', [{}])[0]
        text = candidate.get('content', {}).get('parts', [{}])[0].get('text', 'No content generated.')
        
        grounding_metadata = candidate.get('groundingMetadata', {})
        
        return text, grounding_metadata

    except requests.exceptions.RequestException as e:
        error_message = f"API Request Error: {e}"
        if response.status_code == 429:
             error_message = "**Fatal Error:** Google API quota exhausted or rate limited too heavily."
        elif response.status_code == 400:
             error_message = f"**Client Error:** Check your API key and input parameters. Response: {response.text}"
        return error_message, {}
    except Exception as e:
        return f"An unexpected error occurred: {e}", {}

# --- Main CLI Execution ---
if __name__ == "__main__":
    import time # Import time here for use in retry logic

    parser = argparse.ArgumentParser(description="Run a grounded search query using the Gemini API.")
    parser.add_argument("query", type=str, help="The search query to send to the AI model.")
    parser.add_argument("--grounding", type=bool, default=True, help="Enable/Disable Google Search grounding (default: True)")
    parser.add_argument("--temp", type=float, default=0.2, help="Set model temperature (0.0 to 1.0, default: 0.2)")
    
    args = parser.parse_args()

    # Use the default system prompt from your Streamlit app
    default_system_prompt = "You are a friendly, factual, and concise research assistant. Summarize findings in bullet points unless otherwise instructed."

    print("--- AI Search Results ---")
    
    response_text, grounding_metadata = generate_content_with_gemini(
        prompt=args.query,
        system_prompt=default_system_prompt,
        temperature=args.temp,
        use_grounding=args.grounding
    )

    print(response_text)
    print(clean_and_format_sources(grounding_metadata))
