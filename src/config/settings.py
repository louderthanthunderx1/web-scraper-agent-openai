import os
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# print(OPENAI_API_KEY)

DATAFORTHAI_REQUIRES_LOGIN = os.getenv("DATAFORTHAI_REQUIRES_LOGIN", "false").lower() == "true"