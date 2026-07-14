# Custom headers and streaming with Rasa

This standalone example shows how to:

- pass selected HTTP headers from a client to a custom action;
- read those values from Rasa message metadata;
- stream a response through a REST webhook.

For a short explanation of Rasa's HTTP endpoints, channels, and deployment
options, see [how-rasa-serves-http.md](how-rasa-serves-http.md).

## Request path

```text
client headers
  → POST /webhooks/header_rest/webhook
  → HeaderRestInput.get_metadata()
  → tracker.latest_message["metadata"]
  → custom action
```

## Files

| Path | Purpose |
|---|---|
| `header-assistant/` | Small CALM assistant used by the example |
| `header-assistant/channels/header_rest.py` | Copies allow-listed headers into message metadata |
| `header-assistant/actions/show_session.py` | Reads the metadata from the tracker |
| `header-assistant/actions/streaming_demo.py` | Streams a response in chunks |
| `webapp/index.html` | Browser client for normal and streaming requests |
| `client.py` | Command-line client |

## Run the example

Set the required environment variables:

```bash
export RASA_LICENSE=...
export OPENAI_API_KEY=...
```

Prepare and train the assistant:

```bash
make setup
make train
```

Start the services in separate terminals:

```bash
# Terminal 1: Rasa on port 5005
make run
```

```bash
# Terminal 2: browser client on port 8080
make run-webapp
```

Open <http://localhost:8080>.

## Verify the behavior

Send `who am I?`. The response should contain the values that the browser sent
in `X-Session-Id`, `X-Client-Channel`, and `Authorization`.

Send `show me the streaming demo` with streaming enabled. The response should
appear incrementally. Disable streaming to receive the same response normally.

You can run the same checks from a terminal:

```bash
make client MSG="who am I?"
make client-stream
```

The custom channel copies only the three allow-listed headers. Metadata is
attached to each user message, so a changed header value is available to the
next action call.
