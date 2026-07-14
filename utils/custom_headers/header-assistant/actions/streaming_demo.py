"""Stream a response one word at a time."""

import asyncio
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

DEMO_TEXT = (
    "Watch closely — this sentence is being produced word by word by a custom "
    "action, pushed through Rasa's output channel as individual chunks, and "
    "written onto the open HTTP response your client is still reading. "
    "That is all streaming is: one long-lived response, many small writes."
)


class ActionStreamingDemo(Action):
    def name(self) -> Text:
        return "action_streaming_demo"

    # Streaming dispatcher methods are asynchronous.
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        await dispatcher.stream_start()
        for word in DEMO_TEXT.split(" "):
            await dispatcher.stream_chunk(text=word + " ")
            # Slow the demo enough to make each chunk visible.
            await asyncio.sleep(0.04)
        await dispatcher.stream_end()
        return []
