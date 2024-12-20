import os

import dotenv
import requests

from src.adapters.notification.interfaces.i_notification_adapter import (
    INotificationAdapter,
)
from src.configs.logger_config import logger

dotenv.load_dotenv()


class TelegramAdapter(INotificationAdapter):
    def __init__(self) -> None:
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def send_message(self, message: str) -> None:
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        data = {"chat_id": self.chat_id, "text": message, "parse_mode": "MarkdownV2"}

        response = requests.post(url, data=data)
        response.raise_for_status()

        logger.info(f"Notification sent: {message}")
