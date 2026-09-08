### v1.6.21 — 2026-09-08
- **Changelog**: stesso renderer dell'About — card per versione, `Label` con `wraplength` dinamico anti-loop, supporto `**bold**`
- **About / Changelog**: fix wraplength con `_last_w` — evita loop infinito su `<Configure>`
- **HUB Filter**: fix conteggio "Non trovati in nessuna tabella" — ora esclude correttamente chi è già nell'altra tabella (on_hold o sap_filter_contract)
- **HUB Filter — On Hold → Filtro**: fix `sap_list_supply_csv` — ora sovrascritto con `cluster + data` come nel flusso inverso
- **Payment Filter**: validazione esplicita proprietà vuote prima dell'avvio — messaggio di errore nel log con percorso Impostazioni → File Filter → Payments; default `PAY_OUTPUT_SUBFOLDER` aggiornato a `output/payment plans filter`

### v1.6.20 — 2026-09-04
- **HUB Filter — Filtro → On Hold**: implementata operazione di spostamento da `sap_filter_contract` a `sap_filter_contract_on_hold` — conteggi pre-operazione (da spostare, già in hold, non trovati), INSERT con `sap_list_supply_csv = cluster + data`, DELETE dalla sorgente, commit unico
- **HUB Filter — On Hold → Filtro**: implementata operazione inversa — ripristino da `sap_filter_contract_on_hold` a `sap_filter_contract` con stessa logica di conteggi e overwrite `sap_list_supply_csv`
- **HUB Filter**: rinominato da "HUB Filter Updater" a "HUB Filter"; aggiunta sidebar con radio button per selezionare operazione (Inserimento filtri / Filtro → On Hold / On Hold → Filtro)
- **File Filter — Plan ID**: chiave filtro "Agreement ID" rinominata "Plan ID" — ora usa fallback `agreement_id (col 0) OR sap_plan_id (col 12)` per gestire entrambi i formati; aggiunta colonna `PP_SAP_PLAN_ID_COL` in `_PP_DEFAULTS`
- **ABOUT.md**: creato file esterno con descrizione di tutti i tool — scaricato automaticamente insieme a `CHANGELOG.md` ad ogni aggiornamento

### v1.6.19 — 2026-08-12
- **File Filter — Invoice**: aggiunta sotto-tab "Prm + Kraken Account" con treeview a due colonne (PRM | Kraken Account), identica a Payment Plans Filter e Hub Filter Updater
- **File Filter — Invoice**: `zip_path.unlink()` all'avvio di ogni run — elimina lo ZIP esistente prima di rigenerarlo
- **Refactoring — PRM + Kraken Account**: estratto `_AppBase._prm_account_paste_popup` come metodo condiviso con validazione `_RE_PRM_ACCOUNT` (`^[A-Za-z0-9]+;A-[A-Za-z0-9]+$`) — usato da KrakenDataExtractor, FileFilter (Payment Plans + Invoice), HubFilterUpdater
- **Refactoring**: rimosso parametro `two_column` da `_paste_popup` — ora gestisce solo colonna singola (Identifier, Reference); il caso PRM + Kraken Account è delegato interamente a `_prm_account_paste_popup`
- **Validazione**: regex `_RE_PRM_ACCOUNT` aggiornata — il secondo campo deve iniziare con `A-` (es. `A-4441486C`); prefissi diversi non sono accettati
- **Refactoring — Canvas scroll**: `_AppBase._update_scroll(canvas, inner, vsb)` — auto show/hide scrollbar + scrollregion; tutti i metodi `_fc/fv/fm/zf/cbr_update_scroll` delegano a questo
- **Refactoring — Popup Modifica/Aggiungi**: `_AppBase._paste_popup` esteso con `validate_fn`, `load_existing_fn`, `insert_fn`, `undo` — tutti i popup (FileFilter, PaymentFilter, InvoiceWriter, InvFilter) ora usano il metodo condiviso
- **About**: contenuto spostato da codice statico a `ABOUT.md` — file esterno scaricabile ad ogni aggiornamento insieme a `CHANGELOG.md`

### v1.6.18 — 2026-08-11
- **Kraken Full Data Extractor**: aggiunto flusso "Allocation B2B" (ELEC + GAS) — delta load su `updated_at` verso `j_kraken_allocation_b2b`, query `B2B_ALLOCATION_PWR` / `B2B_ALLOCATION_GAS` da `hub_config_query_kraken`; rename `prm_id`/`pce_id` → `supply_point`, inserimento colonna `commodity`
- **Validator — Payment**: aggiunta regex `_PAY_BU_RE` per file Allocation B2B (prefisso `BU`) — riconosciuti e skippati; corretta regex `_PAY_B2B_RE` (prefisso `BC`, più permissiva su lunghezza segmenti)
- **Validator — Payment / Jira Ticket Creator**: implementata validazione B2B su `j_kraken_payments_b2b` — stesso flusso B2C, tabella parametrizzata in `_pay_check_hub`
- **`_pay_check_hub`**: fix estrazione reference — ora presa direttamente dalle tuple `(r, d, s)` invece che via regex sulla chiave stringa (evita parsing errato su reference contenenti `D` + cifre)
- **`_pay_check_hub`**: fix `payment_date` per B2B — cast `::date` prima di `::text` per eliminare l'orario (`2025-06-04 00:00:00` → `20250604`)
- **Hub Console**: reload flag immediato al cambio ambiente (poll ogni 2s su `TARGET_ENV`)

### v1.6.17 — 2026-08-11
- **Refactoring — Payment KJ/KH**: estratte `_kj_aggregate_lines`, `_kj_check_hub`, `_kh_aggregate_lines`, `_kh_check_hub` come funzioni condivise module-level (stesso pattern di `_pay_aggregate_lines`/`_pay_check_hub`)
- **Validator — Payment**: blocchi KJ e KH ora usano le funzioni condivise invece di logica inline
- **Jira Ticket Creator**: aggiunta validazione KJ (`j_cheque_energie_registrati`) e KH (`j_cheque_energie_utilizzati`) in `_jira_validate_payment_hub` tramite le stesse funzioni condivise

### v1.6.16 — 2026-08-10
- **Validator — Payment**: implementata validazione payment B2C — classifica file da nome (regex B2B/B2C/KH/KJ), aggrega per (reference, date, sign) separando PAYMENT e REJECT, cerca su `j_kraken_payments` con query `unnest` + JOIN ottimizzata con pre-filtro su `reference`/`payment_id`, confronta totali e logga chiavi mancanti con file sorgente
- **Validator — Payment**: file KH e KJ riconosciuti ma esclusi dalla validazione HUB (logga solo il conteggio)
- **Validator — Payment**: file B2B skippano la validazione HUB
- **Jira Ticket Creator**: aggiunta validazione payment su HUB prima della creazione ticket (flag `JIRA_VALIDATE_PAYMENT`, default abilitato) — stesso flusso del Validator ma legge da ZIP
- **Refactoring**: estratte `_pay_aggregate_lines` e `_pay_check_hub` come funzioni condivise tra Validator e Jira Ticket Creator
- **Jira Ticket Creator — Impostazioni**: aggiunto flag `JIRA_VALIDATE_PAYMENT` per abilitare/disabilitare la validazione payment su HUB
- **`_invoice_check_hub`**: fix parsing `template_vars_json` — ora prova prima `json.loads` (B2C, JSON standard) e poi `ast.literal_eval` (B2B, formato Python dict)
- **File Filter — Payments**: conteggio post-filtro mostra ora anche chiavi distinte (`x righe [y chiavi distinte]`)

### v1.6.15 — 2026-08-10
- **File Filter — Payments**: fix `NameError: name 'valid' is not defined` nel popup modifica chiavi Reference+Data+Tipo
- **File Filter — Payments**: messaggio errore chiavi non valide ora usa singolare/plurale corretto ("1 chiave non valida" / "N chiavi non valide")

### v1.6.14 — 2026-08-10
- **Kraken Full Data Extractor**: aggiunto flusso "Invoice B2B" (ELEC + GAS) — delta load su `finalized_at` verso `j_kraken_invoice_b2b`, query `B2B_INVOICE_ELEC` / `B2B_INVOICE_GAS` da `hub_config_query_kraken`
- **Validator / Jira Ticket Creator**: check HUB per fatture B2B ora usa `j_kraken_invoice_b2b`; campo importo `payment_amount` per KF, `gross_amount` per KM; fix parsing `template_vars_json` in formato Python dict (apici singoli) tramite `ast.literal_eval`
- **Validator**: aggiunto try/except esplicito attorno al check HUB per loggare errori invece di propagarli silenziosamente
- **Refactoring**: estratta `_invoice_check_hub` come funzione condivisa tra Validator e Jira Ticket Creator; connessione HUB aperta una sola volta per tutte le entry nel Validator

### v1.6.13 — 2026-08-07
- **Kraken Full Data Extractor — Payment**: introdotto delta load su `updated_at` (come Invoice su `finalized_at`) — cancella i record dell'ultimo giorno e ricarica da Kraken solo il delta; full load se la tabella è vuota; i flow ELEC e GAS sono gestiti separatamente tramite `commodity`

### v1.6.12 — 2026-08-07
- **HUB Console**: aggiunto tasto "▶ Avvia Run B2B" nella sezione B2B — alza il flag `B2B_SAP_INTEGRATION_IS_ACTIVE` su `hub_config_db`
- **HUB Console**: tasto "▶ Avvia Run B2C" spostato dentro la sezione B2C (era in fondo alla sidebar)

### v1.6.11 — 2026-08-07
- **HUB Console**: sezioni "Flussi B2C" e "Flussi B2B" ora a fisarmonica — solo una aperta alla volta; B2C aperta di default, B2B chiusa
- **HUB Console**: aggiunti flag B2B (`B2B_INVOICE_IS_ACTIVE`, `B2B_PAYMENT_IS_ACTIVE`, `B2B_ALLOCATION_IS_ACTIVE`)

### v1.6.10 — 2026-08-06
- **Jira Ticket Creator — Impostazioni**: aggiunta sezione "Assegnatari .cfg" con lista configurabile, radio per default e autocomplete live da API Jira (`/rest/api/2/user/search`) con debounce 300ms
- **Jira Ticket Creator — Impostazioni**: aggiunto flag `JIRA_VALIDATE_INVOICE` per abilitare/disabilitare la validazione invoice su HUB prima della creazione ticket (default: abilitata)
- **Jira Ticket Creator**: rimosso bottone "Valida" assegnatario — sostituito dall'autocomplete live sulla stessa API Jira
- **Jira Ticket Creator**: autocomplete assegnatario aggiunto anche nel form principale
- **Jira Ticket Creator**: in modalità `.cfg` l'assegnatario di default viene letto da `JIRA_CFG_ASSIGNEES_DEFAULT` invece di essere hardcoded
- **Jira Ticket Creator**: aggiunto blocco recap copiabile a fine creazione ticket (nome ticket + link + file per cartella destinazione)
- **Jira Ticket Creator**: log semplificato — rimossi messaggi ridondanti col recap finale
- **Jira Ticket Creator**: bottone "Rimuovi tutti" allegati sostituito con icona 🗑
- **Jira Ticket Creator**: layout 50/50 tra form e log (era 68/32)
- **Jira Ticket Creator**: tasto "Pulisci" ora deseleziona anche il checkbox `.cfg` e sblocca i campi
- **Jira Ticket Creator**: corretto spazio vuoto a destra dei bottoni Importa/Template nell'header card
- **Bonifica PROD — Agreement**: l'UPDATE degli agreement esistenti aggiorna ora anche il campo `urn`

### v1.6.9 — 2026-08-06
- **Bonifica PROD — Agreement**: l'UPDATE degli agreement esistenti aggiorna ora anche il campo `urn`

### v1.6.8 — 2026-08-05
- **File Filter — Payments / Payment Plans**: al termine del run con successo si apre automaticamente la cartella output in Esplora risorse
- **Popup migrazione .env**: altezza dinamica in base al numero di nuove variabili; testo su più righe leggibile; singolare/plurale corretto ("1 nuova variabile" / "N nuove variabili")

### v1.6.7 — 2026-08-04
- **File Filter** (ex Payment Plans Filter): rinominata l'etichetta della sezione in "File Filter"; il contenuto della tab "Pipeline" è stato spostato in una sotto-tab "Payment Plans", in preparazione della generalizzazione dello strumento ad altri tipi di file
- **File Filter**: la cartella `output/` con i CSV filtrati non compressi viene ora eliminata subito dopo la creazione dello ZIP (resta solo lo ZIP finale)
- **File Filter — Payments**: aggiunta sotto-tab "Payments" (in Pipeline, Filtro e Impostazioni), sorella di "Payment Plans" — filtra CSV di pagamento B2C per chiave "Reference" o "Reference + Data + Tipo (P/R)", ricalcola header (conteggio e somma importi) e produce lo ZIP filtrato
- **File Filter — Payments**: la tab Filtro ha due sotto-tab distinte ("Reference" e "Reference + Data + Tipo (P/R)"), ognuna con file di persistenza separato (`filter_payment_reference.txt` / `filter_payment_key_ref_date_type.txt`)
- **File Filter — Payments**: validazione chiavi nel popup modifica — Reference accetta solo `[A-Za-z0-9]`; Reference+Data+Tipo verifica il formato `R{ref}D{YYYYMMDD}T{PAYMENT|REJECT|""}`
- **File Filter — Payments**: drag & drop per selezionare la cartella input (una sola cartella); stessa funzionalità aggiunta anche a Payment Plans
- **File Filter — Payments**: al click ▶ verifica che la cartella contenga file B2C validi (pattern `K[EG]_XX_X_NNNNNNNNNN_YYYYMMDD.csv`); file B2B (BC/BU) bloccano con errore; errori loggati nel pannello output senza popup
- **File Filter — Payments**: fix ricalcolo header — somma importi body in euro (con virgola) e riformatta con 2 decimali e virgola, senza moltiplicazioni/divisioni
- **File Filter — Payment Plans**: output ZIP spostato in `output/file filter/payment plans filter/`
- **File Filter — Payment Plans**: al click ▶ verifica che la cartella contenga file `KE_PP_` / `KG_PP_`; errori loggati nel pannello output senza popup

### v1.6.6 — 2026-07-30
- **Payment Plans Filter**: generato file `output/payment plans filter/recovered_ids/recovered_ids.txt` con la lista degli agreement ID distinti mantenuti dal filtro

### v1.6.5 — 2026-07-30
- **Payment Plans Filter**: il riepilogo finale mostra ora gli agreement ID distinti mantenuti globalmente su tutti i file (non la somma dei distinti per file)

### v1.6.4 — 2026-07-30
- **Validator — Invoice / Jira Ticket Creator**: aggiunta distinzione B2C/B2B — le fatture B2B (EB2B/GB2B) saltano la validazione HUB, le B2C (EB2C/GB2C) vengono validate; reference miste B2C+B2B bloccano con errore

### v1.6.3 — 2026-07-30
- **Jira Ticket Creator**: aggiunta validazione invoice su HUB (`j_kraken_invoice`) prima della creazione ticket — verifica presenza reference EB/GB e confronto totale gross_amount per ogni ZIP; se fallisce il ticket non viene creato
- **Jira Ticket Creator**: validazione invoice eseguita anche in modalità DEBUG (specchio del flusso reale)
- **Jira Ticket Creator**: debug spostato in thread separato — l'interfaccia resta reattiva e i log arrivano in tempo reale
- **Validator — Invoice**: fix lettura file in ZIP con sottocartella (usato path completo invece del solo basename)
- **Validator — Invoice**: aggiunto messaggio di fine validazione (successo o errori)

### v1.6.2 — 2026-07-30
- **Validator — Invoice**: la verifica delle reference e il confronto degli importi ora interrogano direttamente `j_kraken_invoice` su HUB (eliminata la connessione a Kraken e il recupero query tramite `hub_config_query_kraken`)

### v1.6.1 — 2026-07-30
- **Kraken Full Data Extractor — Invoice**: rimossa la TRUNCATE, introdotto delta load — cancella solo i record con `finalized_at >= max(finalized_at)` per prefisso (EB/GB) e ricarica dal delta Kraken; se la tabella è vuota esegue full load

### v1.6.0 — 2026-07-30
- **Validator**: nuova sezione FILE — validatore di file con due modalità (Invoice, Payment)
- **Validator — Invoice**: valida cartelle e ZIP (KF, KR, KM, KK); controlla struttura, tipo file, assenza di mix tipologie; somma gli importi dalle testate; conta le reference distinte; verifica presenza su Kraken via query invoice (ELEC + GAS) e confronta il totale gross_amount
- **Validator**: drag & drop per cartelle e file ZIP; percorsi persistiti in `input/validator/folders.txt`

### v1.5.5 — 2026-07-24
- **ZIP Folder**: aggiunta drop zone drag & drop per aggiungere cartelle trascinandole direttamente
- **ZIP Folder**: apertura automatica cartella output nell'esplora risorse al termine della compressione
- **CSV Blank Header Remover**: aggiunta drop zone drag & drop per file .csv e .txt
- **CSV Blank Header Remover**: fix — file completamente vuoti vengono ora skippati con avviso invece di creare un output vuoto

### v1.5.4 — 2026-07-24
- **Jira Ticket Creator**: il link al ticket creato appare ora nel log come testo, rimosso il popup di conferma

### v1.5.3 — 2026-07-24
- **Payment Plans Filter**: zippatura accelerata con compresslevel=1 al posto del default DEFLATE

### v1.5.2 — 2026-07-24
- **Payment Plans Filter**: elaborazione file parallelizzata con 16 worker — tempo stimato da ~7 minuti a ~1 minuto su 600+ file

### v1.5.1 — 2026-07-23
- **About**: aggiunto bottone "📋 Changelog" che apre il pannello storico versioni
- **Changelog**: pannello con storico versioni, testo in grassetto, scrollabile
- **Update**: popup post-aggiornamento con le novità della versione appena installata

### v1.5.0 — 2026-07-23
- **Folder Cleaner**: aggiunta drop zone drag & drop per aggiungere cartelle trascinandole direttamente nell'interfaccia
- **Folder Cleaner**: cancellazione riscritta con scandir + ThreadPoolExecutor (64 worker per file, 16 per cartelle) — velocità notevolmente migliorata su grandi volumi
- **Kraken Full Data Extractor**: corretto hname Cheque Energie KJ (CHEQUE_ENERGIE_REGISTER)

### v1.4.12 — 2026-07-23
- **Kraken Full Data Extractor**: corretto hname per il flow Cheque Energie KJ (QUERY_CHEQUE_ENERGIE_REGISTER → CHEQUE_ENERGIE_REGISTER)

### v1.4.11 — 2026-07-20
- **Header**: aggiunto badge di aggiornamento disponibile con controllo periodico in background

### v1.4.10 — 2026-07-16
- **B2C**: aggiunto cleanup dei renewal prima dell'esecuzione del run B2C
- **Payment Plans Filter**: i file vengono ora saltati in modalità Agreement ID + Plan Type se il tipo non corrisponde

### v1.4.9 — 2026-07-16
- **Pagamenti**: aggiunti flow CE_KH e CE_KJ
- **ZIP**: bloccata la creazione di ZIP con nomi duplicati

### v1.4.8 — 2026-07-15
- **Jira**: aggiunto link cliccabile nel log dopo la creazione di un ticket
- **UI**: fix al padding delle tab nei notebook UHF e KDE in stato selezionato

### v1.4.7 — 2026-07-15
- **HubFilterUpdater**: abilitata la creazione batch
- **DB**: aggiunta insert sap_filter_contract
- Rinominati alcuni tool nell'interfaccia

### v1.4.6 — 2026-07-15
- **Kraken Data Extractor**: aggiunti flow Cheque Energie KJ e KH
- **Kraken Full Data Extractor**: fix alla sostituzione DATETOINSERT che preserva le keyword AND/WHERE
- **Kraken Data Extractor**: rimossa la colonna created_at dai flow invoice (PRM e Identifier)

### v1.4.5 — 2026-07-14
- Aggiunta migrazione automatica delle variabili .env all'aggiornamento

### v1.4.4 — 2026-07-14
- Bump tecnico (rilascio automatico su GitHub Actions)

### v1.4.3 — 2026-07-14
- **Setup**: aggiunto wizard di primo avvio che guida alla configurazione delle credenziali se .env non esiste

### v1.4.2 — 2026-07-14
- Aggiunto controllo aggiornamenti automatico all'avvio con download e installazione guidata della nuova versione

### v1.4.1 — 2026-07-14
- Aggiunto workflow GitHub Actions per la creazione automatica di tag e release ad ogni push su main

### v1.4.0 — 2026-07-14
- Importazione del progetto su Git
