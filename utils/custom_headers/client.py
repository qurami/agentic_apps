"""Send messages and session headers to the Rasa webhook.

Run from `custom_headers` after starting Rasa:

    header-assistant/.venv/bin/python client.py "who am I?"
    header-assistant/.venv/bin/python client.py --stream "show me the streaming demo"
"""

import argparse
import json
import uuid

import requests

# Default webhook for the custom channel.
DEFAULT_WEBHOOK = "http://localhost:5005/webhooks/header_rest/webhook"
WEBHOOK = DEFAULT_WEBHOOK  # Overridden by --url.

# Example session headers sent with each request.
SESSION_HEADERS = {
    "X-Session-Id": "sess-4242-from-python-client",
    "X-Client-Channel": "python-demo-client",
    "Authorization": "Bearer demo-token-not-a-real-secret",
}


def send_plain(sender_id: str, message: str) -> None:
    """Print every message from a complete JSON response."""
    response = requests.post(
        WEBHOOK,
        headers=SESSION_HEADERS,
        json={"sender": sender_id, "message": message},
        timeout=60,
    )
    response.raise_for_status()
    for bot_message in response.json():
        print(f"bot> {bot_message.get('text', bot_message)}")


def send_streaming(sender_id: str, message: str) -> None:
    """Print newline-delimited messages as they arrive."""
    response = requests.post(
        WEBHOOK + "?stream=true",
        headers=SESSION_HEADERS,
        json={"sender": sender_id, "message": message},
        stream=True,  # Do not buffer the full response.
        timeout=60,
    )
    response.raise_for_status()

    mid_stream = False
    for line in response.iter_lines():
        if not line:
            continue
        bot_message = json.loads(line)
        if bot_message.get("chunk"):
            # Keep chunks on the same line.
            print(bot_message.get("text", ""), end="", flush=True)
            mid_stream = True
        else:
            if mid_stream:
                print()  # End the streamed message.
                mid_stream = False
            print(f"bot> {bot_message.get('text', bot_message)}")
    if mid_stream:
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("message", help="what to say to the assistant")
    parser.add_argument(
        "--stream", action="store_true", help="read the answer as it is produced"
    )
    parser.add_argument(
        "--sender",
        default=f"py-{uuid.uuid4().hex[:8]}",
        help="conversation id (same sender = same conversation)",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_WEBHOOK,
        help="the Rasa webhook URL (change it if rasa runs on another port)",
    )
    args = parser.parse_args()
    WEBHOOK = args.url

    if args.stream:
        send_streaming(args.sender, args.message)
    else:
        send_plain(args.sender, args.message)
