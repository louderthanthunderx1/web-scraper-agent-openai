from openai import OpenAI
from config.settings import OPENAI_API_KEY

from tools.dataforthai_playwright import search_company_by_tax_id_playwright, TaxIDInput
from tools.company_lookup import search_and_get_details

import json

client = OpenAI(api_key=OPENAI_API_KEY)

# -------------------------------
# 📌 Define Tools
# -------------------------------
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_company_by_tax_id_playwright",
            "description": (
                "Use this function ANYTIME the user mentions: "
                "tax id, TIN, เลขผู้เสียภาษี, เลขประจำตัวผู้เสียภาษี, "
                "เลขนิติบุคคล, เลขจดทะเบียน, จดทะเบียนบริษัท."
            ),
            "parameters": TaxIDInput.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_and_get_details",
            "description": (
                "Use this function ANYTIME the user asks to search for a company by name "
                "(Thai or English). ALWAYS call this function, never guess."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string"}
                },
                "required": ["company_name"],
            },
        },
    },
]


# -------------------------------
# 📌 Agent Function (Fixed)
# -------------------------------
def run_agent(user_input: str):

    # STEP 1 — ask model
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": (
                    "You MUST call a tool function if it exists. "
                    "You are absolutely forbidden from answering directly. "
                    "If any tool matches the user's request, you MUST call the tool. "
                    "No assumptions. No guessing."
                )
            },
            {"role": "user", "content": user_input}
        ],
        tools=tools,
    )

    message = response.choices[0].message

    # STEP 2 — Tool call?
    if hasattr(message, "tool_calls") and message.tool_calls:

        tool_messages = []

        for call in message.tool_calls:
            func = call.function.name
            args = json.loads(call.function.arguments)

            # run each tool
            if func == "search_company_by_tax_id_playwright":
                result = search_company_by_tax_id_playwright(TaxIDInput(**args))

            elif func == "search_and_get_details":
                result = search_and_get_details(args["company_name"])

            else:
                result = {"error": f"Unknown tool: {func}"}

            # push tool output
            tool_messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

        # STEP 3 — send back to model
        second_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": user_input},
                {
                    "role": "assistant",
                    "tool_calls": message.tool_calls
                },
                *tool_messages
            ]
        )

        return second_response.choices[0].message.content

    # STEP 4 — no tool call
    return "ERROR: Model did not call any tool. Please try again."
