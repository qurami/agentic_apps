"""Show the session metadata stored on the tracker."""

from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionShowSession(Action):
    def name(self) -> Text:
        return "action_show_session"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # The custom channel stores selected headers here.
        metadata = tracker.latest_message.get("metadata") or {}

        session_id = metadata.get("session_id")
        client_channel = metadata.get("client_channel")
        authorization = metadata.get("authorization")

        if not any([session_id, client_channel, authorization]):
            # Shell, Inspector, and plain curl requests may omit these headers.
            dispatcher.utter_message(
                text=(
                    "No session metadata reached me on this message. "
                    "Talk to me through the header_rest webhook with the "
                    "X-Session-Id / X-Client-Channel / Authorization headers set."
                )
            )
            return []

        # Show only part of the credential.
        auth_hint = (
            f"{authorization[:12]}… ({len(authorization)} chars)"
            if authorization
            else "not sent"
        )

        dispatcher.utter_message(
            text=(
                "Here is what your app attached to this message as HTTP headers:\n"
                f"• session id: {session_id or 'not sent'}\n"
                f"• client channel: {client_channel or 'not sent'}\n"
                f"• authorization: {auth_hint}"
            )
        )
        dispatcher.utter_message(
            text=(
                "They travelled: HTTP request → HeaderRestInput.get_metadata() → "
                "message metadata on the tracker → this custom action."
            )
        )
        return []
