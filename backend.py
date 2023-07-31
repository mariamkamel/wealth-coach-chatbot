# %%writefile backend.py
import os
from typing import Literal

import openai
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

# Load your API key from an environment variable or secret management service
openai.api_key = os.getenv("OPENAI_API_KEY")


class Conversation(BaseModel):
    role: Literal["system", "assistant", "user"]
    content: str


backend_history: list[Conversation] = [
    {
        "role": "system",
        "content": "You'are a friendly and professional personal financial advisor assistant chatbot designed to provide personalized financial advice and wealth management solutions to users based on their specific data such as income, expenses, savings, and financial goals, etc\
               if you need more info from the user you can ask him only one question and waits for the user's response then after his answer you can ask the next one. \
               you MUST consider the following: \
                - you are a professional financial advisor that have a great knowledge, \
                - but also remember you are an assistant you MUST be very friendly \
                - if  you need any user's info you MUST ask only about one INFO  per time and waits for the user's reply before any step further \
                - YOU CAN'T DISPLAY MORE THAN ONE QUESTION PER TIME\
                - use relevant emojis",
    }
]


class ConversationHistory(BaseModel):
    history: list[object]


@app.get("/")
async def health_check():
    return {"status": "OK!"}


@app.post("/chat")
async def llm_response(history: ConversationHistory) -> dict:
    # Step 0: Receive the API payload as a dictionary
    print("history", history)

    history = history.dict()
    # Step 1: Initialize messages with a system prompt and conversation history
    backend_history.append(history["history"][-1])
    print("bakend_history", backend_history)
    messages = backend_history

    # Step 2: Generate a response
    llm_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=messages
    )
    print("llm_response", llm_response.choices[0]["message"])
    backend_history.append(
        {
            "role": llm_response.choices[0]["message"].role,
            "content": llm_response.choices[0]["message"].content,
        }
    )
    print("history", backend_history)

    # Step 3: Return the generated response and the token usage
    return {
        "message": llm_response.choices[0]["message"],
        "token_usage": llm_response["usage"],
    }
