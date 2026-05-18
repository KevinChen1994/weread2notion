import os

from dotenv import load_dotenv

load_dotenv()

WEREAD_API_KEY = os.environ.get("WEREAD_API_KEY", "")
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "")

WEREAD_API_URL = "https://i.weread.qq.com/api/agent/gateway"
SKILL_VERSION = "1.0.3"
