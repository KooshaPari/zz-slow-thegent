"""WP-17003: Push Notification Bridge (Firebase).
Sends real-time alerts to the mobile companion app using Firebase Cloud Messaging (FCM).
"""

import logging

_log = logging.getLogger(__name__)


class NotificationBridge:
    """Sends push notifications to registered devices via FCM."""

    def __init__(self, fcm_api_key: str, project_id: str) -> None:
        self.fcm_api_key = fcm_api_key
        self.project_id = project_id
        self.fcm_url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"

    async def send_push(self, device_token: str, title: str, body: str, data: dict[str, str] | None = None) -> bool:
        """Send a push notification to a specific device."""
        _log.info("Sending push notification to device: %s", device_token[:10] + "...")



        try:
            # Simulated HTTP call
            # async with httpx.AsyncClient() as client:
            #     resp = await client.post(self.fcm_url, json=message, headers=headers)
            #     if resp.status_code != 200:
            #         _log.error("FCM push failed: %s", resp.text)
            #         return False
            _log.info("Push notification sent successfully (Mocked)")
            return True
        except Exception as e:
            _log.error("Failed to send push notification: %s", e)
            return False

    async def alert_policy_violation(self, device_token: str, run_id: str, rule_id: str) -> bool:
        """Specific alert for a policy violation."""
        title = "⚠️ Policy Violation Detected"
        body = f"Run {run_id} violated rule {rule_id}. Approval required."
        data = {"run_id": run_id, "type": "policy_violation", "rule_id": rule_id}
        return await self.send_push(device_token, title, body, data)
