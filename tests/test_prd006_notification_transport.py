"""
PRD-006 transport lock tests.

Verifies:
  1. send_notification dispatches via Telegram only — no ntfy calls
  2. send_notification is the sole dispatch path (no parallel transports)
  3. A sample alert flows through send_notification → send_telegram exactly once
"""

from unittest.mock import MagicMock, patch

from cuttingboard import config
from cuttingboard.output import send_notification, send_telegram


# ---------------------------------------------------------------------------
# 1. No ntfy dispatch
# ---------------------------------------------------------------------------

class TestNoNtfyDispatch:
    def test_send_notification_does_not_reference_ntfy_topic(self):
        """send_notification must not read config.NTFY_TOPIC (attribute removed)."""
        assert not hasattr(config, "NTFY_TOPIC"), (
            "config.NTFY_TOPIC still exists — ntfy not fully removed from config"
        )

    def test_send_notification_does_not_reference_ntfy_url(self):
        """send_notification must not read config.NTFY_URL (attribute removed)."""
        assert not hasattr(config, "NTFY_URL"), (
            "config.NTFY_URL still exists — ntfy not fully removed from config"
        )

    def test_send_notification_skips_when_telegram_unconfigured(self):
        with patch.object(config, "TELEGRAM_BOT_TOKEN", None):
            with patch.object(config, "TELEGRAM_CHAT_ID", None):
                result = send_notification("title", "body")
        assert result is False

    def test_send_notification_does_not_post_to_ntfy_domain(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch.object(config, "TELEGRAM_BOT_TOKEN", "bot-token"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "12345"):
                with patch("requests.post", return_value=mock_resp) as mock_post:
                    send_notification("title", "body")
        url_called = mock_post.call_args[0][0]
        assert "ntfy" not in url_called.lower()
        assert "ntfy.sh" not in url_called


# ---------------------------------------------------------------------------
# 2. Telegram dispatch only
# ---------------------------------------------------------------------------

class TestTelegramDispatchOnly:
    def test_send_notification_delegates_to_send_telegram(self):
        """send_notification must call send_telegram — no other transport."""
        with patch("cuttingboard.output.send_telegram", return_value=True) as mock_tg:
            result = send_notification("HALT", "system halted")
        mock_tg.assert_called_once_with(
            "HALT", "system halted",
            notification_priority="",
            notification_state_key="",
        )
        assert result is True

    def test_send_telegram_posts_to_telegram_api(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch.object(config, "TELEGRAM_BOT_TOKEN", "bot-abc"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "99"):
                with patch("requests.post", return_value=mock_resp) as mock_post:
                    send_telegram("title", "body")
        url_called = mock_post.call_args[0][0]
        assert "api.telegram.org" in url_called
        assert "bot-abc" in url_called
        assert "sendMessage" in url_called

    def test_send_telegram_sends_chat_id_in_json(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "777"):
                with patch("requests.post", return_value=mock_resp) as mock_post:
                    send_telegram("title", "body")
        payload = mock_post.call_args[1]["json"]
        assert payload["chat_id"] == "777"


# ---------------------------------------------------------------------------
# 3. Notification path integrity — one dispatch per alert
# ---------------------------------------------------------------------------

class TestNotificationPathIntegrity:
    def test_single_dispatch_per_send_notification_call(self):
        """Exactly one HTTP POST must be made per send_notification call."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=mock_resp) as mock_post:
                    send_notification("NO TRADE", "STAY_FLAT — no setups")
        assert mock_post.call_count == 1

    def test_title_and_body_both_present_in_sent_text(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch.object(config, "TELEGRAM_BOT_TOKEN", "tok"):
            with patch.object(config, "TELEGRAM_CHAT_ID", "1"):
                with patch("requests.post", return_value=mock_resp) as mock_post:
                    send_notification("HALT", "macro data invalid")
        text = mock_post.call_args[1]["json"]["text"]
        assert "HALT" in text
        assert "macro data invalid" in text

    def test_no_dispatch_when_unconfigured(self):
        with patch.object(config, "TELEGRAM_BOT_TOKEN", None):
            with patch.object(config, "TELEGRAM_CHAT_ID", None):
                with patch("requests.post") as mock_post:
                    send_notification("title", "body")
        mock_post.assert_not_called()
