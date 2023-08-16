import os
import uvicorn
import openai
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

openai.api_key = os.getenv("OPENAI_API_KEY")


initialConv = {
    "role": "system",
    "content": "You'are a friendly and professional personal financial advisor assistant chatbot designed to provide personalized financial advice and wealth management solutions to users based on their specific data such as income, expenses, savings, and financial goals, etc\
               if you need more info from the user you can ask him only one question and waits for the user's response then after his answer you can ask the next one. \
               you MUST consider the following: \
                - you are a professional financial advisor that have a great knowledge, \
                - you MUST always return with an answer for analysis and calculations YOU CAN'T reply with a waiting message like  'I'll calculate that please wait' or 'give me a moment'\
                - but also remember you are an assistant you MUST be very friendly \
                - if  you need any user's info you MUST ask only about one INFO  per time and waits for the user's reply before any step further \
                - YOU CAN'T DISPLAY MORE THAN ONE QUESTION PER TIME\
                - use relevant emojis\
                - You must only display just ONE question about ONE info per reply",
}
backend_history = [{"id": 0, "conv": [initialConv]}]


def find_user_data(id):
    new_item = None
    for item in backend_history:
        if item["id"] == id:
            new_item = item
            break
    if new_item is None:
        new_item = {"id": id, "conv": [initialConv]}
        backend_history.append(new_item)
    return new_item


def remove_item_by_id(id_to_remove):
    data = [item for item in backend_history if item["id"] != id_to_remove]
    print("Data", data)
    return data


@app.post("/user_data")
async def user_data(
    file: UploadFile = File(...), tool_name: str = Form(...), id: int = Form(...)
):
    try:
        print(tool_name, id)
        ext = os.path.splitext(file.filename)[-1]
        if ext.lower() != ".csv":
            raise HTTPException(status_code=422, detail="Uploaded file is not a CSV.")

        # Read the uploaded CSV file into a DataFrame
        df = pd.read_csv(file.file)

        # validate csv columns against tools columns
        columns = df.columns.tolist()
        ynab_columns = list(
            [
                "Account",
                "Flag",
                "Date",
                "Payee",
                "Category Group/Category",
                "Category Group",
                "Category",
                "Memo",
                "Outflow",
                "Inflow",
                "Cleared",
            ]
        )
        if columns != ynab_columns:
            print("invalid data")
            return 400
        user = find_user_data(id)
        user["conv"].append(
            {
                "role": "user",
                "content": f"please consider the following user's data extracted from the user's ynab account budget the following array \
                                contains the budget each transaction contains the following fields: {ynab_columns} \
                                 {df.values.tolist()}",
            }
        )
        print(backend_history)
        return 200
    except Exception as e:
        # If an error occurs during processing, you can raise an HTTPException with an appropriate status code
        raise HTTPException(
            status_code=500, detail="An error occurred during data processing."
        )


@app.post("/chat")
async def llm_response(request: Request) -> dict:
    data = await request.json()
    if data["id"] is None:
        return {"status": 404, "message": "can't find user, please provide id"}
    user = find_user_data(data["id"])
    user["conv"].append({"role": "user", "content": data["history"]})

    messages = user["conv"]

    llm_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=messages
    )
    print("llm_response", llm_response.choices[0]["message"])
    user["conv"].append(
        {
            "role": llm_response.choices[0]["message"].role,
            "content": llm_response.choices[0]["message"].content,
        }
    )
    print("history id: ", user["id"], " conversation: ", user["conv"])

    #  Return the generated response and the token usage
    return {
        "message": llm_response.choices[0]["message"],
        "token_usage": llm_response["usage"],
        "id": user["id"],
    }


@app.post("/clear")
async def clear(request: Request):
    data = await request.json()
    global backend_history

    backend_history = remove_item_by_id(data["id"])
    return 200


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
