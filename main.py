import streamlit as st
from dotenv import load_dotenv
import os
import requests

# Load environment variables
load_dotenv()

# Configure Streamlit UI
st.set_page_config(page_title="AI Assistant", layout="wide")
st.title("🦜 AI Chat Interface")

# Initialize session state
if 'last_response' not in st.session_state:
    st.session_state.last_response = None
if 'raw_response' not in st.session_state:
    st.session_state.raw_response = None

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input(
        "OpenRouter API Key", 
        type="password",
        value=os.getenv("OPENROUTER_API_KEY", "")
    )
    model = st.selectbox(
        "Model",
        [
            "google/gemini-2.5-pro-exp-03-25:free",
            "anthropic/claude-3-haiku",
            "openai/gpt-3.5-turbo",
            "meta-llama/llama-3-70b-instruct",
            "openai/gpt-4o-mini"
        ],
        index=0
    )
    max_tokens = st.slider("Max Tokens", 100, 2000, 500)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7)

# Main chat interface
col1, col2 = st.columns([1, 1])

with col1:
    prompt = st.text_area(
        "Your Prompt:", 
        "What are the 3 most significant AI trends in 2024? Provide concise bullet points.",
        height=200
    )

    if st.button("Generate Response", type="primary"):
        if not api_key:
            st.error("Please enter your API key")
        elif not prompt.strip():
            st.error("Please enter a valid prompt")
        else:
            with st.spinner("Generating response..."):
                try:
                    response = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://localhost"  # Required for some models
                        },
                        json={
                            "model": model,
                            "messages": [
                                {"role": "system", "content": "You are a helpful AI assistant."},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": temperature,
                            "max_tokens": max_tokens
                        },
                        timeout=30  # 30 second timeout
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    # Debug print (remove in production)
                    st.session_state.raw_response = result
                    
                    # Handle response
                    if (result.get('choices') and 
                        len(result['choices']) > 0 and
                        result['choices'][0].get('message') and
                        result['choices'][0]['message'].get('content')):
                        
                        content = result['choices'][0]['message']['content'].strip()
                        if content:
                            st.session_state.last_response = content
                        else:
                            st.error("Received empty response. The model may have refused to answer.")
                            if result['choices'][0]['message'].get('refusal'):
                                st.error(f"Reason: {result['choices'][0]['message']['refusal']}")
                    else:
                        st.error("Unexpected response format from the API")
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"API Error: {str(e)}")
                except Exception as e:
                    st.error(f"Unexpected error: {str(e)}")

with col2:
    st.subheader("AI Response")
    
    # Response box with border
    response_container = st.container(border=True)
    
    if st.session_state.last_response:
        with response_container:
            st.markdown(st.session_state.last_response)
            
        with st.expander("📄 Raw Response & Debug Info"):
            st.json(st.session_state.raw_response)
            
            # Display token usage if available
            if st.session_state.raw_response and 'usage' in st.session_state.raw_response:
                st.metric("Prompt Tokens", st.session_state.raw_response['usage']['prompt_tokens'])
                st.metric("Completion Tokens", st.session_state.raw_response['usage']['completion_tokens'])
    else:
        response_container.info("Your generated response will appear here")
        if st.session_state.raw_response:
            with st.expander("⚠️ View Error Details"):
                st.json(st.session_state.raw_response)