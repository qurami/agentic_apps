# Cockburn Fully Dressed Use Case Template

> Compilare solo i campi utili al progetto. Mantenere il sistema descritto come black box e usare frasi brevi nella forma `Actor + active verb + result`.

## Use Case: `<ID> — <goal espresso con verbo attivo>`

**Goal in Context:**  
`<risultato che il Primary Actor vuole ottenere>`

**Scope:**  
`<System under Design considerato come black box>`

**Level:**  
`<Summary | User goal | Subfunction>`

**Primary Actor:**  
`<ruolo che avvia l'interazione per raggiungere il goal>`

**Supporting Actors:**  
`<sistemi o ruoli esterni che collaborano con il sistema>`

## Stakeholders & Interests

| Stakeholder | Interest da proteggere |
|---|---|
| `<ruolo o organizzazione>` | `<necessità, vincolo o risultato atteso>` |
|  |  |

## Preconditions

- `<condizione che deve essere già vera e che il use case non verifica>`

## Minimal Guarantees

- `<ciò che il sistema garantisce anche quando il goal non viene raggiunto>`

## Success Guarantees

- `<stato osservabile che deve essere vero quando il use case termina con successo>`

## Trigger

`<evento, richiesta o scadenza temporale che avvia il use case>`

## Main Success Scenario

1. `<Actor compie un'azione orientata al goal.>`
2. `<System risponde oppure acquisisce informazioni.>`
3. `<System valida ciò che deve proteggere.>`
4. `<Actor o System fa avanzare il processo.>`
5. `<System produce il Success Guarantee.>`

## Extensions

> Collegare ogni Extension al passo in cui la condizione viene rilevata. Scrivere la condizione come fatto, non come domanda.

- **2a.** `<condizione alternativa o di errore rilevata al passo 2>`
  1. `<azione di gestione>`
  2. `<ritorno al passo N | separate success | failure>`

- **\*a.** `<condizione che può verificarsi in qualsiasi passo>`
  1. `<azione di gestione>`
  2. `<esito>`

## Technology and Data Variations

> Inserire qui variazioni di tecnologia, formato o rappresentazione dei dati che non cambiano il comportamento.

- **3a.** `<variante tecnologica o dei dati relativa al passo 3>`

## Related Information

- **Priority:** `<valore>`
- **Frequency of use:** `<valore>`
- **Performance constraints:** `<valore>`
- **Open Issues:** `<decisioni ancora da prendere>`
- **Owner:** `<responsabile dell'approvazione>`
- **Last reviewed:** `<YYYY-MM-DD>`

## Sources

Template adattato da Alistair Cockburn, *Writing Effective Use Cases*:

- [Book extract hosted by the University of Zurich](https://www.ifi.uzh.ch/dam/jcr:00000000-25a0-3d08-0000-00000ce96422/weuc_extract.pdf)
- [Chapter 1 scan hosted by Carnegie Mellon University](http://www.cs.cmu.edu/~jhm/Readings/Cockburn%20Ch%201%20Scan.pdf)
