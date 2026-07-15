# Cockburn Fully Dressed Use Case Template

## Use Case: `<ID> — <goal espresso con verbo attivo>`

**Goal in Context:**  
Richiedere informazioni su un accredito non ricevuto

**Scope:**  
- System Boundary: <rasa_endpoint>
- System Under Design: <rasa_agent>

**Level:**  
User goal

**Primary Actor:**  
<app_user>

**Supporting Actors:**  
- <chat_page>

## Stakeholders & Interests

| Stakeholder | Interest da proteggere |
|---|---|
| `<ruolo o organizzazione>` | `<necessità, vincolo o risultato atteso>` |
|  |  |

## Preconditions

- <app_user> ha utilizzato la <search_bar> senza trovare un intent 
- <chat_page> e' visualizzata

## Minimal Guarantees

- L'utente visualizza in app un deep link per accedere alla <transactions_list_page>

## Success Guarantees

- L'utente ha ricevuto informazioni su come contattare l'assistenza
- L'utente visualizza in app un deep link per accedere alla <transactions_list_page>

## Trigger

- <app_user> ha selezionato il pulsante <additional_help>
- il controller di <chat_page> e' aperto con <search_bar_text> e <search_bar_results> 

## Main Success Scenario

1. <rasa_agent> esegue <prefetch_user_intent> con <search_bar_text> e <search_bar_results> 
2. <rasa_agent> chiede <check_controllo_transazioni> (risposta si/no)
3. <app_user> risponde si
4. <rasa_agent> comunica <contatto_assistenza_transazioni> (contiene numero di telefono e info su CRO, data e importo)
5. <chat_page> visualizza deep link <transactions_list_page>

## Extensions

- **2a**: <rasa_agent> fa disambiguazione sulla richiesta di <app_user>
  1. <rasa_agent> chiede quale flow avviare
  2. <app_user> risponde comunicando richiesta informazioni accredito non ricevuto
  - prosegue su punto 2. originale

- **4a.** <app_user> risponde no 
  1. <rasa_agent> comunica <controllo_transazioni_preliminare> (contiene invito a controllare prima la lista di transazioni)
  2. <chat_page> visualizza deep link <transactions_list_page>