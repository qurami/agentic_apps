import os
from typing import Any, Dict, List, Text

import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher


class ActionExecuteTransfer(Action):
    def name(self) -> Text:
        return "action_execute_transfer"

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
            "recipient_name": tracker.get_slot("recipient_name"),
            "recipient_iban": tracker.get_slot("recipient_iban"),
            "amount": tracker.get_slot("transfer_amount"),
        }

        try:
            response = requests.post(
                f"{api_base}/v1/transfers",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
            response.raise_for_status()
            transfer_id = response.json()["transfer_id"]
            return [
                SlotSet("transfer_id", transfer_id),
                SlotSet("transfer_ok", True),
            ]
        except (requests.RequestException, KeyError, TypeError, ValueError):
            return [
                SlotSet("transfer_id", None),
                SlotSet("transfer_ok", False),
            ]
