from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionSendStatementLink(Action):
    def name(self) -> Text:
        return "action_send_statement_link"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        account_type = tracker.get_slot("account_type")
        url = f"https://banca-lumera.example/statements/{account_type}"

        dispatcher.utter_message(
            text=f"Here is the statement of your {account_type} account:"
        )
        dispatcher.utter_message(
            json_message={
                "type": "deeplink",
                "url": url,
                "label": f"Download {account_type} statement (PDF)",
            }
        )
        return []
