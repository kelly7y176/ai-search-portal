import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
# The API key must be set either in a local .env file or in Streamlit Secrets
API_KEY = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

if not API_KEY:
    st.error("🚨 Configuration Error: GOOGLE_API_KEY not found. Please set it in your local .env file or Streamlit Secrets.")
    st.stop()

# Google GenAI API endpoint details
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

# --- Rate Limiting Setup ---
MAX_CALLS_PER_SESSION = 5
CALL_COUNT_KEY = 'api_call_count'

# Initialize session state for the call count
if CALL_COUNT_KEY not in st.session_state:
    st.session_state[CALL_COUNT_KEY] = 0

# --- Helper Functions ---

def generate_grounded_content(query, system_prompt):
    """
    Calls the Gemini API with Google Search grounding enabled.
    """
    payload = {
        "contents": [{"parts": [{"text": query}]}],
        "tools": [{"google_search": {}}],  # Enable Google Search grounding
        "systemInstruction": {"parts": [{"text": system_prompt}]},
    }

    # Exponential backoff for API calls
    for attempt in range(5):
        try:
            response = requests.post(
                API_URL,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=30  # Increased timeout for complex searches
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            if attempt < 4:
                # Wait longer on each subsequent failed attempt
                import time
                time.sleep(2 ** attempt)
            else:
                st.exception(f"API Request Failed after multiple retries: {e}")
                return None
    return None

def extract_and_format_response(result):
    """
    Extracts the text and source citations from the Gemini API response.
    """
    if not result or 'candidates' not in result or not result['candidates']:
        return "⚠️ Received an empty or invalid response from the API.", []

    candidate = result['candidates'][0]
    generated_text = candidate.get('content', {}).get('parts', [{}])[0].get('text', 'No text generated.')
    sources = []

    # Extract grounding sources
    grounding_metadata = candidate.get('groundingMetadata', {})
    if grounding_metadata and grounding_metadata.get('groundingAttributions'):
        for attribution in grounding_metadata['groundingAttributions']:
            web_info = attribution.get('web')
            if web_info and web_info.get('uri') and web_info.get('title'):
                sources.append({
                    'title': web_info['title'],
                    'uri': web_info['uri']
                })
    
    return generated_text, sources

# --- Streamlit UI and Logic ---

st.set_page_config(
    page_title="AI Grounded Search Portal",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌐 AI Grounded Search Portal")
st.markdown("Ask any question to get an up-to-date answer backed by Google Search results.")

# Sidebar for controls and status
with st.sidebar:
    st.header("App Status")
    
    # Display rate limit status
    remaining_calls = MAX_CALLS_PER_SESSION - st.session_state[CALL_COUNT_KEY]
    
    if remaining_calls > 0:
        st.success(f"Searches Remaining: {remaining_calls} / {MAX_CALLS_PER_SESSION}")
    else:
        st.error(f"Daily Limit Reached: {MAX_CALLS_PER_SESSION} / {MAX_CALLS_PER_SESSION}")
        st.info("Please refresh the app to start a new session.")

    st.markdown("---")
    st.caption("Powered by Google Gemini API.")
    st.caption("The code uses Streamlit Secrets to securely hide your API key.")


# System prompt to guide the model's behavior
system_prompt = (
    "You are an expert research assistant. Your task is to provide accurate, "
    "concise, and well-structured answers to user queries, primarily using the "
    "information provided by the Google Search grounding tool. Always prioritize "
    "information found through search over internal knowledge. State your answer clearly, "
    "and do not repeat the question."
)

# Main input form
with st.form("search_form"):
    user_query = st.text_area("Enter your search query:", placeholder="e.g., What are the latest developments in fusion energy as of today?", height=100)
    submitted = st.form_submit_button("Search for Grounded Answer")

if submitted and user_query:
    if st.session_state[CALL_COUNT_KEY] >= MAX_CALLS_PER_SESSION:
        st.warning("⚠️ **Rate Limit Exceeded:** You have reached the maximum number of searches for this session. Please refresh the page to try again.")
    else:
        # Increment call count immediately
        st.session_state[CALL_COUNT_KEY] += 1
        
        # Display the updated status in the sidebar
        st.rerun() 
        
        st.subheader("Results")
        with st.spinner("Searching the web and generating content..."):
            
            # Make the API call
            api_result = generate_grounded_content(user_query, system_prompt)
            
            if api_result:
                # Extract and format the response
                generated_text, sources = extract_and_format_response(api_result)

                # Display the main answer
                st.markdown("### 💡 AI Generated Answer")
                st.info(generated_text)

                # Display sources if available
                if sources:
                    st.markdown("### 📚 Grounding Sources")
                    for i, source in enumerate(sources):
                        st.markdown(f"**{i+1}.** [{source['title']}]({source['uri']})")
                else:
                    st.warning("No specific grounding sources were found for this query.")
            
            else:
                st.error("Failed to get a response from the Gemini API.")
