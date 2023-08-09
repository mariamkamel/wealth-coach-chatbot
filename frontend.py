# %%writefile frontend.py
import requests
import streamlit as st
import utils
import os
from dotenv import load_dotenv

load_dotenv()

# Replace with the URL of your backend
app_url = os.getenv("APP_URL")


@st.spinner("🤔 Thinking...")
def openai_llm_response(user_input):
    """Send the user input to the LLM API and return the response."""
    # Send the entire conversation history to the backend
    payload = {"history": user_input}
    response = requests.post(app_url, json=payload).json()

    # Generate the unit api call cost and add it to the response
    api_call_cost = utils.calc_cost(response["token_usage"])
    api_call_response = response["message"]
    api_call_response["api_call_cost"] = api_call_cost

    # Add everything to the session state
    st.session_state.conversation_history.append(api_call_response)
    st.session_state.total_cost += api_call_cost


def send_users_data(tool_name, uploaded_file):
    send_users_data_url = "http://localhost:8000/user_data"
    response = requests.post(
        send_users_data_url,
        files={"file": uploaded_file},
        data={"tool_name": tool_name},
    ).json()


def chatbot():
    st.empty()
    st.title("🦸 Wealth Coach ChatBot")
    st.markdown("I'm here to give you a customized financial assistance")

    col1, col2 = st.columns(2)
    with col1:
        utils.clear_conversation()

    # Get user input
    if user_input := st.chat_input(
        "Ask me any finance related question or advice!", max_chars=400
    ):
        # Append user question to the conversation history
        st.session_state.conversation_history.append(
            {"role": "user", "content": user_input}
        )
        openai_llm_response(user_input)

    # Display the total cost
    st.caption(f"Total cost of this session: US${st.session_state.total_cost:.5f}")

    # Display the entire conversation on the frontend
    utils.display_conversation(st.session_state.conversation_history)

    # Download conversation code runs last to ensure the latest messages are captured
    with col2:
        utils.download_conversation()


def main():
    st.sidebar.title("Navigation")
    pages = ["Home", "Chatbot"]
    choice = st.sidebar.selectbox("Go to", pages)

    if choice == "Home":
        st.subheader(
            "Before starting, are you using one of these management apps that you wish importing your personal data from?"
        )
        selectedApp = st.selectbox("Available apps:", ["YNAB"])
        uploaded_file = st.file_uploader(
            "Upload your " + selectedApp + " csv file here...", type=["csv"]
        )
        skip = st.button("Skip")
        if skip:
            choice = "Chatbot"
        if uploaded_file is not None:
            print(uploaded_file)

            send_users_data("ynab", uploaded_file)
    elif choice == "Chatbot":
        chatbot()


if __name__ == "__main__":
    main()
