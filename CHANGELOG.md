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
