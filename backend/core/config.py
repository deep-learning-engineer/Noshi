import os

from dotenv import load_dotenv
from decimal import Decimal


load_dotenv()


class AppConfig:
    """Configuration of application business logic"""

    # Bank Account
    MAX_ACCOUNTS_PER_USER = int(os.getenv('MAX_ACCOUNTS_PER_USER', 5))

    # Transaction
    CURRENCY_API_URL = os.getenv("CURRENCY_API")

    # Savings Account
    MAX_SAVINGS_ACCOUNTS_PER_USER = int(os.getenv("MAX_SAVINGS_ACCOUNTS_PER_USER"))
    MAXIMUM_ACCRUAL_BALANCE = Decimal(os.getenv("MAXIMUM_ACCRUAL_BALANCE"))
    INTEREST_RATES = {
        'monthly': Decimal(os.getenv("INTEREST_RATES_MONTHLY")),
        'yearly': Decimal(os.getenv("INTEREST_RATES_YEARLY")),
    }
