# Banca Lumera — process runner (mock core-banking API + assistant).
#
# RASA_LICENSE and OPENAI_API_KEY are NOT set here: export them in your shell.
# The core-banking variables below are demo values shared by the mock API
# (which checks the token) and the action code (which sends it).

export CORE_BANKING_URL := http://localhost:8000
export CORE_BANKING_TOKEN := test_token

# One-time: create the two virtual environments.
# The assistant needs the `rasa-pro[nlu]` extra (classic-NLU components).
# On Apple Silicon that extra pulls in tensorflow-metal, which is currently
# incompatible with the TensorFlow version resolved next to it — we remove it
# (we don't use TensorFlow components; the intent classifier is scikit-learn).
setup:
	cd lumera-fastapi-server && uv venv --python 3.11 && uv pip install -r requirements.txt
	cd lumera-assistant && uv venv --python 3.11 && uv pip install -r requirements.txt
	cd lumera-assistant && uv pip uninstall tensorflow-metal || true

# Terminal 1 — the mock core-banking API on :8000
run-fastapi-server:
	cd lumera-fastapi-server && .venv/bin/uvicorn lumera_fastapi_server:app --reload

# Terminal 2 (only for the external-wiring demo) — the action server on :5055
run-actions-server:
	cd lumera-assistant && .venv/bin/rasa run actions

# Terminal 3 — train and open the Inspector
run-rasa:
	cd lumera-assistant && .venv/bin/rasa train && .venv/bin/rasa inspect

# Terminal 3 [alternative] — train and open the Inspector with log level info for LLM
run-rasa-llm-info:
	cd lumera-assistant && .venv/bin/rasa train && LOG_LEVEL_LLM_COMMAND_GENERATOR=INFO .venv/bin/rasa inspect

# Terminal 3 [alternative] — train and open the Inspector with log level info for both NLU and LLM
run-rasa-llm-nlu-info:
	cd lumera-assistant && .venv/bin/rasa train && LOG_LEVEL_LLM_COMMAND_GENERATOR=INFO LOG_LEVEL_NLU_COMMAND_ADAPTER=INFO .venv/bin/rasa inspect

# Terminal 3 [alternative] — train and watch API logs
run-rasa-enable-api:
	cd lumera-assistant && .venv/bin/rasa train && .venv/bin/rasa run --enable-api

# Run the regression suite against the latest trained model.
# Stubbed custom actions are a beta feature, hence the env flag. Every turn
# still goes through the real LLM — a full run costs a few dozen calls.
run-e2e-tests:
	cd lumera-assistant && RASA_PRO_BETA_STUB_CUSTOM_ACTION=true .venv/bin/rasa test e2e e2e_tests/

# Same suite, plus the flow/step coverage report.
run-e2e-coverage:
	cd lumera-assistant && RASA_PRO_BETA_STUB_CUSTOM_ACTION=true .venv/bin/rasa test e2e e2e_tests/ --coverage-report
