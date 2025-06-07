import os
from dotenv import load_dotenv


load_dotenv()


class AppConfig:
    """Configuration of application business logic"""

    MAX_ACCOUNTS_PER_USER = int(os.getenv('MAX_ACCOUNTS_PER_USER', 5))
    CURRENCY_API_URL = os.getenv("CURRENCY_API")
