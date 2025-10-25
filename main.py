import streamlit as st
import os
import json
import time
import requests
from dotenv import load_dotenv

# --- Configuration and Setup ---

# 1. Load Environment Variables
load_dotenv()

# 2. Access the API Key
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GEMINI_API_KEY:
    st.error("Error: API Key not found. Please ensure you have set GOOGLE_API_KEY in your .env file.")
    st.stop()

# Define the Gemini API endpoint and model
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"
HEADERS = {'Content-Type': 'application/json'}

# --- Core Logic for AI Enhancement (Categories and Advanced Search) ---

def get_system_instruction(category):
    """Dynamically sets the AI's persona and goal based on the selected category."""
    if category == "Academic Analysis":
        return (
            "You are a peer-reviewed scholar. Provide a structured, objective, and deeply analytical answer "
            "based on the search results. Use formal language, discuss complexities, and cite all points."
        )
    elif category == "Technical How-To":
        return (
            "You are a senior software engineer. Provide a detailed, step-by-step tutorial or technical explanation "
            "based on the search results. Prioritize clarity, use numbered lists, and include code examples where appropriate."
        )
    else: # General Summary (Default)
        return (
            "You are an expert research assistant. Analyze the search results and provide a detailed, "
            "concise, and well-structured summary of the information relevant to the user's query. Format the output clearly using markdown."
        )

# --- Core Functions (API Call) ---

@st.cache_data(show_spinner=False)
def fetch_grounded_content(user_query, api_key, system_instruction):
    """
    Fetches grounded content (text and sources) from the Gemini API 
    using Google Search as a tool, guided by the custom system instruction.
    """
    
    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "tools": [{"google_search": {} }],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
    }
    
    max_retries = 4
    for attempt in range(max_retries):
        try:
            api_url_with_key = f"{API_URL}?key={api_key}"
            response = requests.post(api_url_with_key, headers=HEADERS, json=payload)
            response.raise_for_status()

            response_data = response.json()
            
            candidate = response_data.get("candidates", [{}])[0]
            if not candidate:
                return "No content generated. The API returned an empty response.", []

            text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "No text found.")
            
            # Extract grounding sources
            sources = []
            grounding_metadata = candidate.get("groundingMetadata", {})
            if grounding_metadata and grounding_metadata.get("groundingAttributions"):
                sources = [
                    {"uri": attr["web"]["uri"], "title": attr["web"]["title"]}
                    for attr in grounding_metadata["groundingAttributions"]
                    if attr.get("web", {}).get("uri")
                ]
            
            return text, sources
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                return f"Failed to fetch content after multiple retries. Network Error: {e}", []
        except Exception as e:
             return f"An unexpected internal error occurred: {e}", []

# --- Streamlit UI Implementation ---

st.set_page_config(page_title="AI Search Portal", layout="wide")

st.markdown("""
    <style>
        /* General Button Styling for aesthetics */
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 24px;
            border-radius: 8px;
            border: none;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
            font-size: 16px;
            transition: all 0.2s;
            width: 100%;
            margin-top: 10px;
        }
        .stButton>button:hover {
            background-color: #45a049;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        }
    </style>
""", unsafe_allow_html=True)


st.title("🧠 AI Grounded Search Portal")
st.markdown("Use the controls below to refine your search and customize the AI's response style.")

# --- Filters / Advanced Search Interface ---
st.subheader("Advanced Search Filters")

# Use columns for layout
col_category, col_clear = st.columns([3, 1])

with col_category:
    search_category = st.selectbox(
        "Select AI Response Style (Category Filter)",
        options=["General Summary", "Academic Analysis", "Technical How-To"],
        index=0,
        help="This changes the AI's persona, influencing the structure and tone of the summary."
    )

with col_clear:
    # A. Add a "Clear Results" Button (UX enhancement)
    if st.button("🔄 Clear Results"):
        if 'summary_text' in st.session_state:
            del st.session_state['summary_text']
            del st.session_state['sources']
            del st.session_state['last_query']
        st.experimental_rerun() # Rerun to instantly clear the UI


# Input and Search Button
query = st.text_input(
    "What question can I research for you?",
    "How is Next.js different from standard React routing?",
    key="search_query"
)

# --- Execution Logic ---
if st.button("Search for Answer"):
    if query:
        # 1. Get the dynamic system instruction based on the user's category choice
        system_instruction = get_system_instruction(search_category)

        # 2. Call the function with the custom instruction
        with st.spinner(f"Searching and synthesizing results for '{query}' using '{search_category}' style..."):
            summary_text, sources = fetch_grounded_content(query, GEMINI_API_KEY, system_instruction)
        
        # 3. Store results in Streamlit session state
        st.session_state['summary_text'] = summary_text
        st.session_state['sources'] = sources
        st.session_state['last_query'] = query
        st.session_state['last_category'] = search_category # Store category too

    else:
        st.warning("Please enter a query to begin the search.")


# --- Display Results from session state ---
if 'summary_text' in st.session_state:
    st.subheader(f"🤖 Summary for: {st.session_state['last_query']} (Style: {st.session_state['last_category']})")
    
    # Display the output from the AI
    st.markdown(st.session_state['summary_text'])

    # Display Sources/Citations
    if st.session_state['sources']:
        st.subheader("📚 Sources Used (Grounding)")
        source_markdown = ""
        for i, source in enumerate(st.session_state['sources']):
            source_markdown += f"- [{source['title']}]({source['uri']})\n"
        st.markdown(source_markdown)
    else:
        if not st.session_state['summary_text'].startswith("Failed to fetch content") and "An unexpected error occurred" not in st.session_state['summary_text']:
            st.info("No explicit grounding sources were returned for this query.")

st.markdown("---")
