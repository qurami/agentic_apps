import os
from typing import Any, Dict, List, Text

import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher


class ActionVerifyCustomer(Action):
    def name(self) -> Text:
        return "action_verify_customer"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        api_base = os.environ.get("CORE_BANKING_URL")
        token = os.environ.get("CORE_BANKING_TOKEN")

        payload = {
            "customer_id": tracker.sender_id,
            "security_code": tracker.get_slot("security_code"),
        }

        try:
            response = requests.post(
                f"{api_base}/v1/auth/verify",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
            response.raise_for_status()
            verified = bool(response.json()["verified"])
        except (requests.RequestException, KeyError, TypeError, ValueError):
            verified = False

        return [
            SlotSet("authenticated", verified),
            # Never keep a security code in conversation memory.
            SlotSet("security_code", None),
        ]
