# app.py
import streamlit as st
import requests
import base64 # Needed to embed the logo

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Zolve",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- MODERN UI STYLING (CSS) ---
st.markdown("""
<style>
    /* Main app background */
    .stApp {
        background-color: #121212; /* Dark background */
        color: #e0e0e0; /* Light text */
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1e1e1e; /* Slightly lighter dark for sidebar */
        border-right: 1px solid #2c2c2c;
    }

    /* Main chat container */
    [data-testid="stAppViewContainer"] {
        background-color: #121212;
    }

    /* Chat message styling */
    [data-testid="stChatMessage"] {
        background-color: #2c2c2c; /* Darker chat bubbles */
        border-radius: 18px;
        padding: 1rem 1.25rem;
        border: 1px solid #3a3a3a;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* User message styling */
    [data-testid="stChatMessage"]:has([data-testid="stAvatarIcon-user"]) {
        background-color: #005A9C; /* A distinct blue for user messages */
    }
    
    /* Buttons in sidebar */
    .stButton>button {
        background-color: #333333;
        color: #ffffff;
        border-radius: 8px;
        border: 1px solid #444444;
        transition: background-color 0.3s, border-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #444444;
        border-color: #555555;
    }

    /* Custom Title in Sidebar */
    .sidebar-title {
        display: flex;
        align-items: center;
        gap: 12px;
        padding-bottom: 1rem;
    }
    .sidebar-title .logo {
        width: 40px;
        height: 40px;
    }
    .sidebar-title .title-text {
        font-size: 1.8rem;
        font-weight: 600;
        color: #ffffff;
    }
    .sidebar-subtitle {
        font-size: 0.9rem;
        color: #a0a0a0;
        padding-bottom: 2rem;
    }

    /* Hide the default Streamlit header and footer */
    #MainMenu, footer {
        visibility: hidden;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
      width: 8px;
    }
    ::-webkit-scrollbar-track {
      background: #1e1e1e;
    }
    ::-webkit-scrollbar-thumb {
      background: #4a4a4a;
      border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: #555;
    }

</style>
""", unsafe_allow_html=True)


# --- APPLICATION STATE MANAGEMENT ---
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "api_base_url" not in st.session_state:
    st.session_state.api_base_url = 'http://127.0.0.1:8000'

# --- API COMMUNICATION FUNCTIONS ---
def start_new_chat_session():
    """Starts a new chat session by calling the backend API."""
    try:
        response = requests.post(f"{st.session_state.api_base_url}/chat/new")
        response.raise_for_status()
        data = response.json()
        chat_id = data.get("chat_id")
        if chat_id:
            st.session_state.chats[chat_id] = [{"role": "assistant", "content": "Hello! I'm Zolve, your personal financial guide. How can I help you today?"}]
            st.session_state.current_chat_id = chat_id
        else:
            st.error("Failed to get a valid chat ID from the server.")
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: Could not connect to the backend. Please ensure the server is running. Details: {e}")
        st.stop()

def send_message_to_backend(chat_id, message):
    """Sends a message to the backend and gets the response."""
    try:
        response = requests.post(
            f"{st.session_state.api_base_url}/chat/{chat_id}",
            json={"message": message}
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "Sorry, I didn't get a valid response.")
    except requests.exceptions.RequestException as e:
        return f"Error communicating with the backend: {e}"

# --- SIDEBAR UI ---
with st.sidebar:
    # --- LOGO & TITLE ---
    # Create an SVG for the logo as a placeholder
    logo_svg = """
    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 2L2 7V17L12 22L22 17V7L12 2Z" stroke="#007BFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M2 7L12 12L22 7" stroke="#007BFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M12 22V12" stroke="#007BFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    """
    # NOTE: If you have a logo file (e.g., logo.png), you can load and display it like this:
    # with open("logo.png", "rb") as f:
    #     logo_data = base64.b64encode(f.read()).decode("utf-8")
    #     st.markdown(f'<div class="sidebar-title"><img src="data:image/png;base64,{logo_data}" class="logo"><span class="title-text">Zolve</span></div>', unsafe_allow_html=True)
    
    # Using SVG logo for now
    st.markdown(f'<div class="sidebar-title"><div class="logo">{logo_svg}</div><span class="title-text">Zolve</span></div>', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-subtitle">Your Personal AI Financial Guide</p>', unsafe_allow_html=True)

    # --- NEW CHAT BUTTON ---
    if st.button("➕ New Chat", use_container_width=True):
        start_new_chat_session()
        st.rerun()

    st.markdown("---")

    # --- CHAT HISTORY ---
    st.markdown("### Chat History")
    chat_ids = list(st.session_state.chats.keys())
    for chat_id in reversed(chat_ids):
        chat = st.session_state.chats[chat_id]
        first_user_message = next((msg["content"] for msg in chat if msg["role"] == "user"), "New Chat")
        
        # Truncate long chat names
        display_name = (first_user_message[:30] + '...') if len(first_user_message) > 30 else first_user_message

        if st.button(display_name, key=f"history_{chat_id}", use_container_width=True):
            st.session_state.current_chat_id = chat_id
            st.rerun()

# --- MAIN CHAT INTERFACE ---
# Start a new chat on the first run if none exists
if not st.session_state.current_chat_id:
    start_new_chat_session()

# Display messages for the current chat
if st.session_state.current_chat_id:
    current_chat_messages = st.session_state.chats.get(st.session_state.current_chat_id, [])
    for msg in current_chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Get user input
if prompt := st.chat_input("Ask Zolve a financial question..."):
    # Add and display user message
    st.session_state.chats[st.session_state.current_chat_id].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Zolve is thinking..."):
            response_text = send_message_to_backend(st.session_state.current_chat_id, prompt)
            st.markdown(response_text)
            # Add assistant response to chat history
            st.session_state.chats[st.session_state.current_chat_id].append({"role": "assistant", "content": response_text})