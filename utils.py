# %%writefile utils.py
from datetime import datetime
import requests

import pandas as pd
import streamlit as st

user_avatar = "😃"
assistant_avatar = "🤑"

clear_url = "http://127.0.0.1:8000/clear"


def clear():
    print(st.session_state.user_id)
    payload = {"id": st.session_state.user_id}

    response = requests.post(clear_url, json=payload)


def display_conversation(conversation_history):
    """Display the conversation history"""

    # Loop over all messages in the conversation
    for message in conversation_history:
        # Change avatar based on the role
        avatar = user_avatar if message["role"] == "user" else assistant_avatar

        # Display the message content
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

            if "api_call_cost" in message:
                st.caption(f"Cost: US${message['api_call_cost']:.5f}")


def clear_conversation():
    """Start New Conversation"""
    if (
        st.button(
            "🧹 Start New Conversation", use_container_width=True, key="start_new_conv"
        )
        or "conversation_history" not in st.session_state
    ):
        st.session_state.conversation_history = []
        st.session_state.total_cost = 0
        clear()


def download_conversation():
    """Download the conversation history as a CSV file."""
    conversation_df = pd.DataFrame(
        st.session_state.conversation_history, columns=["role", "content"]
    )
    csv = conversation_df.to_csv(index=False)

    st.download_button(
        label="💾 Download conversation",
        data=csv,
        file_name=f"conversation_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True,
        key="download",
    )


def calc_cost(token_usage):
    # https://openai.com/pricing

    return (token_usage["prompt_tokens"] * 0.0015 / 1000) + (
        token_usage["completion_tokens"] * 0.002 / 1000
    )
