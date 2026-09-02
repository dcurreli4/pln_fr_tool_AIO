# HUB Tool - All-in-one

## 🔄 HUB Prod Sync

### Cosa fa
Sincronizza le tabelle dal database HUB Produzione verso Integration o Recette tramite tunnel SSH. Esegue TRUNCATE CASCADE + trasferimento bulk con cursore server-side a batch da 10.000 righe — senza caricare l'intera tabella in memoria.

### Tabelle sincronizzabili
Customer, Agreement, Sap filter contract, Identifier version map, Sap old plan map, Old agreement id map. Ogni tabella si abilita individualmente tramite le checkbox nel pannello sinistro.

### Stop
Il bottone ■ Stop interrompe l'operazione al termine del batch corrente, esegue rollback e chiude tutte le connessioni in modo pulito.

## 🐙 Kraken Data Extractor

### Modalità operative
**PRM** — Estrae dati a partire da coppie PRM / Kraken Account fornite manualmente.

**Identifier** — Parte da una lista di document identifier. Recupera le invoice su Kraken, estrae automaticamente le coppie PRM/Kraken Account e poi esegue i flussi secondari.

**Reference** — Parte da una lista di payment reference. Recupera i pagamenti, estrae le coppie PRM/Kraken Account e poi esegue i flussi secondari.

### Architettura connessioni
**Kraken DB** — Connessione diretta PostgreSQL al database sorgente (replica analytics).
**SSH Tunnel** — Tunnel sicuro verso Integration o Recette.
**HUB DB** — Lettura delle query SQL dalla tabella hub_config_query_kraken.

### File di input
PRM: input/kraken data extractor/data_input.txt
Identifier: input/kraken data extractor/data_input_identifier.txt
Reference: input/kraken data extractor/data_input_reference.txt

## 🔬 Kraken Full Data Extractor

### Cosa fa
Estrae dati full (senza filtri) da Kraken PROD e li carica direttamente su HUB PROD nelle tabelle j_kraken_*. Per ogni flow: TRUNCATE + estrazione Kraken + bulk insert su HUB con cursore server-side a batch da 10.000 righe.

### Tabelle estratte
Customer → j_kraken_customer
Agreement → j_kraken_agreement
Payment Plan (ELEC + GAS) → j_kraken_payment_plan
Renewal → j_kraken_renewal
Invoice (ELEC + GAS) → j_kraken_invoice
Payment (ELEC + GAS) → j_kraken_payments

### Tempi stimati
Dopo ogni esecuzione i tempi per flow vengono salvati nel .env (chiavi ADE_TIME_*) e mostrati accanto alle checkbox come previsione per i run futuri. Al passaggio del mouse appare un tooltip esplicativo.

### Connessioni
Usa le stesse credenziali HUB e Kraken già configurate. Le connessioni hanno TCP keepalive abilitato (idle 60s) per reggere query che durano oltre un'ora. Reconnect automatico se la connessione HUB cade durante il fetch. Il commento di ogni tabella viene aggiornato con la data dell'ultima estrazione riuscita.

## ⚡ Delta Recovery

### Cosa fa
Si connette al database HUB Produzione, estrae i pagamenti recuperabili da ztemp_pp_delta_payment_cluster (sub_cluster = SCARTO HUB) che hanno un match in payment_plans, li cerca nelle tabelle kraken ELE e GAS e inserisce i risultati in test_payments / test_payments_gas su Recette o Integration via tunnel SSH.

### Modalità operative
**NO_PAYMENT_PLAN_FOUND** — Pagamenti senza piano.

**MULTIPLE_PAYMENT_PLAN_FOUND_FOR_PAYMENT_DATE** — Pagamenti con più piani, risolti per conteggio.

**NO_PAYMENT_PLAN_FOUND_FOR_PAYMENT_DATE** — Pagamenti senza piano per la data specifica.

### Tab Query
Le query SQL per ogni modalità sono modificabili e validabili direttamente dall'interfaccia. Le modifiche vengono salvate nei file .sql in input/delta recovery/queries/. Se il file non esiste viene usato il fallback hardcoded.

## 🧹 Folder Cleaner

### Cosa fa
Elimina tutti i file e le sottocartelle dentro le cartelle configurate (non le cartelle stesse). La cancellazione dei file avviene in parallelo, le sottocartelle in sequenza con shutil.rmtree.

### Configurazione
Le cartelle da pulire sono elencate in input/folder cleaner/folders.txt. Si aggiungono tramite il bottone + e si rimuovono con la ✕ su ogni riga.

## 📦 Folder Mover

### Cosa fa
Copia tutti i file da una cartella sorgente a una cartella destinazione. La destinazione viene svuotata prima della copia. La copia è interrompibile.

### Configurazione
Le coppie sorgente → destinazione si configurano in input/folder mover/folders.txt. Si aggiungono tramite il bottone + selezionando prima la sorgente poi la destinazione. Sorgente e destinazione identiche vengono rifiutate. La ✕ su ogni riga rimuove quella coppia specifica.

## 🗜 ZIP Folder

### Cosa fa
Comprime le cartelle selezionate in file ZIP individuali usando la compressione DEFLATE. Il nome del file ZIP corrisponde al nome della cartella sorgente. L'output viene salvato in output/zip folder/.

### Filtro
È possibile filtrare i file da includere nello ZIP per sottostringa nel nome. Se il filtro è disabilitato, tutti i file vengono compressi.

### Configurazione
Le cartelle da comprimere sono elencate in input/zip folder/folders.txt. La cartella di output è configurabile dal campo Output nel pannello.

## 💳 File Filter

### Cosa fa
Gestisce due flussi distinti in tab separate: **Payment Plans** e **Invoice**. Ogni flusso filtra file CSV per le righe corrispondenti agli ID caricati nei file di filtro, produce i file filtrati e li comprime in un ZIP.

### Tab Payment Plans
Filtra file CSV con pattern K[EG]_PP_*.csv. Output in output/payment plans filter/. Chiavi di filtro disponibili: **Agreement ID**, **Prm + Kraken Account** (coppia prm;A-xxxxxxxx), **Agreement ID + Plan Type** (coppia id;M|C|R|U). L'opzione 'Trasforma file ;C; → ;U;' sostituisce il valore C con U nelle righe mantenute.

### Tab Invoice
Filtra file CSV invoice per **Identifier** (prefisso EB/GB) e **Prm + Kraken Account**. Output in output/invoice filter/. Il ZIP esistente viene eliminato automaticamente ad ogni run.

### File di filtro
Tutti i filtri si modificano dalla tab Filtro con validazione automatica per tipo e popup Modifica/Aggiungi condiviso tra le sezioni.

### Popup Modifica/Aggiungi
Tutte le sezioni usano lo stesso popup: textarea con evidenziazione in giallo delle righe non valide e messaggio d'errore contestuale al formato atteso.

## 📄 CSV Header Remover

### Cosa fa
Rimuove la prima riga da file CSV e TXT, ma solo se è completamente vuota (contiene esclusivamente caratteri di a capo: \n, \r\n o \r). Se la prima riga contiene qualsiasi contenuto, il file viene saltato.

### Output
I file processati vengono salvati in output/csv blank header remover/ con il suffisso _no_head aggiunto al nome originale. File molto grandi vengono gestiti a chunk da 64 MB senza caricarli in memoria.

### Configurazione
I file da processare si aggiungono tramite il bottone + e si rimuovono con la ✕ su ogni riga. La lista persiste in input/csv blank header remover/files.txt.

## 🧾 Invoice Writer

### Cosa fa
Replica il flusso Java InvoiceService: legge le invoice direttamente da Kraken (ELEC e GAS), filtrate per la lista di document identifier inserita nella tab Data Input, le valida e genera i CSV SAP + ZIP in output/invoice writer/.

### Data Input
File: input/invoice writer/data_input.csv
Colonne: IDENTIFIER ; IMPORT_SUPPLIER_BILL_ID ; AGREEMENT_ID
IDENTIFIER obbligatorio (prefisso EB/GB), esattamente uno tra i due campi piano. Il popup Modifica/Aggiungi valida ogni riga ed evidenzia in giallo quelle non valide o duplicate.

### Database
Usa le credenziali HUB e Kraken già configurate. Nessuna configurazione separata.

### Avvio
Esegue il flusso completo per ELEC e GAS in sequenza con log in tempo reale.

## 🎫 Jira Ticket Creator

### Cosa fa
Crea ticket Jira direttamente dall'interfaccia. Supporta autenticazione Basic, formattazione (bold, italic, link, liste), allegati drag & drop, template e importazione da ticket esistente tramite chiave o URL.

### Ambiente
Il toggle Prod / Chopin in alto a destra seleziona l'ambiente di destinazione. Influenza il percorso nel file .cfg (PE1 per Prod, CE1 per Chopin).

### Assegnatario
Il bottone Valida verifica l'esistenza dell'utente su Jira tramite API (/rest/api/2/user/search) prima di creare il ticket. Se l'utente non esiste il flusso viene bloccato con un messaggio nel log.

### File .cfg
La checkbox 'Crea file .cfg' prepopola i campi con valori fissi, li blocca in sola lettura e abilita il bottone 'Preview .cfg'. Il .cfg viene generato, allegato al ticket e salvato in output/jira ticket/cfg/. Togliendo la spunta i campi tornano modificabili e vuoti.

### Credenziali
JIRA_URL, JIRA_USERNAME, JIRA_PASSWORD salvati in config/.env. Modificabili anche da Impostazioni → Jira.

## ⚙ Configurazione

### Impostazioni
Tutte le credenziali e le impostazioni sono salvate in config/.env. Si modificano dalla sezione Impostazioni nella sidebar in basso a sinistra. I valori vengono salvati automaticamente al cambio di campo.

### Ambiente DB
Il toggle Integration / Recette in alto a destra è visibile solo nelle sezioni HUB Prod Sync, Kraken Data Extractor e Delta Recovery. La scelta viene ricordata al riavvio.

### Dipendenze
psycopg2-binary, python-dotenv, paramiko, sshtunnel, requests, tkinterdnd2. Installate automaticamente alla prima esecuzione tramite pip. La splash screen mostra l'avanzamento del caricamento ad ogni avvio.

### Keep-alive
All'avvio il tool imposta SetThreadExecutionState su Windows per impedire sleep, screensaver e spegnimento display. Viene rilasciato alla chiusura.
