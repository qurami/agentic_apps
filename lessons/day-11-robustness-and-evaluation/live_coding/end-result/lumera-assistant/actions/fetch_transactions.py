import os
from typing import Any, Dict, List, Text

import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher


def _format_row(transaction: Dict[Text, Any]) -> Text:
    amount = transaction["amount"]
    sign = "-" if amount < 0 else "+"
    return f"{transaction['date']}  {transaction['description']}  {sign}€{abs(amount):.2f}"


class ActionFetchTransactions(Action):
    def name(self) -> Text:
        return "action_fetch_transactions"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        api_base = os.environ.get("CORE_BANKING_URL")
        token = os.environ.get("CORE_BANKING_TOKEN")
        account_type = tracker.get_slot("account_type")

        try:
            response = requests.get(
                f"{api_base}/v1/accounts/{account_type}/transactions",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
            response.raise_for_status()
            transactions = response.json()["transactions"]
            listing = "\n".join(_format_row(t) for t in transactions)
            return [
                SlotSet("transactions_list", listing),
                SlotSet("transactions_fetch_ok", True),
            ]
        except (requests.RequestException, KeyError, TypeError, ValueError):
            return [
                SlotSet("transactions_list", None),
                SlotSet("transactions_fetch_ok", False),
            ]
