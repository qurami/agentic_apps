# Banca Lumera — Day 8 process runner.
#
# RASA_LICENSE and OPENAI_API_KEY are NOT set here: export them in your shell.
# The core-banking variables below are demo values shared by the mock API
# (which checks the token) and the action code (which sends it).

export CORE_BANKING_URL := http://localhost:8000
export CORE_BANKING_TOKEN := test_token

# One-time: create the two virtual environments.
setup:
	cd lumera-fastapi-server && uv venv --python 3.11 && uv pip install -r requirements.txt
	cd lumera-assistant && uv venv --python 3.11 && uv pip install 'rasa-pro>=3.17' requests

# Terminal 1 — the mock core-banking API on :8000
run-fastapi-server:
	cd lumera-fastapi-server && .venv/bin/uvicorn lumera_fastapi_server:app --reload

# Terminal 2 (only for the external-wiring demo) — the action server on :5055
run-actions-server:
	cd lumera-assistant && .venv/bin/rasa run actions

# Terminal 3 — train and open the Inspector
run-rasa:
	cd lumera-assistant && .venv/bin/rasa train && .venv/bin/rasa inspect
