import os
from typing import Any, Dict, List, Text

import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher


class ActionBlockCard(Action):
    def name(self) -> Text:
        return "action_block_card"

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
                f"{api_base}/v1/cards/block",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
            response.raise_for_status()
            blocked = response.json()["status"] == "blocked"
            return [SlotSet("card_block_ok", blocked)]
        except (requests.RequestException, KeyError, TypeError, ValueError):
            return [SlotSet("card_block_ok", False)]
