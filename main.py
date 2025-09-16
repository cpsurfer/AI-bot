import streamlit as st
import os
import json
import requests
import re
from pypdf import PdfReader
from dotenv import load_dotenv
import streamlit as st

api_key = st.secrets["api"]["GEMINI_API_KEY"]

# Try to import the Google Generative AI library
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    genai = None
    HAS_GEMINI = False

# Load environment variables from a .env file
load_dotenv()

# --- Configuration and Helper Functions ---

st.set_page_config(page_title="AI Chat", layout="centered")

def safe_get_secret(key, default=None):
    """Safely retrieves a secret from Streamlit secrets or environment variables."""
    try:
        # Check for the nested key structure first, then fall back to the top-level key
        api_key_from_secrets = st.secrets.get("api", {}).get(key, None)
        if api_key_from_secrets:
            return api_key_from_secrets
        
        # Fallback to environment variables if the key is not in secrets.toml
        return os.getenv(key, default)
    except Exception:
        # Fallback to environment variables if st.secrets is not available
        return os.getenv(key, default)


# --- Suggestion generator helpers ---
_STOPWORDS = {
    "the","and","for","with","that","this","from","about","have",
    "your","you","are","was","but","not","can","will","they","their",
}

def _extract_keywords(text, top_n=3):
    """Naive keyword extractor: pick the most frequent long words not in stopwords."""
    if not text:
        return []
    words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", text)]
    freq = {}
    for w in words:
        if w in _STOPWORDS:
            continue
        freq[w] = freq.get(w, 0) + 1
    items = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    return [w for w,_ in items[:top_n]]

def generate_suggestions(user_message, response_text, owner=None, max_suggestions=3):
    """Return a short list of suggested follow-up questions.

    Strategy:
    - Extract keywords from the user's message first; fall back to response_text.
    - Create simple question templates using those keywords.
    """
    kws = _extract_keywords(user_message, top_n=max_suggestions)
    if not kws:
        kws = _extract_keywords(response_text, top_n=max_suggestions)

    suggestions = []
    for k in kws:
        suggestions.append(f"Can you tell me more about {k}?")
        if len(suggestions) >= max_suggestions:
            break

    # Add some safe generic prompts if not enough
    generic = [
        "How did you achieve that?",
        "What tools or technologies were used?",
        "Can you share a brief example or outcome?",
    ]
    i = 0
    while len(suggestions) < max_suggestions and i < len(generic):
        suggestions.append(generic[i])
        i += 1

    return suggestions

# --- Pushover Notifications for Tool Calls ---

PUSHOVER_TOKEN = safe_get_secret("PUSHOVER_TOKEN")
PUSHOVER_USER = safe_get_secret("PUSHOVER_USER")

def push(message, title="AI Bot Notification"):
    """Sends a push notification via Pushover if credentials are available."""
    if PUSHOVER_TOKEN and PUSHOVER_USER:
        try:
            requests.post(
                "https://api.pushover.net/1/messages.json",
                data={
                    "token": PUSHOVER_TOKEN,
                    "user": PUSHOVER_USER,
                    "title": title,
                    "message": message,
                },
                timeout=5 # Add a timeout for safety
            )
        except requests.RequestException as e:
            print(f"Pushover notification failed: {e}")


# --- Tool Definitions (Functions the AI can call) ---

def record_user_details(email, name="Name not provided", notes="Not provided"):
    """Records user details and sends a notification."""
    message = f"Name: {name}\nEmail: {email}\nNotes: {notes}"
    push(message, title="New Contact Recorded")
    return {"status": "success", "message": f"Details for {name} recorded."}

def record_unknown_question(question):
    """Records a question the AI could not answer."""
    message = f"Question: {question}"
    push(message, title="Unanswered Question Logged")
    return {"status": "success", "message": "Question has been recorded for review."}


# --- Main Chatbot Class ---

class Me:
    def __init__(self):
        """Initializes the chatbot, configures the AI model, and loads data."""
        self.name = "Rahul Sahu"
        gemini_key = safe_get_secret("GEMINI_API_KEY")

        if not HAS_GEMINI or not gemini_key:
            self.model = None
            st.error("Gemini AI library not found or API key is missing. Please install `google-generativeai` and set your `GEMINI_API_KEY`.")
            return

        # Configure the Gemini client
        genai.configure(api_key=gemini_key)

        # --- FIX: Load personal data BEFORE initializing the model ---
        # Load personal data from local files first, so it's available for the system prompt.
        self.linkedin = self._read_pdf("me/linkedin.pdf")
        self.cv = self._read_pdf("me/cv.pdf")
        self.summary = self._read_file("me/summary.txt")

        # Define the tools (functions) the model can use
        self.tools = {
            "record_user_details": record_user_details,
            "record_unknown_question": record_unknown_question,
        }

        # Initialize the Generative Model with system instructions and tools
        # Now, _get_system_prompt() can safely access self.summary, etc.
        self.model = genai.GenerativeModel(
            model_name='gemini-1.5-flash-latest', # Using a modern, capable model
            system_instruction=self._get_system_prompt(),
            tools=self.tools.values()
        )

    def _read_pdf(self, path):
        """Extracts text from a PDF file."""
        try:
            reader = PdfReader(path)
            return "\n".join(p.extract_text() or "" for p in reader.pages)
        except FileNotFoundError:
            st.warning(f"Warning: PDF file not found at '{path}'.")
            return "Not available."
        except Exception as e:
            st.error(f"Error reading PDF {path}: {e}")
            return "Error reading file."

    def _read_file(self, path):
        """Reads text from a plain text file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            st.warning(f"Warning: Text file not found at '{path}'.")
            return "Not available."
        except Exception as e:
            st.error(f"Error reading file {path}: {e}")
            return "Error reading file."

    def _get_system_prompt(self):
        """Creates the system prompt with loaded personal data."""
        # This prompt is passed during model initialization
        return (
            f"You are a helpful AI assistant representing {self.name}. Your goal is to answer questions about him professionally and accurately. "
            f"Use the provided summary, CV, and LinkedIn information to respond to users.\n\n"
            f"## Summary:\n{self.summary}\n\n"
            f"## LinkedIn Profile:\n{self.linkedin}\n\n"
            f"## CV / Resume:\n{self.cv}\n\n"
            "Your instructions are:\n"
            "1. Be friendly, professional, and concise.\n"
            "2. If you are unsure of an answer or the information is not in your context, you MUST use the `record_unknown_question` tool to log the question.\n"
            "3. Actively encourage users who seem interested in hiring or connecting to provide their name and email. Use the `record_user_details` tool to save their information.\n"
            "4. Do not make up information. Stick strictly to the provided context."
        )

    def chat(self, user_message, chat_history):
        """Handles the main chat logic, including tool calls."""
        if not self.model:
            return "The AI model is not configured. Please check your API key."

        # Start a chat session with the existing history
        chat_session = self.model.start_chat(history=chat_history)

        try:
            # Send the user's message to the model
            response = chat_session.send_message(user_message)

            # --- Handle Function Calling in a loop ---
            # The model might respond with a function call instead of text.
            # We need to detect this, execute the function, and send the result back.
            # This loop handles sequential and parallel tool calls.
            while response.parts and any(part.function_call for part in response.parts):
                # The Gemini API can return multiple parallel tool calls
                function_calls = [part.function_call for part in response.parts if part.function_call]

                # Prepare the responses to send back to the model
                function_responses = []

                for fc in function_calls:
                    function_name = fc.name
                    args = dict(fc.args)

                    # Find and execute the corresponding Python function
                    tool_function = self.tools.get(function_name)
                    if not tool_function:
                        # It's better to let the model know it called a non-existent function
                        # than to just error out in the app.
                        result = {"status": "error", "message": f"Unknown function: {function_name}"}
                    else:
                        try:
                            # Call the function with the arguments provided by the model
                            result = tool_function(**args)
                        except Exception as e:
                            # Capture errors from the tool execution
                            result = {"status": "error", "message": f"Error in {function_name}: {str(e)}"}

                    # Append the result to send back
                    function_responses.append(
                        genai.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=function_name,
                                response={"result": json.dumps(result)}
                            )
                        )
                    )

                # Send the function call results back to the model.
                response = chat_session.send_message(function_responses)

            # The final response should now be a text part
            return response.text

        except Exception as e:
            st.error(f"An error occurred while communicating with the Gemini API: {e}")
            return "Sorry, I encountered an error. Please try again."


# --- Streamlit UI ---

st.title("🤖 Chat with AI")

# Initialize the chatbot class
# Using st.cache_resource to prevent re-initializing on every interaction
@st.cache_resource
def init_chatbot():
    return Me()

me = init_chatbot()

# Initialize chat history in session state if it doesn't exist
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display previous messages
for msg in st.session_state.chat_history:
    # We only display 'user' and 'model' (AI) roles.
    # The Gemini API uses 'model' for the AI's role, but Streamlit's
    # st.chat_message uses 'assistant' for the AI's role.
    if msg['role'] in ['user', 'model']:
        role = "assistant" if msg['role'] == "model" else msg['role']
        st.chat_message(role).write(msg['parts'][0])

# Get user input
user_input = st.chat_input("Ask about my experience, skills, or projects...")

if user_input:
    # Display user message
    st.chat_message("user").write(user_input)

    # Add user message to history
    st.session_state.chat_history.append({"role": "user", "parts": [user_input]})

    # Get bot's response
    # We pass a copy of the history to the chat method
    response_text = me.chat(user_input, st.session_state.chat_history)

    # Display bot's response
    st.chat_message("assistant").write(response_text)

    # Add bot's response to history
    st.session_state.chat_history.append({"role": "model", "parts": [response_text]})
