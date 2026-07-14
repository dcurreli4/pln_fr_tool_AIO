# HUB Tool — All-in-One

Applicazione desktop Windows per il progetto **Plenitude Francia**. Raggruppa in un'unica interfaccia dark-themed tutti gli strumenti operativi usati dal team: sincronizzazione database, estrazione dati, gestione file, creazione ticket Jira e generazione fatture.

## Avvio

Doppio clic su `HUB Tool - All-in-one.pyw` (nessuna console). Le dipendenze mancanti vengono installate automaticamente al primo avvio.

## Strumenti disponibili

| Strumento | Descrizione |
|-----------|-------------|
| **HUB Console** | Console SQL interattiva sul database HUB (PostgreSQL) |
| **HUB Prod Sync** | Sincronizza tabelle da HUB Produzione verso INTEGRATION o RECETTE via SSH tunnel e bulk copy |
| **Kraken Data Extractor** | Estrae dati dal DB Kraken con query configurabili da file di input |
| **Analysis Data Extractor** | Estrazione dati per analisi ad hoc |
| **Delta Recovery** | Recupero delta su payment plans mancanti o non trovati per data, tramite query SQL predefinite |
| **Bonifica PROD** | Operazioni di bonifica (correzione dati) su produzione |
| **Folder Cleaner** | Svuota o pulisce cartelle secondo una lista configurabile |
| **Folder Mover** | Sposta cartelle o file secondo regole definite |
| **ZIP Folder** | Comprime cartelle in archivi ZIP |
| **Payment Plans Filter** | Filtra piani di pagamento per agreement ID, tipo piano o PRM/Kraken — output ZIP |
| **Jira Ticket Creator** | Crea ticket Jira da template JSON riutilizzabili |
| **CSV Blank Header Remover** | Rimuove colonne con header vuoto da file CSV |
| **Invoice Writer** | Genera fatture da dati CSV secondo template configurabili |

## Configurazione

Le credenziali e i parametri di connessione si impostano in `config/.env`:

- **HUB DB** — database PostgreSQL di produzione
- **Kraken DB** — database Kraken
- **Recette DB** — database Recette (accesso via SSH tunnel)
- **SSH Tunnel** — parametri per il tunnel verso INTEGRATION e RECETTE
- **Jira** — URL e credenziali per la creazione ticket
- **Payment Plans Filter** — colonne e cartelle di output

I file di input (liste di ID, query SQL, template) si trovano nella cartella `input/`.

## Dipendenze principali

- `psycopg2-binary` — connessioni PostgreSQL
- `paramiko==3.3.0` — SSH
- `sshtunnel` — tunnel SSH verso i DB remoti
- `python-dotenv` — lettura del file `.env`
- `requests` — chiamate HTTP (Jira)
- `tkinterdnd2` — drag & drop nell'interfaccia

## Requisiti

- Windows 10/11
- Python 3.x con `pip`
