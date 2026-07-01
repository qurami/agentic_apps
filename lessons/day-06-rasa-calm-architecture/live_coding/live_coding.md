# Day 6 — Live coding: empty directory to first conversation

## Chapter 6 — Worked walkthrough: empty directory to first conversation

> ** REQUIREMENTS:
> Have `uv` installed (on macos: `brew install uv`), 
> Have a valid `RASA_LICENSE` exported 
> Have an `OPENAI_API_KEY` exported 

### 6.1 Empty room → install → verify

Start from nothing, create and activate a virtual environment, then install:

```bash
mkdir lumera-assistant && cd lumera-assistant
uv venv --python 3.11 && source .venv/bin/activate
uv pip install rasa-pro
```

That pulls the **full Rasa Pro** from the public PyPI — no private index — free under the Developer Edition within caps. Then verify; three lines confirm the install (the Rasa Pro version, the Python version, and **License Expires** — the license check working)

### 6.2 Scaffold and train

Scaffold into the current directory and accept the training offer:

```bash
rasa init --template default --init-dir .   # --init-dir . scaffolds into the current directory (lumera-assistant) rather than a new subfolder
```

As the file-copy log scrolls you will see the tree materialize on disk — the `domain/` split, the `data/flows/` directory, the `e2e_tests/` suite. Then the train log names the two components from `config.yml` — `CompactLLMCommandGenerator` and `FlowPolicy`, the components that implement understanding and decision stages — and ends with:

```text
Your Rasa model is trained and saved at 'models/<timestamp>-<adjective>-<noun>.tar.gz'.
```

**No LLM call happened yet**: training does not need the model; conversations do. Run `rasa train` a second time and both components **restore from cache**, near-instant.

### 6.3 Use the Inspector

Start the Inspector:

```bash
rasa inspect
```

The inspector page should be opened automatically; if it doesn't, a url is printed to be opened. 

When the browser opens, use the **Inspect** view as a map of the running conversation. It has three columns.

1. **Left: Preview.** This is the chat transcript plus the event stream. It shows user messages, assistant messages, actions, flow starts, slot writes, "waiting for user input", and "bot turn ended".
2. **Middle: current flow diagram.** This is the business process view. It shows the active flow as boxes connected by arrows, with the current step outlined in purple.
3. **Right: History and Memory.** History shows which flows have run and whether they are active or completed. Memory shows current values: system values always, and current-flow slots once the flow starts filling them.

Read those columns from left to right: **what happened**, **where we are in the flow**, **what state Rasa remembers**. Before typing anything, point to the initial state:

1. In **Preview** shows a list of events 
2. In the **middle**, the empty-state message says `No flow is currently active`: no business process has started yet.
3. In **History**, `Pattern session start` is marked `Completed`. That was Rasa's system startup pattern, not a business flow.
4. In **Memory**, still no slot exists yet because no flow has started.

Now type:

> "Add a contact"

Now read what changed:

1. In **Preview**, the event stream says `Flow add_contact started` and the assistant runs `utter_ask_add_contact_handle` and asks: `"What's the handle of the user you want to add?"`
2. In the **middle**, the add a contact flow diagram appears, and `add_contact_handle` is outlined in purple telling the current step.
3. Subsequent steps, such as `add_contact_name` and `add_contact_confirmation`
4. In **History**, `Add a contact` appears above `Pattern session start` and is marked `Active`. This is the live dialogue stack in plain language: the user flow is now on top; the startup pattern is finished below it.
5. In **Memory**, there is still no current-flow slot value. 

Proceed typing the contact handle, e.g:

```text
@anna
```

Now take a look to the updated panels:

1. In **Preview** the event stream says `Slot add_contact_handle set` and the assistant runs `utter_ask_add_contact_name` for the next question
2. In the **middle** the flow advanced one step after the slot was filled.
3. In **Memory**, `add_contact_handle` slot has been populated with the value `"@anna"`: now the value is in conversation memory.
4. In **History**, `Add a contact` is still `Active`, because the flow is not finished because name and confirmation steps are still to be completed.

Complete (or abort) the flow and see how the panels update accordingly.
