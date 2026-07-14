# Day 12 — Live coding: aggiungere un livello di conoscenza

Oggi aggiungiamo Enterprise Search all'assistente del Day 11. I documenti di policy risponderanno alle domande di conoscenza, anche durante un flow in pausa. Aggiorneremo poi i test interessati e aggiungeremo un test di risposta grounded.

Lavora in `starting-point/`. Usa `end-result/` come soluzione di riferimento. I cinque documenti di policy in `lumera-assistant/docs/` sono forniti. Leggili, ma non ricrearli.

> **Requisiti:** esporta `RASA_LICENSE` e `OPENAI_API_KEY`. Avvia la mock bank sulla porta `8000` quando testi i trasferimenti. Il training, i turni di conoscenza e il test finale giudicato effettuano chiamate API a pagamento.

Da `starting-point/`, prepara il progetto:

```bash
make setup
```

Per il debug della search, avvia Rasa con `LOG_LEVEL_LLM_COMMAND_GENERATOR=INFO` e `LOG_LEVEL_LLM_ENTERPRISE_SEARCH=INFO` insieme.

## 1. Conferma il comportamento di partenza

Avvia una nuova conversazione sul progetto del Day 11 ancora intatto:

> **user:** does the current account have a monthly maintenance fee?
> **bot:** I am afraid, I don't know the answer. At this point, I don't have access to a knowledge base. (riformulato)

Il tracker mostra un command di knowledge seguito da `pattern_search`. Il suo step di default restituisce `utter_no_knowledge_base`. Il percorso esiste già; dobbiamo collegarlo alla policy e al corpus.

## 2. Ispeziona il corpus fornito

La modalità di sviluppo di Enterprise Search legge file di testo semplice da una cartella locale. Ispeziona i file forniti:

```
docs/
├── accounts.txt         # maintenance fee (€2.50, waived above €5,000), savings interest
├── card_fees.txt        # card yearly fees, replacement fee, foreign-withdrawal fee
├── transfer_limits.txt  # €5,000 per-transfer limit, €10,000 daily, SEPA timing
├── security.txt         # security codes, what the bank never asks, fraud line
└── branches.txt         # opening hours, main branches
```

Tieni a mente questi vincoli:

- **Vengono letti solo i file `.txt`.** Rasa legge le sottocartelle in modo ricorsivo. Converti in testo formati come PDF e HTML prima di indicizzarli.
- **L'indicizzazione avviene durante il training.** `rasa train` suddivide i file in chunk e ne calcola gli embedding. L'indice FAISS viene memorizzato nell'archivio del modello. Riallena dopo aver modificato un documento. Store di produzione come Milvus e Qdrant possono aggiornare il corpus senza riallenare Rasa.
- **I documenti devono essere coerenti con l'assistente.** Il limite di €5,000 documentato deve coincidere con la validazione del flow. Rivedi insieme i documenti e le regole dei flow.

## 3. Configura Enterprise Search

Esegui tre modifiche, poi riallena.

**Modifica uno — sostituisci il command generator** (`config.yml`). Enterprise Search richiede un generator il cui vocabolario di command includa la search:

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

Il nuovo generator supporta `search and reply`, ma non `offtopic reply`. Lo small talk può quindi essere instradato attraverso `pattern_search`. La sezione 5 mostra come questo influisca sui test.

**Modifica due — aggiungi la policy** (`config.yml`) e i suoi modelli (`endpoints.yml`):

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

Il modello di search si occupa della generazione della risposta. Il modello di embedding indicizza i documenti durante il training e calcola l'embedding delle domande a runtime.

**Modifica tre — sovrascrivi il search pattern** (`data/flows/patterns/pattern_search.yml`). Il `pattern_search` di default restituisce `utter_no_knowledge_base`. Punta il pattern a Enterprise Search:

```yaml
flows:
  pattern_search:
    description: Flow for handling knowledge-based questions
    name: pattern search
    steps:
      - action: action_trigger_search
```

Riallena:

```bash
cd lumera-assistant
.venv/bin/rasa data validate
.venv/bin/rasa train
```

L'indice FAISS è memorizzato nell'archivio del modello. Riallena dopo aver modificato il corpus. Gli embedding hosted inviano inoltre il contenuto dei documenti al provider del modello durante il training.

## 4. Verifica il comportamento della search

### 4.1 Rispondi a una domanda supportata

> **user:** does the current account have a monthly maintenance fee?
> **bot:** Yes. The Lumera current account has a maintenance fee of €2.50 per month. The fee is waived in any month where the average account balance stays above €5,000.

Il tracker dovrebbe mostrare `pattern_search`, poi `action_trigger_search`. Il log della search mostra i chunk recuperati e i file sorgente. Il dato dei €2.50 proviene da `accounts.txt`.

### 4.2 Poni una domanda di conoscenza durante un trasferimento

Avvia un trasferimento, autenticati, raggiungi la domanda sull'importo e chiedi del limite:

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

Nell'Inspector, `pattern_search` si colloca sopra il trasferimento in pausa. Dopo la risposta, `pattern_continue_interrupted` propone di riprenderlo. L'assistente chiede poi nuovamente l'importo. Il limite di €5,000 recuperato coincide con la validazione del flow.

### 4.3 Preferisci un flow azionabile

> **user:** how do I send money to someone?
> **bot:** For your security, please enter your one-time code.

Di norma il generator dovrebbe preferire il flow azionabile `transfer_money` a `pattern_search`. Se il routing risulta errato, ispeziona la description del flow, perché sono le description a guidare il routing.

### 4.4 Rifiuta una domanda non supportata

> **user:** what is your mortgage rate for buying a house in France?
> **bot:** I don't know — the provided documents only cover current/savings accounts, cards, transfers and branch hours and do not state any mortgage rates or mortgage products.

FAISS restituisce comunque i chunk più vicini anche per una domanda non pertinente. Rendi esplicito il comportamento di mancata risposta abilitando le citation e il controllo di rilevanza in `config.yml`:

```yaml
- name: EnterpriseSearchPolicy
  # ... as before ...
  citation_enabled: true   # found answers list sources at the end
  check_relevancy: true    # an answer the retrieved documents don't support is dropped for pattern_cannot_handle
```

Dopo il retrain e l'inspect: 

> **user:** what is your mortgage rate for buying a house in France?
> **bot:** I'm sorry, but I'm not able to provide that information.

La domanda non supportata viene ora instradata al flow testabile `pattern_cannot_handle`.

Le risposte supportate includono ora le citation:

> **user:** does the current account have a monthly maintenance fee?
> **bot:** Yes. The Lumera current account has a maintenance fee of €2.50 per month, waived in any month where the average account balance stays above €5,000. [1]
> Sources:
> [1] docs/accounts.txt

`docs/accounts.txt` è un percorso di file, non un link. In modalità di sviluppo, FAISS memorizza questo percorso nel metadato `source` del chunk. L'assistente non serve il file via HTTP.

Con uno store esterno come Milvus o Qdrant, i metadati li fornisci tu. Imposta `source` su un URL pubblico quando i clienti hanno bisogno di citation cliccabili. Il nome del file in sviluppo ti dice comunque quale documento locale supporta la risposta.

## 5. Verifica cosa ha cambiato il nuovo prompt

`SearchReadyLLMCommandGenerator` non si limita ad aggiungere la search. Sostituisce il prompt e la lista di command usati dal generator precedente. Confronta il [Compact prompt](https://rasa.com/docs/reference/config/components/llm-command-generators/#prompt-template-1) e il [SearchReady prompt](https://rasa.com/docs/reference/config/components/llm-command-generators/#prompt-template) ufficiali.

Questo può cambiare il modo in cui il modello interpreta i messaggi esistenti. Ferma la mock bank, poi esegui i test. I test usano gli stub delle action.

```bash
make run-e2e-tests
```

L'elenco dei fallimenti può variare, perché i messaggi di test passano comunque attraverso il command generator LLM. Il fallimento del chitchat è atteso: il nuovo prompt non ha `offtopic reply`, quindi il caso non raggiunge più `pattern_chitchat`. Anche i messaggi laconici, in particolare i numeri nudi, possono fallire in alcune esecuzioni:

```
...
FAILED e2e_tests/patterns/chitchat.yml::off_topic_message_goes_to_pattern_chitchat
...
```

Il fallimento del chitchat è causato direttamente dal nuovo prompt e dalla nuova lista di command.

### 5.1 Aggiorna il test del chitchat

Il prompt SearchReady non ha il command `offtopic reply`. Usa `search and reply` per i messaggi sociali. L'override esistente di `pattern_chitchat` non viene più innescato.

Sostituisci `e2e_tests/patterns/chitchat.yml` con:

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

Questo registra il comportamento di SearchReady. Non ripristina `pattern_chitchat`.

### 5.2 Rendi più esplicite le risposte numeriche nei test

Il test dell'importo oltre il limite fallisce prima della validazione. Nell'esecuzione fallita, GPT-5.1 converte `9000` in questo command non valido:

```text
set slot transfer_money_transfer_amount 9000
```

Quello slot non esiste. Rasa scarta il command ed esegue `pattern_cannot_handle`.

Questo non accade a ogni esecuzione. `9000` funziona nella conversazione dal vivo, e altri numeri nudi falliscono solo in alcune esecuzioni dei test. Il nuovo prompt ha reso queste risposte meno stabili in questo contesto di test.

In `e2e_tests/validation/transfer_input_validation.yml`, sostituisci lo step utente `9000` con:

```yaml
      - user: I want to send 9000
        assertions:
          - bot_uttered:
              utter_name: utter_transfer_over_limit
```

In `e2e_tests/patterns/correction.yml`, sostituisci lo step utente `200` con:

```yaml
      - user: I want to send 200
        assertions:
          - bot_uttered:
              utter_name: utter_ask_transfer_confirmed
```

In `e2e_tests/transfers/transfer_happy_path.yml`, sostituisci lo step utente `100` con:

```yaml
      - user: send 100 please
      - slot_was_set:
          - transfer_amount: 100.0
```

Queste modifiche rendono i test più stabili. I numeri nudi restano risposte valide. Esegui di nuovo `make run-e2e-tests` e conferma che tutti e otto i test passino.

## 6. Confronta search generativa ed estrattiva

La search generativa scrive una risposta a partire dal testo recuperato. Può combinare più passaggi, ma può comunque aggiungere affermazioni non supportate.

La search estrattiva restituisce invece una risposta scritta in anticipo. Abilitala in `config.yml`:

```yaml
- name: EnterpriseSearchPolicy
  # ...
  use_generative_llm: false
```

Riallena. Rasa stampa molti warning, quindi filtra l'output:

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

La modalità estrattiva richiede coppie domanda-risposta. Calcola l'embedding di ciascuna domanda e ne restituisce la risposta esattamente come è scritta. I documenti in prosa esistenti non contengono queste coppie, quindi l'indice è vuoto.

Crea `docs/faq.txt`:

```
Q: Does the current account have a monthly maintenance fee?
A: Yes. The Lumera current account costs 2.50 euros per month, waived in any month where the average balance stays above 5,000 euros.

Q: What is the maximum amount for an online transfer?
A: Online transfers are limited to 5,000 euros per single transfer, with a daily online ceiling of 10,000 euros. Larger transfers must be ordered at a branch.

Q: How much does it cost to replace a lost or stolen card?
A: Replacing a card costs 10 euros and the new card arrives within 5 working days. Blocking the old card is free and immediate.
```

Riallena. Rasa salta i file in prosa e indicizza le tre coppie Q/A. Chiedi:

> **user:** does the current account have a monthly maintenance fee?
> **bot:** Yes. The Lumera current account costs 2.50 euros per month, waived in any month where the average balance stays above 5,000 euros.

La risposta corrisponde alla riga `A:` memorizzata. Ora riproponi la domanda non supportata sul mutuo:

> **user:** what is your mortgage rate for buying a house in France?
> **bot:** Yes. The Lumera current account costs 2.50 euros per month, waived in any month where the average balance stays above 5,000 euros.

Questa risposta è sbagliata. La modalità estrattiva non esegue il controllo di rilevanza generativo. Anche il setup locale con FAISS non ha una soglia di similarità, quindi restituisce la coppia Q/A più vicina anche quando la corrispondenza è scadente.

I vector store di produzione come Milvus e Qdrant possono imporre una soglia di similarità. Una corrispondenza scadente può allora non restituire alcuna risposta. La modalità estrattiva elimina il rischio della generazione, ma necessita comunque di una guardia sulla distanza.

Reimposta `use_generative_llm: true`. Mantieni abilitati le citation e il controllo di rilevanza, poi riallena. Lascia `faq.txt` al suo posto; la modalità generativa lo tratta come ulteriore testo del corpus.

Usa la search generativa per una copertura più ampia. Usa la search estrattiva quando ogni risposta deve essere approvata in anticipo, insieme a una soglia di similarità.

## 7. Testa una risposta generata

Il testo generato cambia da un'esecuzione all'altra, quindi non asserire la risposta esatta. Configura un LLM judge nell'esistente `e2e_tests/conftest.yml`:

```yaml
llm_judge:
  llm:
    provider: openai
    model: gpt-5-mini-2025-08-07
  embeddings:
    provider: openai
    model: text-embedding-3-large
```

Mantieni questo blocco in `e2e_tests/conftest.yml`. Il runner si ferma al primo `conftest.yml` che trova risalendo a partire dal file di test, quindi un secondo file nella root del progetto verrebbe ignorato.

Rasa raccomanda di usare provider diversi per il giudizio e per la generazione, così da ridurre il bias di auto-preferenza (self-preference bias). Questo progetto usa un solo provider perché il corso usa una sola API key. In produzione, usa provider separati.

Crea `e2e_tests/knowledge/knowledge_grounding.yml`:

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

`generative_response_is_grounded` verifica se la risposta è supportata da `ground_truth`. `generative_response_is_relevant` verifica se la risposta risponde effettivamente alla domanda. `utter_source` seleziona il componente la cui risposta viene giudicata.

Le soglie sono diverse perché i punteggi misurano cose differenti. La groundedness è la frazione di affermazioni supportate. La relevancy è un punteggio di similarità tra embedding. Una risposta valida ha ottenuto `0.67` nell'esecuzione registrata, quindi una soglia di relevancy di `0.9` era troppo alta. Calibra le soglie del judge sui risultati osservati.

Ogni assertion aggiunge chiamate al judge e quindi costi. Esegui l'intera suite due volte. Conferma che gli otto test esistenti e il nuovo test di knowledge passino in entrambe le esecuzioni.

## 8. Verifica finale

Prima di concludere, conferma che:

- le domande supportate restituiscano risposte grounded con le citation;
- le domande non supportate eseguano `pattern_cannot_handle`;
- una domanda di conoscenza possa mettere in pausa e riprendere un trasferimento;
- le richieste azionabili preferiscano ancora i flow alla search;
- tutti e nove i test end-to-end passino due volte.
