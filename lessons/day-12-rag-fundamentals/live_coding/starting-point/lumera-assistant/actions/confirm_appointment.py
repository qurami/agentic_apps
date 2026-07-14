import os
from typing import Any, Dict, List, Text

import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher


class ActionConfirmAppointment(Action):
    def name(self) -> Text:
        return "action_confirm_appointment"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        api_base = os.environ.get("CORE_BANKING_URL")
        token = os.environ.get("CORE_BANKING_TOKEN")

        # Everything the conversation collected, read back from the tracker.
        payload = {
            "customer_id": tracker.sender_id,
            "branch_city": tracker.get_slot("branch_city"),
            "topic": tracker.get_slot("appointment_topic"),
            "preferred_time": tracker.get_slot("preferred_time"),
        }

        try:
            response = requests.post(
                f"{api_base}/v1/appointments",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
            response.raise_for_status()
            reference = response.json()["reference"]
            return [
                SlotSet("booking_reference", reference),
                SlotSet("booking_ok", True),
            ]
        except (requests.RequestException, KeyError, TypeError, ValueError):
            return [
                SlotSet("booking_reference", None),
                SlotSet("booking_ok", False),
            ]
