import os
from typing import Any, Dict, List, Text

import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher


class ValidateTransferAmount(Action):
    """Layer-3 validation: the truth about available funds lives in the
    core-banking system, not in YAML. Rasa runs any action named
    validate_<slot_name> automatically whenever that slot is collected."""

    def name(self) -> Text:
        return "validate_transfer_amount"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        amount = tracker.get_slot("transfer_amount")
        if amount is None:
            return []

        api_base = os.environ.get("CORE_BANKING_URL")
        token = os.environ.get("CORE_BANKING_TOKEN")

        try:
            response = requests.get(
                f"{api_base}/v1/balance",
                params={"account_type": "checking"},
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
            response.raise_for_status()
            balance = response.json()["balance"]
        except (requests.RequestException, KeyError, TypeError, ValueError):
            # If the balance service is unreachable, don't block the customer
            # at validation: the transfer execution itself fails clean.
            return []

        if amount > balance:
            dispatcher.utter_message(
                response="utter_insufficient_funds",
                available_balance=f"{balance:.2f}",
            )
            return [SlotSet("transfer_amount", None)]

        return []
