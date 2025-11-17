from openai import OpenAI
from config.settings import OPENAI_API_KEY

# from tools.dataforthai_playwright import search_company_by_tax_id_playwright, TaxIDInput
from tools.dataforthai_crawl import crawl_dft_clean
from tools.company_lookup import search_and_get_details

import json
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

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
            "parameters": {
                "type": "object",
                "properties": {
                    "tax_id": {"type": "string", "description": "Tax ID or company registration number"}
                },
                "required": ["tax_id"],
            },
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
    logger.info("=" * 60)
    logger.info(f"📥 User Input: {user_input}")
    logger.info(f"🔧 Available Tools: {[tool['function']['name'] for tool in tools]}")

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
        logger.info(f"✅ Model selected {len(message.tool_calls)} tool(s)")

        tool_messages = []

        for call in message.tool_calls:
            func = call.function.name
            args = json.loads(call.function.arguments)
            
            # Log tool selection and reasoning
            logger.info("-" * 60)
            logger.info(f"🛠️  Selected Tool: {func}")
            logger.info(f"📋 Arguments: {json.dumps(args, ensure_ascii=False, indent=2)}")
            
            # Get tool description for context
            tool_info = next((t for t in tools if t['function']['name'] == func), None)
            if tool_info:
                logger.info(f"📝 Tool Description: {tool_info['function']['description']}")

            # run each tool
            logger.info(f"⚙️  Executing tool: {func}")
            if func == "search_company_by_tax_id_playwright":
                result = crawl_dft_clean(tax_id=args["tax_id"])

            elif func == "search_and_get_details":
                result = search_and_get_details(args["company_name"])

            else:
                result = {"error": f"Unknown tool: {func}"}
                logger.warning(f"⚠️  Unknown tool: {func}")

            # Log tool result summary
            if isinstance(result, dict):
                if "error" in result:
                    logger.error(f"❌ Tool Error: {result.get('error')}")
                else:
                    logger.info(f"✅ Tool Success: Returned {len(result)} fields")
                    # Log key fields if available
                    if "company_th" in result:
                        logger.info(f"   Company (TH): {result.get('company_th')}")
                    if "company_en" in result:
                        logger.info(f"   Company (EN): {result.get('company_en')}")
                    if "tax_id" in result:
                        logger.info(f"   Tax ID: {result.get('tax_id')}")
            else:
                logger.info(f"✅ Tool Success: Result type = {type(result).__name__}")

            # push tool output
            tool_messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

        # STEP 3 — send back to model
        logger.info("-" * 60)
        logger.info("🔄 Sending tool results back to model for final response...")
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

        final_response = second_response.choices[0].message.content
        logger.info(f"📤 Final Response: {final_response[:100]}..." if len(final_response) > 100 else f"📤 Final Response: {final_response}")
        logger.info("=" * 60)
        return final_response

    # STEP 4 — no tool call
    logger.warning("⚠️  Model did not call any tool!")
    logger.info("=" * 60)
    return "ERROR: Model did not call any tool. Please try again."
