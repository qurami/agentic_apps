# Workflow compatto per scrivere un Cockburn Use Case

## 1. Fissa Scope e Level

- Nomina un solo **System under Design**.
- Decidi cosa è dentro e cosa è fuori dal **System boundary**.
- Scegli il **Level**: `Summary`, `User goal` o `Subfunction`.

## 2. Trova Primary Actor e goal

- Chi avvia l'interazione?
- Quale risultato vuole ottenere dal sistema?
- Titolo: breve frase con verbo attivo che esprime quel goal.

## 3. Elenca Stakeholders & Interests

- Chi è interessato al comportamento?
- Quale interesse deve proteggere il sistema?

## 4. Definisci le condizioni ai bordi

- **Preconditions:** ciò che deve essere già vero.
- **Minimal Guarantees:** ciò che resta protetto anche in caso di fallimento.
- **Success Guarantees:** stato osservabile prodotto dal successo.
- **Trigger:** evento che avvia il use case.

## 5. Scrivi il Main Success Scenario

- Preferibilmente 3–9 passi dal Trigger al Success Guarantee.
- Ogni passo nomina l'Actor e fa avanzare il processo.
- Descrivi intenti e risultati, non schermate, click o dettagli di implementazione.
- Mantieni il sistema come black box.

## 6. Aggiungi le Extensions

- Per ogni passo chiedi: «Cosa può accadere diversamente?»
- Numera rispetto al passo: `3a`, `3b`, `5a`.
- Scrivi una condizione rilevabile come fatto.
- Ogni Extension deve rientrare nel Main Success Scenario, raggiungere un separate success oppure terminare in failure.

## 7. Separa le semplici variazioni

- Formati, canali o tecnologie che non cambiano il comportamento vanno in **Technology and Data Variations**, non nelle Extensions.

## 8. Riesamina

- Primary Actor, goal e Success Guarantees sono coerenti?
- Il Scope è rispettato e il sistema può davvero produrre il risultato?
- Tutti gli Stakeholders & Interests sono protetti?
- Passi ed Extensions sono implementabili e verificabili?
- Voci con goal diversi vanno separate; semplici varianti diventano Extensions.

## 9. Solo dopo, deriva i Rasa Flow

- `description` dal goal e dallo Scope.
- `collect` dalle informazioni richieste.
- `action` dalle responsabilità del sistema e dalle integrations.
- branches dalle Extensions.
- conclusione dal Success Guarantee o dal Failure or handoff outcome.
- Non assumere una relazione uno-a-uno: un use case può richiedere più Flow o Flow riutilizzabili.

## Sources

- [Alistair Cockburn, *Writing Effective Use Cases* — extract](https://www.ifi.uzh.ch/dam/jcr:00000000-25a0-3d08-0000-00000ce96422/weuc_extract.pdf)
- [Alistair Cockburn, Chapter 1 scan](http://www.cs.cmu.edu/~jhm/Readings/Cockburn%20Ch%201%20Scan.pdf)
