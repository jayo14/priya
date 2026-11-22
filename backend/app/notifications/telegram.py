"""Telegram Bot API integration for real-time promotion deal alerting."""

from typing import Optional

import httpx

from app.core.config import settings
from app.core.logging import setup_logging

logger = setup_logging()


class TelegramNotifier:
    """Delivers subscription promotion alerts to Telegram chats via Telegram Bot API."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        default_chat_id: Optional[str] = None,
        timeout: float = 5.0,
    ):
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.default_chat_id = default_chat_id or settings.TELEGRAM_CHAT_ID
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        """Check if both bot token and chat ID are present."""
        return bool(self.bot_token and self.default_chat_id)

    def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: str = "HTML",
    ) -> tuple[bool, Optional[str]]:
        """Send a message to a Telegram chat.

        Returns (success: bool, error_detail: Optional[str]).
        """
        target_chat = chat_id or self.default_chat_id

        if not self.bot_token or not target_chat:
            logger.info(
                f"[SIMULATED TELEGRAM ALERT] Bot not configured. Message preview:\n{text[:200]}..."
            )
            return True, "Simulated delivery: Telegram bot token or chat ID not set in environment."

        api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": target_chat,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(api_url, json=payload)

                if resp.status_code == 200:
                    logger.info(f"Telegram notification delivered to chat {target_chat}")
                    return True, None
                elif resp.status_code == 400 and parse_mode == "HTML":
                    # Fallback to plain text if HTML tags were rejected
                    logger.warning("Telegram rejected HTML formatting, falling back to plain text")
                    payload["parse_mode"] = None
                    plain_resp = client.post(api_url, json=payload)
                    if plain_resp.status_code == 200:
                        return True, None
                    return False, f"Telegram API error {plain_resp.status_code}: {plain_resp.text}"
                else:
                    err_msg = f"Telegram API error {resp.status_code}: {resp.text}"
                    logger.warning(err_msg)
                    return False, err_msg

        except httpx.RequestError as exc:
            err_msg = f"Network failure communicating with Telegram API: {exc}"
            logger.warning(err_msg)
            return False, err_msg
        except Exception as exc:
            err_msg = f"Unexpected error dispatching Telegram alert: {exc}"
            logger.error(err_msg, exc_info=True)
            return False, err_msg
