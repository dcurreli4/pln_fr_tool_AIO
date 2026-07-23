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
