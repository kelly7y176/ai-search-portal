# 🔍 AI Grounded Search Portal
This project is a Streamlit application that provides a powerful, grounded search experience using the Gemini API and Google Search grounding to retrieve real-time, up-to-date information.
The repository includes both a public web application and a command-line interface (CLI) tool for direct querying.

# 🚀 Live Web Application
You can access and interact with the live application deployed on Streamlit Community Cloud here:
 [➡️ Launch AI Search Portal](https://ai-search-app-7hq63kmdyykhoam9eetjox.streamlit.app/)


# 💻 Running the Project Locally
### Prerequisites
1. Python 3.8+
2. A Google Gemini API Key: Obtain one from Google AI Studio.

### Setup
1. Clone the repository:
```
git clone https://github.com/kelly7y176/ai-search-portal.git
cd ai-search-portal
```


2. Set up the Virtual Environment:
```
python3 -m venv venv
source venv/bin/activate
```

3. Install Dependencies:
```
pip install -r requirements.txt
```

4. Set up your API Key:
Create a file named .env in the root directory (ai-search-portal/) and add your Google Gemini API key:
```
 .env file content
GOOGLE_API_KEY="YOUR_GEMINI_API_KEY_HERE"
```

(Note: This file is ignored by Git via the .gitignore file for security.)


### How to Use the Streamlit Web App (main.py)
Run this command to launch the interactive web interface:
```
streamlit run main.py
```

The application will open in your default web browser, complete with a session-based rate limiter to help manage API usage when deployed publicly.
