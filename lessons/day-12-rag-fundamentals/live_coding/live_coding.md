# Day 12 — Live coding: adding a knowledge layer

Today we add Enterprise Search to the Day 11 assistant. Policy documents will answer knowledge questions, even during a paused flow. We then update the affected tests and add a grounded-answer test.

Work in `starting-point/`. Use `end-result/` as the reference solution. The five policy documents in `lumera-assistant/docs/` are provided. Read them, but do not recreate them.

> **Requirements:** export `RASA_LICENSE` and `OPENAI_API_KEY`. Start the mock bank on port `8000` when testing transfers. Training, knowledge turns, and the final judged test make paid API calls.

From `starting-point/`, prepare the project:

```bash
make setup
```

For search debugging, start Rasa with both `LOG_LEVEL_LLM_COMMAND_GENERATOR=INFO` and `LOG_LEVEL_LLM_ENTERPRISE_SEARCH=INFO`.

## 1. Confirm the starting behavior

Start a fresh conversation on the untouched Day 11 project:

> **user:** does the current account have a monthly maintenance fee?
> **bot:** I am afraid, I don't know the answer. At this point, I don't have access to a knowledge base. (rephrased)

The tracker shows a knowledge command followed by `pattern_search`. Its default step returns `utter_no_knowledge_base`. The route already exists; we need to connect it to the policy and corpus.

## 2. Inspect the provided corpus

Enterprise Search development mode reads plain-text files from a local folder. Inspect the provided files:

```
docs/
├── accounts.txt         # maintenance fee (€2.50, waived above €5,000), savings interest
├── card_fees.txt        # card yearly fees, replacement fee, foreign-withdrawal fee
├── transfer_limits.txt  # €5,000 per-transfer limit, €10,000 daily, SEPA timing
├── security.txt         # security codes, what the bank never asks, fraud line
└── branches.txt         # opening hours, main branches
```

Keep these constraints in mind:

- **Only `.txt` files are read.** Rasa reads subfolders recursively. Convert formats such as PDF and HTML to text before indexing them.
- **Indexing happens during training.** `rasa train` chunks and embeds the files. It stores the FAISS index in the model archive. Retrain after changing a document. Production stores such as Milvus and Qdrant can update the corpus without retraining Rasa.
- **Documents must match the assistant.** The documented €5,000 limit must match the flow validation. Review documents and flow rules together.

## 3. Configure Enterprise Search

Make three edits, then retrain.

**Edit one — swap the command generator** (`config.yml`). Enterprise Search wants a generator whose command vocabulary includes search:

```yaml
pipeline:
- name: WhitespaceTokenizer
- name: CountVectorsFeaturizer
- name: LogisticRegressionClassifier
- name: NLUCommandAdapter
- name: SearchReadyLLMCommandGenerator   # was: CompactLLMCommandGenerator
  llm:
    model_group: openai_llm
```

The new generator supports `search and reply`, but not `offtopic reply`. Small talk can therefore route through `pattern_search`. Section 5 shows how this affects the tests.

**Edit two — add the policy** (`config.yml`) and its models (`endpoints.yml`):

```yaml
policies:
- name: FlowPolicy
- name: EnterpriseSearchPolicy
  vector_store:
    type: faiss        # the development-mode default: local, in the model
    source: ./docs
  llm:
    model_group: search_llm
  embeddings:
    model_group: openai_embeddings
```

```yaml
# endpoints.yml — two new model groups
  - id: search_llm
    models:
      - provider: openai
        model: gpt-5-mini-2025-08-07     # answer generation is a cheaper job
        timeout: 25
  - id: openai_embeddings
    models:
      - provider: openai
        model: text-embedding-3-large
```

The search model handles answer generation. The embedding model indexes documents during training and embeds questions at runtime.

**Edit three — override the search pattern** (`data/flows/patterns/pattern_search.yml`). The default `pattern_search` returns `utter_no_knowledge_base`. Point the pattern to Enterprise Search:

```yaml
flows:
  pattern_search:
    description: Flow for handling knowledge-based questions
    name: pattern search
    steps:
      - action: action_trigger_search
```

Retrain:

```bash
cd lumera-assistant
.venv/bin/rasa data validate
.venv/bin/rasa train
```

The FAISS index is stored in the model archive. Retrain after changing the corpus. Hosted embeddings also send the document content to the model provider during training.

## 4. Verify search behavior

### 4.1 Answer a supported question

> **user:** does the current account have a monthly maintenance fee?
> **bot:** Yes. The Lumera current account has a maintenance fee of €2.50 per month. The fee is waived in any month where the average account balance stays above €5,000.

The tracker should show `pattern_search`, then `action_trigger_search`. The search log shows the retrieved chunks and source files. The €2.50 fact comes from `accounts.txt`.

### 4.2 Ask a knowledge question during a transfer

Start a transfer, authenticate, reach the amount question, and ask about the limit:

> **user:** I want to send some money to a friend
> **bot:** For your security, please enter your one-time code.
> **user:** 123456
> **bot:** Who is the recipient of the transfer?
> **user:** Giulia Bianchi
> **bot:** What is the recipient's IBAN?
> **user:** IT60X0542811101000000123456
> **bot:** How much would you like to transfer, in euros?
> **user:** wait, what is the maximum amount I can transfer?
> **bot:** Online single transfers from a Lumera current account are limited to €5,000 per transfer, and the total amount you can order online in one day is €10,000. For transfers above €5,000 you must order at a branch (they'll perform additional verification)
> **bot:** Do you want to go ahead and continue with the money transfer?
> **user:** yes
> **bot:** How much would you like to transfer, in euros?
> **user:** 300
> **bot:** Please confirm: transfer €300.0 to Giulia Bianchi, IBAN IT60X0542811101000000123456. Shall I proceed?

In the Inspector, `pattern_search` sits above the paused transfer. After the answer, `pattern_continue_interrupted` offers to resume. The assistant then asks for the amount again. The retrieved €5,000 limit matches the flow validation.

### 4.3 Prefer an actionable flow

> **user:** how do I send money to someone?
> **bot:** For your security, please enter your one-time code.

Usually the generator should prefer the actionable `transfer_money` flow over `pattern_search`. If this routes incorrectly, inspect the flow description because descriptions drive routing.

### 4.4 Reject an unsupported question

> **user:** what is your mortgage rate for buying a house in France?
> **bot:** I don't know — the provided documents only cover current/savings accounts, cards, transfers and branch hours and do not state any mortgage rates or mortgage products.

FAISS still returns nearest chunks for an unrelated question. Make the no-answer behavior explicit by enabling citations and relevancy checking in `config.yml`:

```yaml
- name: EnterpriseSearchPolicy
  # ... as before ...
  citation_enabled: true   # found answers list sources at the end
  check_relevancy: true    # an answer the retrieved documents don't support is dropped for pattern_cannot_handle
```

After retrain and inspect: 

> **user:** what is your mortgage rate for buying a house in France?
> **bot:** I'm sorry, but I'm not able to provide that information.

The unsupported question now routes to the testable `pattern_cannot_handle` flow.

Supported answers now include citations:

> **user:** does the current account have a monthly maintenance fee?
> **bot:** Yes. The Lumera current account has a maintenance fee of €2.50 per month, waived in any month where the average account balance stays above €5,000. [1]
> Sources:
> [1] docs/accounts.txt

`docs/accounts.txt` is a file path, not a link. In development mode, FAISS stores this path in the chunk's `source` metadata. The assistant does not serve the file over HTTP.

With an external store such as Milvus or Qdrant, you provide the metadata. Set `source` to a public URL when customers need clickable citations. The development filename still tells you which local document supports the answer.

## 5. Check what the new prompt changed

`SearchReadyLLMCommandGenerator` does more than add search. It replaces the prompt and command list used by the previous generator. Compare the official [Compact prompt](https://rasa.com/docs/reference/config/components/llm-command-generators/#prompt-template-1) and [SearchReady prompt](https://rasa.com/docs/reference/config/components/llm-command-generators/#prompt-template).

This can change how the model interprets existing messages. Stop the mock bank, then run the tests. The tests use action stubs.

```bash
make run-e2e-tests
```

The failure list can vary because test messages still pass through the LLM command generator. The chitchat failure is expected: the new prompt has no `offtopic reply`, so the case no longer reaches `pattern_chitchat`. Terse messages, especially bare numbers, may also fail on some runs:

```
...
FAILED e2e_tests/patterns/chitchat.yml::off_topic_message_goes_to_pattern_chitchat
...
```

The chitchat failure is caused directly by the new prompt and command list.

### 5.1 Update the chitchat test

The SearchReady prompt has no `offtopic reply` command. It uses `search and reply` for social messages. The existing `pattern_chitchat` override is no longer triggered.

Replace `e2e_tests/patterns/chitchat.yml` with:

```yaml
test_cases:
  - test_case: off_topic_message_goes_to_pattern_search
    steps:
      - user: do you like pizza?
        assertions:
          - flow_started:
              operator: all
              flow_ids:
                - pattern_search
```

This records the SearchReady behavior. It does not restore `pattern_chitchat`.

### 5.2 Make numeric test replies more explicit

The over-limit test fails before validation. In the failing run, GPT-5.1 converts `9000` to this invalid command:

```text
set slot transfer_money_transfer_amount 9000
```

That slot does not exist. Rasa drops the command and runs `pattern_cannot_handle`.

This does not happen on every run. `9000` works in the live conversation, and other bare numbers fail only in some test runs. The new prompt has made these replies less stable in this test context.

In `e2e_tests/validation/transfer_input_validation.yml`, replace the `9000` user step with:

```yaml
      - user: I want to send 9000
        assertions:
          - bot_uttered:
              utter_name: utter_transfer_over_limit
```

In `e2e_tests/patterns/correction.yml`, replace the `200` user step with:

```yaml
      - user: I want to send 200
        assertions:
          - bot_uttered:
              utter_name: utter_ask_transfer_confirmed
```

In `e2e_tests/transfers/transfer_happy_path.yml`, replace the `100` user step with:

```yaml
      - user: send 100 please
      - slot_was_set:
          - transfer_amount: 100.0
```

These changes make the tests more stable. Bare numbers are still valid replies. Run `make run-e2e-tests` again and confirm that all eight tests pass.

## 6. Compare generative and extractive search

Generative search writes an answer from the retrieved text. It can combine passages, but it can still add unsupported claims.

Extractive search returns a pre-written answer instead. Enable it in `config.yml`:

```yaml
- name: EnterpriseSearchPolicy
  # ...
  use_generative_llm: false
```

Retrain. Rasa prints many warnings, so filter the output:

```bash
cd lumera-assistant && (set -o pipefail; .venv/bin/rasa train 2>&1 \
	  | grep -Eo 'Chunk does not match expected QA format|"len_chunks": 0|"exc_value": "No documents found[^"]*"' \
	  | sort \
	  | uniq -c)
```

```
   1 "exc_value": "No documents found at './docs'."
   1 "len_chunks": 0
  27 Chunk does not match expected QA format
```

Extractive mode requires question-and-answer pairs. It embeds each question and returns its answer exactly as written. The existing prose documents do not contain these pairs, so the index is empty.

Create `docs/faq.txt`:

```
Q: Does the current account have a monthly maintenance fee?
A: Yes. The Lumera current account costs 2.50 euros per month, waived in any month where the average balance stays above 5,000 euros.

Q: What is the maximum amount for an online transfer?
A: Online transfers are limited to 5,000 euros per single transfer, with a daily online ceiling of 10,000 euros. Larger transfers must be ordered at a branch.

Q: How much does it cost to replace a lost or stolen card?
A: Replacing a card costs 10 euros and the new card arrives within 5 working days. Blocking the old card is free and immediate.
```

Retrain. Rasa skips the prose files and indexes the three Q/A pairs. Ask:

> **user:** does the current account have a monthly maintenance fee?
> **bot:** Yes. The Lumera current account costs 2.50 euros per month, waived in any month where the average balance stays above 5,000 euros.

The response matches the stored `A:` line. Now ask the unsupported mortgage question again:

> **user:** what is your mortgage rate for buying a house in France?
> **bot:** Yes. The Lumera current account costs 2.50 euros per month, waived in any month where the average balance stays above 5,000 euros.

This answer is wrong. Extractive mode does not run the generative relevancy check. The local FAISS setup also has no similarity threshold, so it returns the nearest Q/A pair even when the match is poor.

Production vector stores such as Milvus and Qdrant can enforce a similarity threshold. A poor match can then return no answer. Extractive mode removes generation risk, but it still needs a distance guard.

Set `use_generative_llm: true` again. Keep citations and relevancy checking enabled, then retrain. Leave `faq.txt` in place; generative mode treats it as more corpus text.

Use generative search for broader coverage. Use extractive search when every answer must be approved in advance, together with a similarity threshold.

## 7. Test a generated answer

Generated text changes between runs, so do not assert the exact response. Configure an LLM judge in the existing `e2e_tests/conftest.yml`:

```yaml
llm_judge:
  llm:
    provider: openai
    model: gpt-5-mini-2025-08-07
  embeddings:
    provider: openai
    model: text-embedding-3-large
```

Keep this block in `e2e_tests/conftest.yml`. The runner stops at the first `conftest.yml` it finds while walking up from the test file, so a second file at the project root would be ignored.

Rasa recommends using a different provider for judging and generation to reduce self-preference bias. This project uses one provider because the course uses one API key. Use separate providers in production.

Create `e2e_tests/knowledge/knowledge_grounding.yml`:

```yaml
test_cases:
  - test_case: knowledge_answer_grounded_in_corpus
    steps:
      - user: does the current account have a monthly maintenance fee?
        assertions:
          - generative_response_is_grounded:
              threshold: 0.9
              utter_source: EnterpriseSearchPolicy
              ground_truth: >-
                The Lumera current account has a maintenance fee of 2.50
                euros per month. The fee is waived in any month where the
                average account balance stays above 5,000 euros.
          # Relevancy is scored as the average cosine similarity between
          # the user message and 3 question variations the judge generates
          # from the answer — good answers score well below 1.0, so the threshold is calibrated
          # against observed scores, not copied from the grounded one.
          - generative_response_is_relevant:
              threshold: 0.6
              utter_source: EnterpriseSearchPolicy
```

`generative_response_is_grounded` checks whether the answer is supported by `ground_truth`. `generative_response_is_relevant` checks whether the answer addresses the question. `utter_source` selects the component whose response is judged.

The thresholds differ because the scores measure different things. Groundedness is the fraction of supported statements. Relevancy is an embedding-similarity score. A valid answer scored `0.67` in the captured run, so a `0.9` relevancy threshold was too high. Calibrate judge thresholds with observed results.

Each assertion adds judge calls and cost. Run the full suite twice. Confirm that the eight existing tests and the new knowledge test pass on both runs.

## 8. Final verification

Before finishing, confirm that:

- supported questions return grounded answers with citations;
- unsupported questions run `pattern_cannot_handle`;
- a knowledge question can pause and resume a transfer;
- actionable requests still prefer flows over search;
- all nine end-to-end tests pass twice.
