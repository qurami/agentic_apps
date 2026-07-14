"""Copy selected HTTP headers into Rasa message metadata.

The channel is registered in `credentials.yml` and exposed at
`POST /webhooks/header_rest/webhook`.
"""

from asyncio import Queue
from typing import Any, Awaitable, Callable, Dict, Optional, Text

from sanic.request import Request

from rasa.core.channels.channel import OutputChannel, UserMessage
from rasa.core.channels.rest import QueueOutputChannel, RestInput


class HeaderRestInput(RestInput):
    """REST channel with header metadata and marked stream chunks."""

    @classmethod
    def name(cls) -> Text:
        return "header_rest"

    def get_metadata(self, request: Request) -> Optional[Dict[Text, Any]]:
        """Return an allow-list of headers to store as message metadata."""
        return {
            "session_id": request.headers.get("X-Session-Id"),
            "client_channel": request.headers.get("X-Client-Channel"),
            # Validate credentials before using them in production.
            "authorization": request.headers.get("Authorization"),
        }

    # Mark streamed chunks so clients can distinguish them from full messages.

    @staticmethod
    async def on_message_wrapper(
        on_new_message: Callable[[UserMessage], Awaitable[Any]],
        text: Text,
        queue: Queue,
        sender_id: Text,
        input_channel: Text,
        metadata: Optional[Dict[Text, Any]],
    ) -> None:
        """Same as RestInput.on_message_wrapper, but with the marked queue."""
        collector = MarkedQueueOutputChannel(queue)
        message = UserMessage(
            text, collector, sender_id, input_channel=input_channel, metadata=metadata
        )
        await on_new_message(message)
        await queue.put("DONE")


class MarkedQueueOutputChannel(QueueOutputChannel):
    """QueueOutputChannel whose token chunks carry a `"chunk": true` marker."""

    async def send_response_chunk(
        self, recipient_id: Text, chunk: Text, **kwargs: Any
    ) -> None:
        # Accumulate the text without enqueuing an unmarked duplicate.
        await OutputChannel.send_response_chunk(self, recipient_id, chunk, **kwargs)
        await self.messages.put(
            {"recipient_id": recipient_id, "text": chunk, "chunk": True}
        )
