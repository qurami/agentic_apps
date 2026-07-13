import os
from typing import Any, Dict, List, Text

import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher


class ActionReplaceCard(Action):
    def name(self) -> Text:
        return "action_replace_card"

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
            "card_type": tracker.get_slot("card_type"),
        }

        try:
            response = requests.post(
                f"{api_base}/v1/cards/replace",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
            response.raise_for_status()
            eta_days = response.json()["delivery_eta_days"]
            return [
                SlotSet("card_replacement_eta", f"{eta_days} working days"),
                SlotSet("card_replace_ok", True),
            ]
        except (requests.RequestException, KeyError, TypeError, ValueError):
            return [
                SlotSet("card_replacement_eta", None),
                SlotSet("card_replace_ok", False),
            ]
