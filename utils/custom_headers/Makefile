# Export RASA_LICENSE and OPENAI_API_KEY before running these targets.

# Create the virtual environment.
setup:
	cd header-assistant && uv venv --python 3.11 && uv pip install 'rasa-pro>=3.17'

# Train after changing flows, domain, or config.
train:
	cd header-assistant && .venv/bin/rasa train

# Terminal 1: start Rasa on http://localhost:5005 with API and CORS enabled.
run:
	cd header-assistant && .venv/bin/rasa run --enable-api --cors "*" --port 5005

# Terminal 2: serve the web app on http://localhost:8080.
run-webapp:
	cd webapp && python3 -m http.server 8080

# Terminal client examples:
#   make client MSG="who am I?"
#   make client-stream
MSG ?= who am I?
client:
	header-assistant/.venv/bin/python client.py "$(MSG)"

client-stream:
	header-assistant/.venv/bin/python client.py --stream "show me the streaming demo"
