"""
GUI_-_launcher.pyw  —  Launcher unificato: HUB Prod Sync + Kraken Data Extractor.
Doppio clic per avviare su Windows (nessuna console).
"""

# ── Auto-install dipendenze ──────────────────────────────────────────────────
import importlib
import subprocess
import sys
import tkinter as _tk
import warnings
warnings.filterwarnings("ignore", message=".*InsecureRequestWarning.*")
warnings.filterwarnings("ignore", message=".*TripleDES.*")

# Imposta App User Model ID per staccarsi dall'icona di pythonw.exe nella taskbar
try:
    import ctypes as _ctypes
    _ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "Plenitude.HUBTool.Allinone.1")
except Exception:
    pass

# Titolo scuro per tutti i Toplevel su Windows 11



VERSION_LAUNCHER = "1.4.8"


_REQUIRED = {
    "psycopg2":    "psycopg2-binary",
    "dotenv":      "python-dotenv",
    "paramiko":    "paramiko==3.3.0",
    "sshtunnel":   "sshtunnel",
    "requests":    "requests",
    "tkinterdnd2": "tkinterdnd2",
}

# ── Splash screen ─────────────────────────────────────────────────────────────

class _Splash:
    """Splash screen visibile durante l'avvio — appare prima di tutto il resto."""

    def __init__(self):
        self._root = _tk.Tk()
        self._root.overrideredirect(True)
        self._root.configure(bg="#0f1117")
        self._root.attributes("-topmost", True)
        W, H = 380, 200
        x = (self._root.winfo_screenwidth()  - W) // 2
        y = (self._root.winfo_screenheight() - H) // 2
        self._root.geometry(f"{W}x{H}+{x}+{y}")

        # Bordo sottile
        outer = _tk.Frame(self._root, bg="#2a2d3e", bd=1)
        outer.pack(fill="both", expand=True, padx=1, pady=1)
        inner = _tk.Frame(outer, bg="#0f1117")
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Logo (HUB AIO)
        logo_row = _tk.Frame(inner, bg="#0f1117")
        logo_row.pack(pady=(28, 8))

        txt = _tk.Frame(logo_row, bg="#0f1117")
        txt.pack(side="left")
        _tk.Label(txt, text="HUB", font=("Consolas", 14, "bold"),
                  fg="#4f8ef7", bg="#0f1117", padx=0).pack(side="left", padx=0)
        _tk.Label(txt, text="|", font=("Consolas", 14),
                  fg="#2a2d3e", bg="#0f1117", padx=2).pack(side="left", padx=0)
        _tk.Label(txt, text="AIO", font=("Consolas", 14, "bold"),
                  fg="#f0f2ff", bg="#0f1117", padx=0).pack(side="left", padx=0)

        _tk.Frame(inner, bg="#2a2d3e", height=1).pack(fill="x", padx=24, pady=(8, 0))

        # Barra di avanzamento
        bar_bg = _tk.Frame(inner, bg="#1a1d27", height=4)
        bar_bg.pack(fill="x", padx=24, pady=(10, 0))
        bar_bg.pack_propagate(False)
        self._bar = _tk.Canvas(bar_bg, bg="#1a1d27", height=4,
                               highlightthickness=0, bd=0)
        self._bar.pack(fill="both", expand=True)
        self._bar_fill = self._bar.create_rectangle(
            0, 0, 0, 4, fill="#4f8ef7", outline="")

        # Messaggio di stato
        self._msg_var = _tk.StringVar(value="Avvio in corso...")
        _tk.Label(inner, textvariable=self._msg_var,
                  bg="#0f1117", fg="#8892b0",
                  font=("Consolas", 9), pady=8).pack()

        # Versione
        _tk.Label(inner, text=f"v{VERSION_LAUNCHER}",
                  bg="#0f1117", fg="#2a2d3e",
                  font=("Consolas", 8)).pack(side="bottom", pady=8)

        self._progress = 0.0
        self._root.update()

    def set(self, msg: str):
        self._msg_var.set(msg)
        self._root.update()

    def progress(self, value: float):
        """value tra 0.0 e 1.0"""
        self._progress = max(0.0, min(1.0, value))
        self._root.update_idletasks()
        w = self._bar.winfo_width()
        self._bar.coords(self._bar_fill, 0, 0, int(w * self._progress), 4)
        self._root.update()

    def destroy(self):
        self._root.destroy()


_splash = _Splash()
_splash.set("Verifica dipendenze...")
_splash.progress(0.05)

try:
    from tkinterdnd2 import TkinterDnD as _TkDnD, DND_FILES as _DND_FILES
    _HAS_DND = True
except Exception:
    _TkDnD   = None
    _DND_FILES = None
    _HAS_DND  = False

_N_DEPS = len(_REQUIRED)

def _ensure_dependencies():
    missing = []
    for i, (module, package) in enumerate(_REQUIRED.items(), 1):
        _splash.set(f"Caricamento {module}...")
        _splash.progress(i / (_N_DEPS + 2))
        try:
            importlib.import_module(module)
            if module == "paramiko":
                import paramiko as _pm
                ver_str = _pm.__version__
                ver = tuple(int(x) for x in ver_str.split(".")[:2])
                if ver >= (3, 4):
                    missing.append((module, package))
                # Se è già <=3.3.x non fa nulla
        except ImportError:
            missing.append((module, package))
    if not missing:
        return

    failed = []
    for i, (module, package) in enumerate(missing, 1):
        _splash.set(f"Installazione {package} ({i}/{len(missing)})...")
        _splash.progress(i / (len(missing) + 1))
        result = subprocess.run([sys.executable, "-m", "pip", "install", package],
                                capture_output=True, text=True)
        if result.returncode != 0:
            failed.append(package)

    if failed:
        _splash.set(f"\u2717 Installazione fallita: {', '.join(failed)}")
        import tkinter.messagebox as _mb
        _mb.showerror(
            "Errore installazione",
            "Impossibile installare:\n\n  \u2022 " + "\n  \u2022 ".join(failed) +
            f"\n\nEsegui manualmente:\n  pip install {' '.join(failed)}"
        )
        sys.exit(1)
_ensure_dependencies()

# ── Controllo aggiornamenti ──────────────────────────────────────────────────
_UPDATE_INFO = None  # (latest_version, download_url) oppure None

def _check_update_available():
    global _UPDATE_INFO
    try:
        import requests as _req
        resp = _req.get(
            "https://api.github.com/repos/dcurreli4/pln_fr_tool_AIO/releases/latest",
            timeout=5,
        )
        if resp.status_code != 200:
            return
        data = resp.json()
        tag = data.get("tag_name", "")
        latest = tag.lstrip("v")
        if not latest:
            return
        def _vtuple(v):
            try:
                return tuple(int(x) for x in v.split("."))
            except Exception:
                return (0,)
        if _vtuple(latest) > _vtuple(VERSION_LAUNCHER):
            assets = data.get("assets", [])
            url = next(
                (a["browser_download_url"] for a in assets if a["name"].endswith(".pyw")),
                None,
            )
            if url:
                _UPDATE_INFO = (latest, url)
    except Exception:
        pass

_splash.set("Controllo aggiornamenti...")
_splash.progress((_N_DEPS + 1) / (_N_DEPS + 2))
_check_update_available()

_splash.set("Caricamento interfaccia...")
_splash.progress(1.0)

# ── Fine auto-install ────────────────────────────────────────────────────────

# ── Colori ───────────────────────────────────────────────────────────────────
BG       = "#0f1117"
BG_CARD  = "#1a1d27"
BG_CARD2 = "#141720"
BG_HOVER = "#22263a"
BG_INPUT = "#0d1020"
ACCENT   = "#4f8ef7"
ACCENT2  = "#7c3aed"
SUCCESS  = "#22c55e"
WARNING  = "#f59e0b"
ERROR    = "#ef4444"
TEXT_PRI = "#f0f2ff"
TEXT_SEC = "#8892b0"
BORDER   = "#2a2d3e"


def _setup_scrollbar_style():
    """Configura lo stile ttk Dark per le scrollbar — chiamata una volta sola."""
    from tkinter import ttk
    s = ttk.Style()
    s.theme_use("clam")
    for name in ("Dark.Vertical.TScrollbar", "Dark.Horizontal.TScrollbar"):
        s.configure(name,
                    background=BORDER, troughcolor=BG_CARD,
                    arrowcolor=TEXT_SEC, bordercolor=BG_CARD,
                    darkcolor=BG_CARD, lightcolor=BG_CARD,
                    relief="flat", arrowsize=12)
        s.map(name, background=[("active", TEXT_SEC), ("pressed", ACCENT)])


def _get_target_env() -> str:
    """Legge l'ambiente selezionato dal .env — sempre uppercase: INTEGRATION | RECETTE."""
    val = _read_env_raw().get("TARGET_ENV", "INTEGRATION").upper()
    return val if val in ("INTEGRATION", "RECETTE") else "INTEGRATION"



def _read_env_raw() -> dict:
    result = {}
    if not _ENV.exists():
        return result
    for line in _ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip().strip('"').strip("'")
    return result


def _write_env(data: dict):
    if _ENV.exists():
        original = _ENV.read_text(encoding="utf-8").splitlines()
    else:
        original = []
    updated_keys = set()
    new_lines = []
    for line in original:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k = stripped.partition("=")[0].strip()
            if k in data:
                new_lines.append(f'{k}={data[k]}')
                updated_keys.add(k)
                continue
        new_lines.append(line)
    for k, v in data.items():
        if k not in updated_keys:
            new_lines.append(f'{k}={v}')
    _ENV.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def get_hub_connection():
    import psycopg2
    required = ["HUB_HOST", "HUB_PORT", "HUB_NAME", "HUB_USER", "HUB_PASSWORD"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        raise EnvironmentError(f"Variabili d'ambiente mancanti (HUB): {', '.join(missing)}")
    return psycopg2.connect(
        host=os.getenv("HUB_HOST"),
        port=int(os.getenv("HUB_PORT", "5432")),
        dbname=os.getenv("HUB_NAME"),
        user=os.getenv("HUB_USER"),
        password=os.getenv("HUB_PASSWORD"),
    )


# ════════════════════════════════════════════════════════════════════════════
# CLASSE BASE — metodi condivisi da tutte le app
# ════════════════════════════════════════════════════════════════════════════


# ════════════════════════════════════════════════════════════════════════════
# HUB PROD SYNC
# ════════════════════════════════════════════════════════════════════════════


import os
import queue
import threading
import tkinter
from pathlib import Path
from tkinter import Frame, Label, Scrollbar, StringVar, Text, Tk, ttk
from tkinter import messagebox, filedialog
from dotenv import load_dotenv

_HERE   = Path(__file__).parent
_ENV    = _HERE / "config" / ".env"

load_dotenv(dotenv_path=_ENV)


# ── Impostazioni — campi .env (usate da entrambe le app e dalla finestra ⚙) ──
SETTINGS_TABS = [
    ("🗄  Database", [
        ("HUB DB  (Produzione)", [
            ("HUB_HOST",     "Host",     False),
            ("HUB_PORT",     "Port",     False),
            ("HUB_NAME",     "Database", False),
            ("HUB_USER",     "Utente",   False),
            ("HUB_PASSWORD", "Password", True),
        ]),
        ("Kraken DB", [
            ("KRAKEN_HOST",     "Host",     False),
            ("KRAKEN_PORT",     "Port",     False),
            ("KRAKEN_NAME",     "Database", False),
            ("KRAKEN_USER",     "Utente",   False),
            ("KRAKEN_PASSWORD", "Password", True),
        ]),
        ("Recette DB  (via SSH)", [
            ("RECETTE_HOST",     "Host",     False),
            ("RECETTE_PORT",     "Port",     False),
            ("RECETTE_NAME",     "Database", False),
            ("RECETTE_USER",     "Utente",   False),
            ("RECETTE_PASSWORD", "Password", True),
        ]),
        ("SSH Tunnel", [
            ("SSH_HOST",         "Host Integration",   False),
            ("SSH_RECETTE_HOST", "Host Recette",       False),
            ("SSH_PORT",         "Port",               False),
            ("SSH_USER",         "Utente",             False),
            ("SSH_KEY_PATH",     "Percorso .pem/.ppk", False),
        ]),
    ]),
    ("🔄  HUB Prod Sync", [
        ("Tabelle", [
            ("CUSTOMER_TABLE",                   "Customer",            False),
            ("AGREEMENT_TABLE",                 "Agreement",           False),
            ("SAP_FILTER_CONTRACT_TABLE", "Sap filter contract", False),
            ("SAP_FILTER_CONTRACT_BATCH_TABLE", "Sap filter batch", False),
            ("IDENTIFIER_VERSION_TABLE", "Identifier version map", False),
            ("SAP_OLD_PLAN_TABLE",           "Sap old plan map",    False),
            ("OLD_AGREEMENT_ID_MAP_TABLE", "Old agreement id map", False),
        ]),
    ]),
    ("🎫  Jira", [
        ("Credenziali", [
            ("JIRA_URL",      "URL",       False),
            ("JIRA_USERNAME", "Username",  False),
            ("JIRA_PASSWORD", "Password",  True),
        ]),
    ]),
    ("💳  Payment Plans Filter", [
        ("Impostazioni", [
            ("PP_OUTPUT_SUBFOLDER",  "Sottocartella output",  False),
            ("PP_ZIP_FILENAME",      "Nome ZIP",              False),
            ("PP_AGREEMENT_ID_COL",  "Agreement ID col",      False),
            ("PP_NUMBER_COL",        "Number col",            False),
            ("PP_SUPPLY_CODE_COL",   "Supply Code col",       False),
            ("PP_PLAN_TYPE_ID_COL",  "Plan Type ID col",      False),
            ("PP_PROGRESS_INTERVAL", "Intervallo progresso",  False),
        ]),
    ]),
]

# Mantieni SETTINGS_SECTIONS per compatibilità con codice esistente
SETTINGS_SECTIONS = [
    (section_title, fields)
    for _, tab_sections in SETTINGS_TABS
    for section_title, fields in tab_sections
]
ENV_TARGETS = ["Recette", "Integration"]


# ════════════════════════════════════════════════════════════════════════════
# LOGICA PIPELINE
# ════════════════════════════════════════════════════════════════════════════

def _reload_env():
    load_dotenv(dotenv_path=_ENV, override=True)




def hub_open_ssh_tunnel(target: str = "INTEGRATION"):
    from sshtunnel import SSHTunnelForwarder
    prefix = "RECETTE" if target == "RECETTE" else "INTEGRATION"
    ssh_host = os.getenv("SSH_RECETTE_HOST" if target == "RECETTE" else "SSH_HOST")

    required = ["SSH_PORT", "SSH_USER", "SSH_KEY_PATH",
                "SSH_RECETTE_HOST" if target == "RECETTE" else "SSH_HOST",
                f"{prefix}_HOST", f"{prefix}_NAME",
                f"{prefix}_USER", f"{prefix}_PASSWORD"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        raise EnvironmentError(f"Variabili mancanti (SSH/{target}): {', '.join(missing)}")
    tunnel = SSHTunnelForwarder(
        (ssh_host, int(os.getenv("SSH_PORT", "22"))),
        ssh_username=os.getenv("SSH_USER"),
        ssh_pkey=os.getenv("SSH_KEY_PATH"),
        remote_bind_address=(os.getenv(f"{prefix}_HOST"),
                             int(os.getenv(f"{prefix}_PORT", "5432"))),
    )
    tunnel.start()
    return tunnel


def get_target_connection(tunnel, target: str):
    import psycopg2
    prefix = "RECETTE" if target == "RECETTE" else "INTEGRATION"
    return psycopg2.connect(
        host="127.0.0.1",
        port=tunnel.local_bind_port,
        dbname=os.getenv(f"{prefix}_NAME"),
        user=os.getenv(f"{prefix}_USER"),
        password=os.getenv(f"{prefix}_PASSWORD"),
    )


def hub_run_pipeline(target: str, app, log, on_done, sync_customer: bool = True, sync_agreement: bool = True, sync_sap_filter: bool = False, sync_identifier_version: bool = False, sync_sap_old_plan: bool = False, sync_old_agreement_id_map: bool = False):
    import psycopg2
    from io import StringIO
    import csv as _csv

    _reload_env()

    prefix = "RECETTE" if target == "RECETTE" else "INTEGRATION"
    customer_src           = os.getenv("CUSTOMER_TABLE",                  "customer")
    customer_tgt           = customer_src
    agreement_src          = os.getenv("AGREEMENT_TABLE",                 "agreement")
    agreement_tgt          = agreement_src
    sap_filter_src         = os.getenv("SAP_FILTER_CONTRACT_TABLE",       "sap_filter_contract")
    sap_filter_tgt         = sap_filter_src
    sap_batch_src          = os.getenv("SAP_FILTER_CONTRACT_BATCH_TABLE", "sap_filter_contract_batch")
    sap_batch_tgt          = sap_batch_src
    id_version_src         = os.getenv("IDENTIFIER_VERSION_TABLE",        "identifier_version_map")
    id_version_tgt         = id_version_src
    sap_old_plan_src       = os.getenv("SAP_OLD_PLAN_TABLE",              "sap_old_plan_map")
    sap_old_plan_tgt       = sap_old_plan_src
    old_agreement_src      = os.getenv("OLD_AGREEMENT_ID_MAP_TABLE",      "old_agreement_id_map")
    old_agreement_tgt      = old_agreement_src

    def _bulk_transfer(hub_conn, int_conn, src_table, tgt_table, do_truncate=True, cascade_source=None):
        """Trasferisce una tabella da HUB a Integration via bulk copy."""
        if do_truncate:
            log(f"\n[INFO] Truncate CASCADE '{tgt_table}' ...", "info")
            cur = int_conn.cursor()
            try:
                cur.execute(f"TRUNCATE TABLE {tgt_table} CASCADE;")
                int_conn.commit()
                cur.close()
                log(f"[OK] Truncate CASCADE eseguito.", "ok")
            except psycopg2.Error as e:
                int_conn.rollback(); cur.close()
                raise e
        else:
            _cascade = cascade_source or "tabella padre"
            log(f"\n[INFO] '{tgt_table}' — truncate non necessaria (già eliminata dalla CASCADE su {_cascade}).", "info")

        log(f"[INFO] Estrazione bulk da '{src_table}' ...", "info")
        hub_cur_meta = hub_conn.cursor()
        hub_cur_meta.execute(f"SELECT COUNT(*) FROM {src_table}")
        total_count = hub_cur_meta.fetchone()[0]
        hub_cur_meta.execute(f"SELECT * FROM {src_table} LIMIT 0")
        columns = [d[0] for d in hub_cur_meta.description]
        hub_cur_meta.close()
        log(f"[INFO] {src_table}: {total_count} righe totali da trasferire.", "info")

        hub_cur = hub_conn.cursor(f"bulk_cursor_{src_table}")
        hub_cur.execute(f"SELECT * FROM {src_table}")

        import time
        BATCH_SIZE   = 10000
        LOG_INTERVAL = 100000
        total_rows   = 0
        int_cur = int_conn.cursor()
        start_time = time.time()

        while True:
            if app._stop_requested:
                log("[WARN] Stop richiesto — operazione annullata, rollback in corso ...", "warn")
                int_conn.rollback()
                hub_cur.close()
                int_cur.close()
                raise InterruptedError("Stop richiesto dall'utente.")
            rows = hub_cur.fetchmany(BATCH_SIZE)
            if not rows:
                break
            buffer = StringIO()
            writer = _csv.writer(buffer, delimiter="\t",
                                 quotechar="\x01", quoting=_csv.QUOTE_MINIMAL)
            for row in rows:
                writer.writerow([
                    "\x02NULL\x02" if v is None else ("" if v == "" else v)
                    for v in row
                ])
            buffer.seek(0)
            cols = ", ".join(columns)
            int_cur.copy_expert(
                f"COPY {tgt_table} ({cols}) FROM STDIN WITH "
                f"(FORMAT CSV, DELIMITER E'\\t', QUOTE E'\\x01', NULL E'\\x02NULL\\x02')",
                buffer,
            )
            total_rows += len(rows)
            if total_rows % LOG_INTERVAL == 0 or total_rows == total_count:
                pct = round(total_rows / total_count * 100) if total_count else 0
                log(f"[INFO] {tgt_table}: {total_rows}/{total_count} righe inserite ({pct}%) ...", "info")

        int_conn.commit()
        hub_cur.close()
        int_cur.close()
        elapsed = time.time() - start_time
        mins, secs = divmod(int(elapsed), 60)
        elapsed_str = f"{mins}m {secs}s" if mins else f"{secs}s"
        log(f"[OK] {total_rows} righe inserite in '{tgt_table}' in {elapsed_str}", "ok")

    try:
        # Connessione HUB
        log(f"[INFO] Connessione HUB: {os.getenv('HUB_HOST')} / {os.getenv('HUB_NAME')} ...", "info")
        try:
            hub_conn = get_hub_connection()
            log("[INFO] Connessione HUB attiva ✓", "ok")
        except (psycopg2.OperationalError, EnvironmentError) as e:
            log(f"[ERRORE] Connessione HUB fallita: {e}", "error")
            on_done(success=False); return

        # Tunnel SSH
        log(f"\n[INFO] Apertura tunnel SSH verso {os.getenv('SSH_RECETTE_HOST' if target == 'RECETTE' else 'SSH_HOST')} ...", "info")
        try:
            tunnel = hub_open_ssh_tunnel(target)
            log(f"[INFO] Tunnel attivo su porta locale {tunnel.local_bind_port}", "info")
        except Exception as e:
            log(f"[ERRORE] Tunnel SSH fallito: {e}", "error")
            hub_conn.close(); on_done(success=False); return

        # Connessione destinazione
        log(f"\n[INFO] Connessione {target}: {os.getenv(f'{prefix}_HOST')} ...", "info")
        try:
            int_conn = get_target_connection(tunnel, target)
            log(f"[INFO] Connessione {target} attiva ✓", "ok")
        except psycopg2.OperationalError as e:
            log(f"[ERRORE] Connessione {target} fallita: {e}", "error")
            hub_conn.close(); tunnel.stop(); on_done(success=False); return

        # ── Guardia di sicurezza ─────────────────────────────────────────
        hub_host = (os.getenv("HUB_HOST", "").strip().lower(),
                    os.getenv("HUB_NAME", "").strip().lower())
        tgt_host = (os.getenv(f"{prefix}_HOST", "").strip().lower(),
                    os.getenv(f"{prefix}_NAME", "").strip().lower())

        if hub_host == tgt_host:
            log(f"[ERRORE CRITICO] HUB e {target} puntano allo stesso host+database.", "error")
            log("[ERRORE CRITICO] Truncate CASCADE bloccato per sicurezza.", "error")
            hub_conn.close(); int_conn.close(); tunnel.stop(); on_done(success=False); return

        if not os.getenv(f"{prefix}_HOST", ""):
            log(f"[ERRORE CRITICO] {prefix}_HOST non configurato — operazione bloccata.", "error")
            hub_conn.close(); int_conn.close(); tunnel.stop(); on_done(success=False); return
        # ── Fine guardia ─────────────────────────────────────────────────

        # Guardia: almeno una tabella deve essere selezionata
        if not sync_customer and not sync_agreement and not sync_sap_filter \
                and not sync_identifier_version and not sync_sap_old_plan \
                and not sync_old_agreement_id_map:
            log("[WARN] Nessuna tabella selezionata — operazione annullata.", "warn")
            hub_conn.close(); int_conn.close(); tunnel.stop(); on_done(success=False); return

        import time
        total_start = time.time()

        # 1. Customer
        if sync_customer:
            log("\n── Customer ──", "section")
            _bulk_transfer(hub_conn, int_conn, customer_src, customer_tgt, do_truncate=True)
        else:
            log("\n[INFO] Customer skippato (checkbox disabilitata).", "info")

        # 2. Agreement
        if sync_agreement:
            needs_truncate = not sync_customer
            log("\n── Agreement ──", "section")
            _bulk_transfer(hub_conn, int_conn, agreement_src, agreement_tgt,
                           do_truncate=needs_truncate, cascade_source=customer_tgt)
        else:
            log("\n[INFO] Agreement skippato (checkbox disabilitata).", "info")

        # 3. Sap filter contract
        if sync_sap_filter:
            log("\n── Sap filter contract ──", "section")
            _bulk_transfer(hub_conn, int_conn, sap_batch_src, sap_batch_tgt, do_truncate=True)
            _bulk_transfer(hub_conn, int_conn, sap_filter_src, sap_filter_tgt,
                           do_truncate=False, cascade_source=sap_batch_tgt)
        else:
            log("\n[INFO] Sap filter contract skippato (checkbox disabilitata).", "info")

        # 4. Identifier version map
        if sync_identifier_version:
            log("\n── Identifier version map ──", "section")
            _bulk_transfer(hub_conn, int_conn, id_version_src, id_version_tgt, do_truncate=True)
        else:
            log("\n[INFO] Identifier version map skippato (checkbox disabilitata).", "info")

        # 5. Sap old plan map
        if sync_sap_old_plan:
            log("\n── Sap old plan map ──", "section")
            _bulk_transfer(hub_conn, int_conn, sap_old_plan_src, sap_old_plan_tgt, do_truncate=True)
        else:
            log("\n[INFO] Sap old plan map skippato (checkbox disabilitata).", "info")

        # 6. Old agreement id map
        if sync_old_agreement_id_map:
            log("\n── Old agreement id map ──", "section")
            _bulk_transfer(hub_conn, int_conn, old_agreement_src, old_agreement_tgt, do_truncate=True)
        else:
            log("\n[INFO] Old agreement id map skippato (checkbox disabilitata).", "info")

        hub_conn.close()
        int_conn.close()
        tunnel.stop()

        total_elapsed = time.time() - total_start
        mins, secs = divmod(int(total_elapsed), 60)
        total_str = f"{mins}m {secs}s" if mins else f"{secs}s"
        log(f"\n[INFO] Sincronizzazione completata con successo in {total_str}.", "ok")
        on_done(success=True)

    except InterruptedError as e:
        log(f"\n[WARN] {e}", "warn")
        try:
            hub_conn.close()
        except Exception:
            pass
        try:
            int_conn.close()
        except Exception:
            pass
        try:
            tunnel.stop()
        except Exception:
            pass
        on_done(success=False)
    except Exception as e:
        import traceback
        log(f"\n[ERRORE CRITICO] {e}", "error")
        for line in traceback.format_exc().splitlines():
            log(f"  {line}", "error")
        on_done(success=False)


# ════════════════════════════════════════════════════════════════════════════
# ENV helpers
# ════════════════════════════════════════════════════════════════════════════








class _AppBase(tkinter.Frame):
    """Classe base con metodi UI condivisi da HubProdSync e KrakenDataExtractor."""

    def _warn_status(self, msg: str, duration: int = 3000):
        """Mostra un avviso giallo nella status bar, poi ripristina."""
        if hasattr(self, "_status_lbl"):
            self._status_lbl.configure(fg=WARNING)
        self._status_var.set(msg)
        def _reset():
            self._status_var.set("Pronto.")
            if hasattr(self, "_status_lbl"):
                self._status_lbl.configure(fg=TEXT_SEC)
        self.after(duration, _reset)

    def _check_duplicate(self, path: str, data: list) -> bool:
        """Ritorna True e mostra warning se path è già in data."""
        if path in data:
            self._warn_status("⚠ Percorso già presente nella lista.")
            return True
        return False


    def _clear_log(self):
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    def _make_btn(self, parent, text, command, color=ACCENT):
        btn = Label(parent, text=text, bg=BG_CARD, fg=color,
                    font=("Consolas", 10, "bold"), cursor="hand2",
                    pady=8, padx=10, relief="flat")
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>",    lambda e: btn.configure(bg=BG_HOVER))
        btn.bind("<Leave>",    lambda e: btn.configure(bg=BG_CARD))
        return btn


    def _build_notebook(self, tabs: list, extra_styles: dict = None):
        """Crea il notebook Dark con le tab fornite. Ritorna il notebook.
        tabs: lista di (label, builder_method)
        extra_styles: dict opzionale di stili ttk aggiuntivi {name: {key: val}}
        """
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TNotebook",
                        background=BG, borderwidth=0, tabmargins=[0, 0, 0, 0])
        style.configure("Dark.TNotebook.Tab",
                        background=BG_CARD, foreground=TEXT_SEC,
                        font=("Consolas", 10), padding=[16, 4], borderwidth=0)
        style.map("Dark.TNotebook.Tab",
                  background=[("selected", BG_CARD2), ("!selected", BG_CARD)],
                  foreground=[("selected", TEXT_PRI), ("!selected", TEXT_SEC)],
                  padding=[("selected", [16, 7]), ("!selected", [16, 4])])
        if extra_styles:
            for style_name, config in extra_styles.items():
                style.configure(style_name, **config)
                if "map" in config:
                    style.map(style_name, **config["map"])

        nb = ttk.Notebook(self, style="Dark.TNotebook")
        nb.pack(fill="both", expand=True, padx=24, pady=(12, 0))
        for label, builder in tabs:
            tab = Frame(nb, bg=BG)
            nb.add(tab, text=label)
            builder(tab)
        return nb

    def _build_panel_layout(self, parent, left_width: int = 200):
        """Crea il layout a due colonne sinistra/destra. Ritorna (left, right)."""
        body = Frame(parent, bg=BG)
        body.pack(fill="both", expand=True)
        paned = Frame(body, bg=BG)
        paned.pack(fill="both", expand=True)
        left = Frame(paned, bg=BG_CARD, bd=0, highlightthickness=1,
                     highlightbackground=BORDER, width=left_width)
        left.pack(side="left", fill="y", padx=(0, 6))
        left.pack_propagate(False)
        right = Frame(paned, bg=BG_CARD, bd=0, highlightthickness=1,
                      highlightbackground=BORDER)
        right.pack(side="left", fill="both", expand=True)
        return left, right

    def _build_log_panel(self, parent, on_clear=None):
        """Costruisce il pannello OUTPUT LOG — identico in tutte le app.
        Se on_clear è passato, mostra un'icona 🗑 nella testata per pulire il log."""
        hdr = Frame(parent, bg=BG_CARD)
        hdr.pack(fill="x")
        Label(hdr, text="OUTPUT LOG", bg=BG_CARD, fg=TEXT_SEC,
              font=("Consolas", 9, "bold"), pady=10, padx=14).pack(side="left")
        if on_clear:
            icon = Label(hdr, text="🗑", bg=BG_CARD, fg=TEXT_SEC,
                         font=("Consolas", 11), cursor="hand2", padx=10)
            icon.bind("<Button-1>", lambda e: on_clear())
            icon.bind("<Enter>",    lambda e: icon.configure(fg=ERROR))
            icon.bind("<Leave>",    lambda e: icon.configure(fg=TEXT_SEC))
            icon.pack(side="right")
        Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=14)

        lf = Frame(parent, bg=BG_CARD)
        lf.pack(fill="both", expand=True, padx=4, pady=4)
        log_vsb = ttk.Scrollbar(lf, style="Dark.Vertical.TScrollbar")
        log_vsb.pack(side="right", fill="y")

        def _log_scroll_set(first, last):
            if float(first) <= 0.0 and float(last) >= 1.0:
                if log_vsb.winfo_ismapped():
                    log_vsb.pack_forget()
            else:
                if not log_vsb.winfo_ismapped():
                    log_vsb.pack(side="right", fill="y")
            log_vsb.set(first, last)
        self._log_box = Text(
            lf, bg=BG_CARD, fg=TEXT_PRI, font=("Consolas", 10),
            insertbackground=ACCENT, relief="flat", bd=0,
            yscrollcommand=_log_scroll_set, state="disabled",
            wrap="word", padx=10, pady=6, selectbackground=ACCENT2,
        )
        self._log_box.pack(side="left", fill="both", expand=True)
        log_vsb.config(command=self._log_box.yview)

        self._log_box.tag_configure("ok",      foreground=SUCCESS)
        self._log_box.tag_configure("error",   foreground=ERROR)
        self._log_box.tag_configure("warn",    foreground=WARNING)
        self._log_box.tag_configure("info",    foreground=TEXT_SEC)
        self._log_box.tag_configure("section", foreground=ACCENT,
                                    font=("Consolas", 10, "bold"))

    def _enqueue_log(self, message: str, level: str = "info"):
        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stripped = message.lstrip("\n")
        prefix   = message[: len(message) - len(stripped)]
        if stripped:
            self._log_queue.put((f"{prefix}[{ts}] {stripped}", level))
        else:
            self._log_queue.put((message, level))



    def _stop(self):
        if not self._running:
            return
        if not messagebox.askyesno(
            "Conferma stop",
            "Interrompere l'operazione in corso?\n\nL'operazione corrente terminerà, poi verrà eseguito rollback e chiusura connessioni.",
            icon="warning"
        ):
            return
        self._stop_requested = True
        self._btn_stop.configure(fg=TEXT_SEC, cursor="arrow")
        self._status_var.set("Stop richiesto — attendi il termine dell'operazione corrente ...")



    def _on_done(self, success: bool):
        self._running = False
        self._stop_requested = False
        self._btn_stop.configure(fg=TEXT_SEC, cursor="arrow")
        color = SUCCESS if success else ERROR
        self._status_var.set("✓ Completato." if success else "✗ Terminato.")
        self._btn.configure(fg=color, cursor="hand2")
        self.after(3000, lambda: self._btn.configure(fg=ACCENT))

    def _attach_tooltip(self, widget, text: str):
        """Mostra un piccolo tooltip scuro al passaggio del mouse sul widget."""
        tip = [None]

        def _show(e):
            if tip[0]:
                return
            x = widget.winfo_rootx() + widget.winfo_width() // 2
            y = widget.winfo_rooty() - 24
            tw = tkinter.Toplevel(widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            tw.configure(bg=BORDER)
            tkinter.Label(tw, text=text, bg=BG_CARD2, fg=TEXT_SEC,
                          font=("Consolas", 8), padx=6, pady=3,
                          relief="flat").pack()
            tip[0] = tw

        def _hide(e):
            if tip[0]:
                tip[0].destroy()
                tip[0] = None

        widget.bind("<Enter>", _show)
        widget.bind("<Leave>", _hide)

    def _poll_log(self):
        try:
            while True:
                msg, level = self._log_queue.get_nowait()
                self._log_box.configure(state="normal")
                self._log_box.insert("end", msg + "\n", level)
                self._log_box.see("end")
                self._log_box.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(80, self._poll_log)

    def _paste_popup(self, *, title, subtitle, tree, count_var, empty_warning,
                     count_label_fn, save_fn, two_column=False,
                     W=500, H=420):
        """Popup generico Modifica/Aggiungi — usato da PRM, Identifier e Reference."""
        popup = tkinter.Toplevel(self)
        popup.title(title)
        popup.configure(bg=BG)
        popup.resizable(False, False)
        popup.grab_set()
        popup.update_idletasks()
        x = (popup.winfo_screenwidth()  - W) // 2
        y = (popup.winfo_screenheight() - H) // 2
        popup.geometry(f"{W}x{H}+{x}+{y}")

        Label(popup, text=title,
              bg=BG, fg=TEXT_PRI, font=("Consolas", 11, "bold"), pady=12).pack()
        Label(popup, text=subtitle,
              bg=BG, fg=TEXT_SEC, font=("Consolas", 9), justify="center").pack()
        Frame(popup, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(8, 0))

        btn_row = Frame(popup, bg=BG)
        btn_row.pack(side="bottom", fill="x", padx=16, pady=12)
        btn_annulla = tkinter.Button(
            btn_row, text="Annulla",
            bg=BG_CARD, fg=TEXT_SEC, activebackground=BG_HOVER,
            activeforeground=TEXT_PRI, font=("Consolas", 10, "bold"),
            relief="flat", cursor="hand2", pady=6, padx=14, bd=0,
            command=popup.destroy)
        btn_annulla.pack(side="right", padx=(6, 0))
        btn_conferma = tkinter.Button(
            btn_row, text="✓  Conferma",
            bg=ACCENT, fg="#ffffff", activebackground="#3a7ee8",
            activeforeground="#ffffff", font=("Consolas", 10, "bold"),
            relief="flat", cursor="hand2", pady=6, padx=14, bd=0)
        btn_conferma.pack(side="right")

        feedback_var = tkinter.StringVar(value="")
        feedback_lbl = Label(popup, textvariable=feedback_var,
                             bg=BG, fg=TEXT_SEC, font=("Consolas", 9), pady=4)
        feedback_lbl.pack(side="bottom", fill="x", padx=16)

        txt_frame = Frame(popup, bg=BG_CARD)
        txt_frame.pack(fill="both", expand=True, padx=16, pady=(8, 0))
        vsb = ttk.Scrollbar(txt_frame, style="Dark.Vertical.TScrollbar")
        vsb.pack(side="right", fill="y")
        txt = Text(txt_frame, bg=BG_INPUT, fg=TEXT_PRI, font=("Consolas", 10),
                   relief="flat", bd=0, insertbackground=TEXT_PRI, wrap="none",
                   padx=8, pady=6, yscrollcommand=vsb.set)
        txt.pack(fill="both", expand=True)
        vsb.config(command=txt.yview)

        if two_column:
            txt.tag_configure("invalid", foreground=WARNING, background="#2a1f00")

        # Carica valori esistenti dalla tabella
        existing = []
        for iid in tree.get_children():
            vals = tree.item(iid, "values")
            if vals:
                existing.append(f"{vals[0]};{vals[1]}" if two_column else vals[0])
        if existing:
            txt.insert("1.0", "\n".join(existing))
        txt.focus_set()

        def _on_conferma():
            raw = txt.get("1.0", "end").strip().splitlines()
            txt.tag_remove("invalid", "1.0", "end") if two_column else None

            if two_column:
                valid, invalid = [], []
                for i, line in enumerate(raw):
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(";")
                    if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                        valid.append((parts[0].strip(), parts[1].strip()))
                    else:
                        invalid.append(i + 1)
                        txt.tag_add("invalid", f"{i+1}.0", f"{i+1}.end")
                if not valid and not invalid:
                    feedback_var.set("⚠  Nessuna riga trovata.")
                    feedback_lbl.config(fg=WARNING)
                    return
                if invalid:
                    feedback_var.set(
                        f"⚠  {len(invalid)} riga/e non valida/e evidenziate — correggi e riprova.")
                    feedback_lbl.config(fg=WARNING)
                    return
                tree.delete(*tree.get_children())
                for p0, p1 in valid:
                    tree.insert("", "end", values=(p0, p1))
            else:
                valid = [line.strip() for line in raw if line.strip()]
                if not valid:
                    feedback_var.set(empty_warning)
                    feedback_lbl.config(fg=WARNING)
                    return
                tree.delete(*tree.get_children())
                for v in valid:
                    tree.insert("", "end", values=(v,))

            count_var.set(count_label_fn(len(valid)))
            save_fn()
            popup.destroy()

        btn_conferma.config(command=_on_conferma)



# ════════════════════════════════════════════════════════════════════════════
# GUI
# ════════════════════════════════════════════════════════════════════════════

class HubProdSync(_AppBase):
    def __init__(self, master):
        super().__init__(master, bg=BG)


        self._log_queue: queue.Queue = queue.Queue()
        self._running        = False
        self._stop_requested = False

        self._build_ui()
        self._poll_log()

    # ── Header ───────────────────────────────────────────────────────────



    def _build_ui(self):
        self._status_var = tkinter.StringVar(value="Pronto.")
        Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, side="bottom")
        self._status_lbl = Label(self, textvariable=self._status_var, bg=BG, fg=TEXT_SEC,
                                  font=("Consolas", 9), anchor="w", pady=5)
        self._status_lbl.pack(fill="x", padx=24, side="bottom")
        self._build_notebook([
            ("  ▶  Pipeline  ", self._build_pipeline_tab),
        ])

    # ── Tab Pipeline ──────────────────────────────────────────────────────

    def _build_pipeline_tab(self, parent):
        left, right = self._build_panel_layout(parent, left_width=220)

        # Intestazione pannello sinistro
        hdr_left = Frame(left, bg=BG_CARD2)
        hdr_left.pack(fill="x")
        Label(hdr_left, text="Tabelle", bg=BG_CARD2, fg=TEXT_PRI,
              font=("Consolas", 9, "bold"), padx=14, pady=10,
              anchor="w").pack(fill="x")
        Frame(left, bg=BORDER, height=1).pack(fill="x")

        # --- Sezione tabelle (checkbox) ---

        _pre = _read_env_raw()
        def _bv(key):
            v = _pre.get(key, "")
            if v == "":
                return False
            return v.lower() in {"1", "true", "yes", "y", "on"}

        self._sync_customer_var            = tkinter.BooleanVar(value=_bv("SYNC_CUSTOMER"))
        self._sync_agreement_var           = tkinter.BooleanVar(value=_bv("SYNC_AGREEMENT"))
        self._sync_sap_filter_var          = tkinter.BooleanVar(value=_bv("SYNC_SAP_FILTER"))
        self._sync_identifier_version_var  = tkinter.BooleanVar(value=_bv("SYNC_IDENTIFIER_VERSION"))
        self._sync_sap_old_plan_var        = tkinter.BooleanVar(value=_bv("SYNC_SAP_OLD_PLAN"))
        self._sync_old_agreement_id_map_var = tkinter.BooleanVar(value=_bv("SYNC_OLD_AGREEMENT_ID_MAP"))

        _FLAG_MAP = {
            id(self._sync_customer_var):           "SYNC_CUSTOMER",
            id(self._sync_agreement_var):          "SYNC_AGREEMENT",
            id(self._sync_sap_filter_var):         "SYNC_SAP_FILTER",
            id(self._sync_identifier_version_var): "SYNC_IDENTIFIER_VERSION",
            id(self._sync_sap_old_plan_var):       "SYNC_SAP_OLD_PLAN",
            id(self._sync_old_agreement_id_map_var): "SYNC_OLD_AGREEMENT_ID_MAP",
        }

        def _make_row_check(par, var, label_text):
            row = Frame(par, bg=BG_CARD)
            row.pack(fill="x", padx=14, pady=3)
            box = Label(row, text="☑" if var.get() else "☐",
                        bg=BG_CARD, fg=ACCENT if var.get() else TEXT_SEC,
                        font=("Consolas", 12), cursor="hand2", width=2)
            box.pack(side="left", padx=(0, 6))
            lbl = Label(row, text=label_text, bg=BG_CARD, fg=TEXT_PRI,
                        font=("Consolas", 10), cursor="hand2", wraplength=155, justify="left")
            lbl.pack(side="left")

            def _toggle(e=None):
                var.set(not var.get())
                box.configure(text="☑" if var.get() else "☐",
                              fg=ACCENT if var.get() else TEXT_SEC)
                env_key = _FLAG_MAP.get(id(var))
                if env_key:
                    _write_env({env_key: "true" if var.get() else "false"})

            box.bind("<Button-1>", _toggle)
            lbl.bind("<Button-1>", _toggle)
            row.bind("<Button-1>", _toggle)

        _make_row_check(left, self._sync_customer_var,          "Customer")
        _make_row_check(left, self._sync_agreement_var,         "Agreement")
        _make_row_check(left, self._sync_sap_filter_var,        "Sap filter contract")
        _make_row_check(left, self._sync_identifier_version_var,"Identifier version map")
        _make_row_check(left, self._sync_sap_old_plan_var,      "Sap old plan map")
        _make_row_check(left, self._sync_old_agreement_id_map_var, "Old agreement id map")

        Frame(left, bg=BORDER, height=1).pack(fill="x", padx=14, pady=(8, 0))

        # --- Bottoni in fondo ---
        btn_frame = Frame(left, bg=BG_CARD)
        btn_frame.pack(side="bottom", fill="x", padx=14, pady=12)

        row1 = Frame(btn_frame, bg=BG_CARD)
        row1.pack(fill="x")
        self._btn = self._make_btn(row1, "\u25b6  Avvia", self._start)
        self._btn.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self._btn_stop = self._make_btn(row1, "\u25a0  Stop", self._stop, color=ERROR)
        self._btn_stop.pack(side="left", fill="x", expand=True, padx=(3, 0))
        self._btn_stop.configure(fg=TEXT_SEC, cursor="arrow")


        # Etichette destinazione (dummy per compatibilita con _on_target_change)
        self._cust_dest_lbl = Label(left, text="", bg=BG_CARD)
        self._agr_dest_lbl  = Label(left, text="", bg=BG_CARD)

        self._build_log_panel(right, on_clear=self._clear_log)

    # ── Tab About ─────────────────────────────────────────────────────────


    # ── Pipeline ──────────────────────────────────────────────────────────

    def _start(self):
        if self._running:
            return
        self._running = True
        self._stop_requested = False
        self._btn.configure(fg=TEXT_SEC, cursor="arrow")
        self._btn_stop.configure(fg=ERROR, cursor="hand2")
        target = _get_target_env()
        self._status_var.set(f"In esecuzione → {target} ...")
        threading.Thread(
            target=hub_run_pipeline,
            args=(target, self, self._enqueue_log, self._on_done,
                  self._sync_customer_var.get(), self._sync_agreement_var.get(),
                  self._sync_sap_filter_var.get(), self._sync_identifier_version_var.get(),
                  self._sync_sap_old_plan_var.get(),
                  self._sync_old_agreement_id_map_var.get()),
            daemon=True,
        ).start()



# ════════════════════════════════════════════════════════════════════════════
# KRAKEN DATA EXTRACTOR
# ════════════════════════════════════════════════════════════════════════════


import csv
import os
import queue
import threading
import tkinter
from io import StringIO
from pathlib import Path
from tkinter import BooleanVar, Frame, Label, Scrollbar, StringVar, Text, Tk, ttk
from tkinter import messagebox

from dotenv import load_dotenv

_HERE      = Path(__file__).parent
_ENV       = _HERE / "config" / ".env"
INPUT_FILE             = _HERE / "input" / "kraken data extractor" / "data_input.txt"
INPUT_FILE_IDENTIFIER  = _HERE / "input" / "kraken data extractor" / "data_input_identifier.txt"
INPUT_FILE_REFERENCE   = _HERE / "input" / "kraken data extractor" / "data_input_reference.txt"
VERSION     = "1.3.0"

MODE_PRM        = "PRM"
MODE_IDENTIFIER = "IDENTIFIER"
MODE_REFERENCE  = "REFERENCE"

load_dotenv(dotenv_path=_ENV)

# ── Configurazione query ─────────────────────────────────────────────────────

PAYMENT_QUERY_FILES = [
    "query_customer.sql",
    "query_agreement.sql",
    "query_pp_elec.sql",
    "query_pp_gas.sql",
    "query_renewal.sql",
    "query_invoice_elec.sql",
    "query_invoice_gas.sql",
    "query_payment_elec.sql",
    "query_payment_gas.sql",
    "query_cheque_kj.sql",
    "query_cheque_kh.sql",
]

ALL_QUERY_FILES = [
    "query_customer.sql",
    "query_agreement.sql",
    "query_pp_elec.sql",
    "query_pp_gas.sql",
    "query_renewal.sql",
    "query_invoice_elec.sql",
    "query_invoice_gas.sql",
    "query_payment_elec.sql",
    "query_payment_gas.sql",
    "query_cheque_kj.sql",
    "query_cheque_kh.sql",
]

TARGET_TABLES_PAYMENT = {
    "query_customer.sql":     "kraken_customer",
    "query_agreement.sql":    "kraken_agreement",
    "query_pp_elec.sql":      "payment_schedule",
    "query_pp_gas.sql":       "payment_schedule_gas",
    "query_renewal.sql":      "kraken_agreement_renewal",
    "query_invoice_elec.sql": "kraken_invoice",
    "query_invoice_gas.sql":  "kraken_invoice_gas",
    "query_payment_elec.sql": "test_payments",
    "query_payment_gas.sql":  "test_payments_gas",
    "query_cheque_kj.sql":    "kraken_cheque_statge_1",
    "query_cheque_kh.sql":    "kraken_cheque_statge_2",
}

QUERY_FLAGS = {
    "query_customer.sql":     "RUN_CUSTOMER",
    "query_agreement.sql":    "RUN_AGREEMENT",
    "query_pp_elec.sql":      "RUN_PP_ELEC",
    "query_pp_gas.sql":       "RUN_PP_GAS",
    "query_renewal.sql":      "RUN_RENEWAL",
    "query_invoice_elec.sql": "RUN_INVOICE_ELEC",
    "query_invoice_gas.sql":  "RUN_INVOICE_GAS",
    "query_payment_elec.sql": "RUN_PAYMENT_ELEC",
    "query_payment_gas.sql":  "RUN_PAYMENT_GAS",
    "query_cheque_kj.sql":    "RUN_CHEQUE_KJ",
    "query_cheque_kh.sql":    "RUN_CHEQUE_KH",
}

QUERY_FLAGS_IDENTIFIER = {
    "query_customer.sql":     "RUN_IDENTIFIER_CUSTOMER",
    "query_agreement.sql":    "RUN_IDENTIFIER_AGREEMENT",
    "query_pp_elec.sql":      "RUN_IDENTIFIER_PP_ELEC",
    "query_pp_gas.sql":       "RUN_IDENTIFIER_PP_GAS",
    "query_renewal.sql":      "RUN_IDENTIFIER_RENEWAL",
    "query_payment_elec.sql": "RUN_IDENTIFIER_PAYMENT_ELEC",
    "query_payment_gas.sql":  "RUN_IDENTIFIER_PAYMENT_GAS",
    "query_cheque_kj.sql":    "RUN_IDENTIFIER_CHEQUE_KJ",
    "query_cheque_kh.sql":    "RUN_IDENTIFIER_CHEQUE_KH",
}

QUERY_FLAGS_REFERENCE = {
    "query_customer.sql":     "RUN_REFERENCE_CUSTOMER",
    "query_agreement.sql":    "RUN_REFERENCE_AGREEMENT",
    "query_pp_elec.sql":      "RUN_REFERENCE_PP_ELEC",
    "query_pp_gas.sql":       "RUN_REFERENCE_PP_GAS",
    "query_renewal.sql":      "RUN_REFERENCE_RENEWAL",
    "query_invoice_elec.sql": "RUN_REFERENCE_INVOICE_ELEC",
    "query_invoice_gas.sql":  "RUN_REFERENCE_INVOICE_GAS",
    "query_cheque_kj.sql":    "RUN_REFERENCE_CHEQUE_KJ",
    "query_cheque_kh.sql":    "RUN_REFERENCE_CHEQUE_KH",
}

FLAG_ENV_KEYS = QUERY_FLAGS  # alias usato da KrakenDataExtractor._load_flags_from_env

def _reload_env_into_os():
    load_dotenv(dotenv_path=_ENV, override=True)

# Flow identifier che estraggono PRM/Kraken dai risultati invoice
FLOWS_IDENTIFIER_SECONDARY = [
    "query_customer.sql",
    "query_agreement.sql",
    "query_pp_elec.sql",
    "query_pp_gas.sql",
    "query_renewal.sql",
    "query_payment_elec.sql",
    "query_payment_gas.sql",
    "query_cheque_kj.sql",
    "query_cheque_kh.sql",
]

# Flow reference secondari (estratti dai pagamenti)
FLOWS_REFERENCE_SECONDARY = [
    "query_customer.sql",
    "query_agreement.sql",
    "query_pp_elec.sql",
    "query_pp_gas.sql",
    "query_renewal.sql",
    "query_invoice_elec.sql",
    "query_invoice_gas.sql",
    "query_cheque_kj.sql",
    "query_cheque_kh.sql",
]

# Query payment con filtro reference
FLOWS_REFERENCE_PRIMARY = [
    "query_payment_elec.sql",
    "query_payment_gas.sql",
]

QUERY_LABELS = {
    "query_customer.sql":     "Customer",
    "query_agreement.sql":    "Agreement",
    "query_pp_elec.sql":      "PP Elec",
    "query_pp_gas.sql":       "PP Gas",
    "query_renewal.sql":      "Renewal",
    "query_invoice_elec.sql": "Invoice Elec",
    "query_invoice_gas.sql":  "Invoice Gas",
    "query_payment_elec.sql": "Payment Elec",
    "query_payment_gas.sql":  "Payment Gas",
    "query_cheque_energie.sql":     "Cheque Energie KJ",
    "query_cheque_energie_kh.sql": "Cheque Energie KH",
    "query_cheque_kj.sql":    "Cheque Energie KJ",
    "query_cheque_kh.sql":    "Cheque Energie KH",
}

# ── Colori & stile ───────────────────────────────────────────────────────────
BG       = "#0f1117"
BG_CARD  = "#1a1d27"
BG_CARD2 = "#141720"
BG_HOVER = "#22263a"
BG_INPUT = "#0d1020"
ACCENT   = "#4f8ef7"
ACCENT2  = "#7c3aed"
SUCCESS  = "#22c55e"
WARNING  = "#f59e0b"
ERROR    = "#ef4444"
TEXT_PRI = "#f0f2ff"
TEXT_SEC = "#8892b0"
BORDER   = "#2a2d3e"


# ════════════════════════════════════════════════════════════════════════════
# LOGICA PIPELINE
# ════════════════════════════════════════════════════════════════════════════

def get_kraken_connection():
    import psycopg2
    required = ["KRAKEN_HOST", "KRAKEN_PORT", "KRAKEN_NAME", "KRAKEN_USER", "KRAKEN_PASSWORD"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        raise EnvironmentError(f"Variabili d'ambiente mancanti (kraken): {', '.join(missing)}")
    return psycopg2.connect(
        host=os.getenv("KRAKEN_HOST"),
        port=int(os.getenv("KRAKEN_PORT", "5432")),
        dbname=os.getenv("KRAKEN_NAME"),
        user=os.getenv("KRAKEN_USER"),
        password=os.getenv("KRAKEN_PASSWORD"),
    )


def get_integration_connection(tunnel, env="INTEGRATION"):
    import psycopg2
    prefix = "RECETTE" if env == "RECETTE" else "INTEGRATION"
    return psycopg2.connect(
        host="127.0.0.1",
        port=tunnel.local_bind_port,
        dbname=os.getenv(f"{prefix}_NAME"),
        user=os.getenv(f"{prefix}_USER"),
        password=os.getenv(f"{prefix}_PASSWORD"),
    )


def get_hub_connection():
    import psycopg2
    required = ["HUB_HOST", "HUB_PORT", "HUB_NAME", "HUB_USER", "HUB_PASSWORD"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        raise EnvironmentError(f"Variabili d'ambiente mancanti (db3): {', '.join(missing)}")
    return psycopg2.connect(
        host=os.getenv("HUB_HOST"),
        port=int(os.getenv("HUB_PORT", "5432")),
        dbname=os.getenv("HUB_NAME"),
        user=os.getenv("HUB_USER"),
        password=os.getenv("HUB_PASSWORD"),
    )


def open_ssh_tunnel(env="INTEGRATION"):
    from sshtunnel import SSHTunnelForwarder
    if env == "RECETTE":
        ssh_host_key = "SSH_RECETTE_HOST"
        db_host_key, db_port_key = "RECETTE_HOST", "RECETTE_PORT"
        required = ["SSH_RECETTE_HOST", "SSH_USER", "SSH_KEY_PATH",
                    "RECETTE_HOST", "RECETTE_NAME", "RECETTE_USER", "RECETTE_PASSWORD"]
        env_label = "SSH/recette"
    else:
        ssh_host_key = "SSH_HOST"
        db_host_key, db_port_key = "INTEGRATION_HOST", "INTEGRATION_PORT"
        required = ["SSH_HOST", "SSH_USER", "SSH_KEY_PATH",
                    "INTEGRATION_HOST", "INTEGRATION_NAME", "INTEGRATION_USER", "INTEGRATION_PASSWORD"]
        env_label = "SSH/integration"
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        raise EnvironmentError(f"Variabili d'ambiente mancanti ({env_label}): {', '.join(missing)}")
    tunnel = SSHTunnelForwarder(
        (os.getenv(ssh_host_key), int(os.getenv("SSH_PORT", "22"))),
        ssh_username=os.getenv("SSH_USER"),
        ssh_pkey=os.getenv("SSH_KEY_PATH"),
        remote_bind_address=(os.getenv(db_host_key), int(os.getenv(db_port_key, "5432"))),
    )
    tunnel.start()
    return tunnel


def load_input_data():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"File di input non trovato: {INPUT_FILE}")

    lines = INPUT_FILE.read_text(encoding="utf-8").strip().splitlines()
    lista_prm_kraken, lista_prm, lista_kraken = [], [], []

    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.lower().startswith("prm"):
            continue
        parts = line.split(";")
        if len(parts) != 2:
            continue
        prm, kraken = parts[0].strip(), parts[1].strip()
        lista_prm_kraken.append(f"'{prm}{kraken}'")
        lista_prm.append(f"'{prm}'")
        lista_kraken.append(f"'{kraken}'")

    if not lista_prm:
        raise ValueError("Nessun dato valido trovato nel file di input.")

    return ", ".join(lista_prm_kraken), ", ".join(lista_prm), ", ".join(lista_kraken)


def load_identifier_data():
    if not INPUT_FILE_IDENTIFIER.exists():
        raise FileNotFoundError(f"File identifier non trovato: {INPUT_FILE_IDENTIFIER}")

    lines = INPUT_FILE_IDENTIFIER.read_text(encoding="utf-8").strip().splitlines()
    lista = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        lista.append(f"'{line}'")

    if not lista:
        raise ValueError("Nessun identifier valido trovato nel file di input.")

    return ", ".join(lista)


def load_reference_data():
    if not INPUT_FILE_REFERENCE.exists():
        raise FileNotFoundError(f"File reference non trovato: {INPUT_FILE_REFERENCE}")

    lines = INPUT_FILE_REFERENCE.read_text(encoding="utf-8").strip().splitlines()
    lista = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        lista.append(f"'{line}'")

    if not lista:
        raise ValueError("Nessun reference valido trovato nel file di input.")

    return ", ".join(lista)




def normalize_timestamps(rows):
    """Converte i datetime con timezone in naive locali con precisione ai millisecondi."""
    import datetime
    normalized = []
    for row in rows:
        new_row = []
        for val in row:
            if isinstance(val, datetime.datetime) and val.tzinfo is not None:
                val = val.astimezone().replace(tzinfo=None, microsecond=(val.microsecond // 1000) * 1000)
            new_row.append(val)
        normalized.append(tuple(new_row))
    return normalized


def bulk_insert(cursor, table: str, columns: list, rows: list):
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", quotechar="\x01", quoting=csv.QUOTE_MINIMAL)
    writer.writerows(rows)
    buffer.seek(0)
    cols = ", ".join(columns)
    cursor.copy_expert(
        f"COPY {table} ({cols}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t', QUOTE E'\\x01', NULL '')",
        buffer,
    )


_HUB_META_QUERIES = {
    "query_customer.sql":      "CUSTOMER",
    "query_agreement.sql":     "AGREEMENT",
    "query_pp_elec.sql":       "QUERY_PAYMENT_PLAN_ELEC",
    "query_pp_gas.sql":        "QUERY_PAYMENT_PLAN_GAS",
    "query_renewal.sql":       "AGREEMENT_RENEWAL",
    "query_invoice_elec.sql":  "QUERY_INVOICE_ELEC",
    "query_invoice_gas.sql":   "QUERY_INVOICE_GAS",
}

_PP_ELEC_CONCAT = """and concat(case
        when prm.external_identifier like '63300000%' 
            then substring(prm.external_identifier,9,6)::numeric::text
        else prm.external_identifier
    end, acc.number) IN ('LISTA_PRM_E_KRAKEN_ACCOUNT')"""

_PP_GAS_CONCAT = """and concat(case
        when pce.external_identifier like '63300000%' 
            then substring(pce.external_identifier,9,6)::numeric::text
        else pce.external_identifier
    end, acc.number) IN ('LISTA_PRM_E_KRAKEN_ACCOUNT')"""

_RENEWAL_CONCAT = """AND concat(
    case when substring(mss.external_identifier,1,8)='63300000' then substring(mss.external_identifier,9,6)::numeric::text else mss.external_identifier end,
    aa.number
    ) IN ('LISTA_PRM_E_KRAKEN_ACCOUNT')"""

_RENEWAL_PRM_FILTER = """  LEFT JOIN issuance_issuedbillingdocument iss_doc 
         ON iss_doc.billing_document_id = doc.id
  WHERE case when mss.external_identifier like '63300000%' then substring(mss.external_identifier,9,6)::numeric::text else mss.external_identifier end IN ('LISTA_PRM')
)"""

# Dizionario dei replace per ogni query: lista di (old, new, max_occurrences)
# max_occurrences=0 significa tutte le occorrenze
_QUERY_REPLACEMENTS = {
    "query_customer.sql": [
        ("AND aa.updated_at > 'DATETOINSERT'",
         "AND aa.number IN ('LISTA_KRAKEN_ACCOUNT')", 0),
    ],
    "query_agreement.sql": [
        ("where updated_at > 'DATETOINSERT'",
         "WHERE concat(supply_point, kraken_account) IN ('LISTA_PRM_E_KRAKEN_ACCOUNT')", 0),
    ],
    "query_pp_elec.sql": [
        ("and schedule.updated_at > 'DATETOINSERT'", _PP_ELEC_CONCAT, 0),
    ],
    "query_pp_gas.sql": [
        ("and schedule.updated_at > 'DATETOINSERT'", _PP_GAS_CONCAT, 0),
    ],
    "query_renewal.sql": [
        ("AND doc.finalized_at > 'DATETOINSERT'\n  AND doc.identifier like '{COMMODITY}%'",
         _RENEWAL_CONCAT, 0),
        ("""  LEFT JOIN issuance_issuedbillingdocument iss_doc 
         ON iss_doc.billing_document_id = doc.id
)""",
         _RENEWAL_PRM_FILTER, 1),
    ],
    "query_invoice_elec.sql": [
        ("document.finalized_at > 'DATETOINSERT'",
         """acc.number in ('LISTA_KRAKEN_ACCOUNT')
	and concat(
			case
				when substring(template_vars_json::json#>>'{prm_info,id}',1,8) = '63300000'
				then substring(template_vars_json::json#>>'{prm_info,id}',9,6)::numeric::text
				else template_vars_json::json#>>'{prm_info,id}'
			end, 
			acc.number
		) in ('LISTA_PRM_E_KRAKEN_ACCOUNT')""", 0),
    ],
    "query_invoice_gas.sql": [
        ("document.finalized_at > 'DATETOINSERT'",
         """acc.number in ('LISTA_KRAKEN_ACCOUNT')
and concat(
		case
			when substring(template_vars_json::json#>>'{meter_info,id}',1,8)='63300000'
			then substring(template_vars_json::json#>>'{meter_info,id}',9,6)::numeric::text
			else template_vars_json::json#>>'{meter_info,id}'
		end,
		acc.number
	) in ('LISTA_PRM_E_KRAKEN_ACCOUNT')""", 0),
    ],
}

# Replace per modalità IDENTIFIER — sostituisce il placeholder con filtro su document.identifier
_QUERY_REPLACEMENTS_IDENTIFIER = {
    "query_invoice_elec.sql": [
        ("document.finalized_at > 'DATETOINSERT'",
         "document.identifier IN ('LISTA_IDENTIFIER')", 0),
    ],
    "query_invoice_gas.sql": [
        ("document.finalized_at > 'DATETOINSERT'",
         "document.identifier IN ('LISTA_IDENTIFIER')", 0),
    ],
}

FLOWS_IDENTIFIER = ["query_invoice_elec.sql", "query_invoice_gas.sql"]


def load_query_from_hub(hub_conn, flow: str, lista_prm_kraken: str, lista_prm: str, lista_kraken: str):
    """Recupera la query dalla tabella di configurazione su HUB e applica i placeholder."""
    import re
    hname = _HUB_META_QUERIES[flow]
    cur = hub_conn.cursor()
    cur.execute("""
        SELECT hquery
        FROM hub_config_query_kraken hcqk
        WHERE hcqk.hname = %s AND hcqk.henv = 'PROD' AND NOT (hcqk.hutemporal_bound)
    """, (hname,))
    row = cur.fetchone()
    cur.close()
    if not row or not row[0]:
        return None
    query = row[0].strip()

    for old, new, count in _QUERY_REPLACEMENTS.get(flow, []):
        if count:
            query = query.replace(old, new, count)
        else:
            query = query.replace(old, new)

    if "DATETOINSERT" in query:
        match = re.search(r".{0,60}DATETOINSERT.{0,60}", query)
        raise ValueError(f"Placeholder DATETOINSERT non sostituito. Contesto: ...{match.group() if match else '?'}...")

    query = query.replace("'LISTA_PRM_E_KRAKEN_ACCOUNT'", lista_prm_kraken)
    query = query.replace("'LISTA_PRM'", lista_prm)
    query = query.replace("'LISTA_KRAKEN_ACCOUNT'", lista_kraken)
    return query


def load_query_from_hub_identifier(hub_conn, flow: str, lista_identifier: str):
    """Recupera la query dal HUB e applica il placeholder LISTA_IDENTIFIER."""
    import re
    hname = _HUB_META_QUERIES[flow]
    cur = hub_conn.cursor()
    cur.execute("""
        SELECT hquery
        FROM hub_config_query_kraken hcqk
        WHERE hcqk.hname = %s AND hcqk.henv = 'PROD' AND NOT (hcqk.hutemporal_bound)
    """, (hname,))
    row = cur.fetchone()
    cur.close()
    if not row or not row[0]:
        return None
    query = row[0].strip()

    for old, new, count in _QUERY_REPLACEMENTS_IDENTIFIER.get(flow, []):
        if count:
            query = query.replace(old, new, count)
        else:
            query = query.replace(old, new)

    if "DATETOINSERT" in query:
        match = re.search(r".{0,60}DATETOINSERT.{0,60}", query)
        raise ValueError(f"Placeholder DATETOINSERT non sostituito. Contesto: ...{match.group() if match else '?'}...")

    query = query.replace("'LISTA_IDENTIFIER'", lista_identifier)
    return query



def _commit_rows(integration_conn, table, columns, rows, log):
    """Bulk insert con commit. Solleva l'eccezione in caso di errore."""
    import psycopg2
    if rows:
        cur = integration_conn.cursor()
        try:
            bulk_insert(cur, table, columns, rows)
            integration_conn.commit(); cur.close()
            log(f"[OK] DB: {len(rows)} righe inserite in '{table}'", "ok")
        except psycopg2.Error as e:
            integration_conn.rollback(); cur.close(); raise e
    else:
        log(f"[INFO] Nessuna riga da inserire in '{table}'.", "info")


def setup_kraken_connections(env, log, on_done):
    import psycopg2
    _ssh_host = os.getenv("SSH_RECETTE_HOST") if env == "RECETTE" else os.getenv("SSH_HOST")
    _db_host  = os.getenv("RECETTE_HOST")      if env == "RECETTE" else os.getenv("INTEGRATION_HOST")
    _db_name  = os.getenv("RECETTE_NAME")      if env == "RECETTE" else os.getenv("INTEGRATION_NAME")
    log(f"\n[INFO] Connessione Kraken: {os.getenv('KRAKEN_HOST')} / {os.getenv('KRAKEN_NAME')} ...", "info")
    try:
        kraken_conn = get_kraken_connection()
        log("[INFO] Connessione Kraken attiva ✓", "ok")
    except (psycopg2.OperationalError, EnvironmentError) as e:
        log(f"[ERRORE] Connessione Kraken fallita: {e}", "error")
        on_done(success=False); return None
    log(f"[INFO] Apertura tunnel SSH verso {_ssh_host} ...", "info")
    try:
        tunnel = open_ssh_tunnel(env)
        log(f"[INFO] Tunnel attivo su porta locale {tunnel.local_bind_port}", "info")
    except Exception as e:
        log(f"[ERRORE] Tunnel SSH fallito: {e}", "error")
        kraken_conn.close(); on_done(success=False); return None
    try:
        integration_conn = get_integration_connection(tunnel, env)
        log(f"[INFO] Connessione {env.capitalize()}: {_db_host} / {_db_name} ✓", "ok")
    except psycopg2.OperationalError as e:
        log(f"[ERRORE] Connessione {env.capitalize()} fallita: {e}", "error")
        kraken_conn.close(); tunnel.stop(); on_done(success=False); return None
    log(f"\n[INFO] Connessione HUB: {os.getenv('HUB_HOST')} ...", "info")
    try:
        hub_conn = get_hub_connection()
        log("[INFO] Connessione HUB attiva ✓", "ok")
    except (psycopg2.OperationalError, EnvironmentError) as e:
        log(f"[ERRORE] Connessione HUB fallita: {e}", "error")
        kraken_conn.close(); integration_conn.close(); tunnel.stop(); on_done(success=False); return None
    return kraken_conn, tunnel, integration_conn, hub_conn

def _run_identifier_query_gui(hub_conn, kraken_conn, integration_conn, flow, flags,
                               lista_identifier, log):
    import psycopg2
    table       = TARGET_TABLES_PAYMENT[flow]
    run_flag    = True  # invoice in modalità identifier gira sempre
    lbl         = QUERY_LABELS.get(flow, flow)

    log(f"\n── {lbl}  [RUN] ──", "section")
    try:
        cur = integration_conn.cursor()
        cur.execute(f"TRUNCATE TABLE {table};")
        integration_conn.commit(); cur.close()
        log(f"[OK] Truncate '{table}'", "ok")

        log(f"[INFO] Caricamento query '{lbl}' da hub_config_query_kraken ...", "info")
        query = load_query_from_hub_identifier(hub_conn, flow, lista_identifier)
        if query is None:
            log(f"[ERRORE] Query non trovata in hub_config_query_kraken per '{lbl}'.", "error")
            return
        hname = _HUB_META_QUERIES.get(flow, flow)
        log(f"[OK] Query {hname} recuperata da HUB PROD, procedo al lancio.", "ok")

        cur = kraken_conn.cursor()
        try:
            cur.execute(query)
        except Exception as e:
            cur.close()
            log(f"[ERRORE] Esecuzione query fallita su Kraken: {e}", "error")
            kraken_conn.rollback()
            return None
        columns = [d[0] for d in cur.description]
        rows = cur.fetchall(); cur.close()

        rows = normalize_timestamps(rows)

        if flow in ("query_invoice_elec.sql", "query_invoice_gas.sql"):
            idx_drop = [i for i, c in enumerate(columns) if c == "created_at"]
            if idx_drop:
                columns = [c for i, c in enumerate(columns) if i not in idx_drop]
                rows = [tuple(v for i, v in enumerate(row) if i not in idx_drop) for row in rows]

        _commit_rows(integration_conn, table, columns, rows, log)
        return columns, rows

    except Exception as e:
        log(f"[ERRORE] '{lbl}': {e}", "error")
        try:
            hub_conn.rollback()
        except Exception:
            pass


def run_pipeline_identifier(flags, log, on_done, env="INTEGRATION"):
    import psycopg2
    _reload_env_into_os()

    try:

        try:
            lista_identifier = load_identifier_data()
        except (FileNotFoundError, ValueError) as e:
            log(f"[ERRORE] {e}", "error")
            on_done(success=False); return

        log(f"[INFO] Caricate {lista_identifier.count(',') + 1} righe dal file identifier.", "info")

        conns = setup_kraken_connections(env, log, on_done)
        if conns is None: return
        kraken_conn, tunnel, integration_conn, hub_conn = conns

        invoice_results = {}
        for flow in FLOWS_IDENTIFIER:
            result = _run_identifier_query_gui(hub_conn, kraken_conn, integration_conn,
                                               flow, flags, lista_identifier, log)
            if result is not None:
                invoice_results[flow] = result

        # Estrai PRM e Kraken Account dai risultati invoice in memoria
        log("\n[INFO] Estrazione PRM e Kraken Account dai risultati invoice ...", "info")
        prm_kraken_set = set()
        prm_set        = set()
        kraken_set     = set()

        for flow, prm_col in [("query_invoice_elec.sql", "prm"), ("query_invoice_gas.sql", "pce")]:
            if flow not in invoice_results:
                continue
            columns, rows = invoice_results[flow]
            col_idx = {c: i for i, c in enumerate(columns)}
            for row in rows:
                prm    = (str(row[col_idx[prm_col]]) if prm_col in col_idx else "").strip()
                kraken = (str(row[col_idx["number"]]) if "number" in col_idx else "").strip()
                if prm and kraken:
                    prm_kraken_set.add(f"{prm}{kraken}")
                    prm_set.add(prm)
                    kraken_set.add(kraken)

        if not prm_set:
            log("[INFO] Nessun PRM/Kraken estratto dalle invoice — flussi secondari saltati.", "warn")
        else:
            log(f"[INFO] {len(prm_set)} coppie distinte PRM/Kraken estratte.", "ok")
            lista_prm_kraken = ", ".join(f"'{v}'" for v in sorted(prm_kraken_set))
            lista_prm        = ", ".join(f"'{v}'" for v in sorted(prm_set))
            lista_kraken     = ", ".join(f"'{v}'" for v in sorted(kraken_set))

            for flow in FLOWS_IDENTIFIER_SECONDARY:
                if flags.get(flow, False):
                    _run_payment_query_gui(hub_conn, kraken_conn, integration_conn,
                                           flow, flags, lista_prm_kraken, lista_prm, lista_kraken, log)

        kraken_conn.close(); integration_conn.close(); hub_conn.close(); tunnel.stop()
        log("\n[INFO] Pipeline identifier completata con successo.", "ok")
        on_done(success=True)

    except Exception as e:
        log(f"\n[ERRORE CRITICO] {e}", "error")
        on_done(success=False)


_PAYMENT_QUERIES = {
    "query_payment_elec.sql": "select * from j_kraken_payments\nwhere concat(supply_point, account_number) in ('LISTA_PRM_E_KRAKEN_ACCOUNT')\nand commodity = 'ELEC'",
    "query_payment_gas.sql":  "select * from j_kraken_payments\nwhere concat(supply_point, account_number) in ('LISTA_PRM_E_KRAKEN_ACCOUNT')\nand commodity = 'GAS'",
    "query_cheque_kj.sql": (
        "select account_number as kraken_account, net_amount, created_date as created_at,"
        " energy_cheque_id, segment"
        " from j_cheque_energie_registrati"
        " where account_number in ('LISTA_KRAKEN_ACCOUNT')"
    ),
    "query_cheque_kh.sql": (
        "select supply_point, ledger_type, net_amount, transferred_at, segment,"
        " reference, credit_id, account_number as kraken_account"
        " from j_cheque_energie_utilizzati"
        " where concat(supply_point, account_number) in ('LISTA_PRM_E_KRAKEN_ACCOUNT')"
    ),
}

_PAYMENT_QUERIES_REFERENCE = {
    "query_payment_elec.sql": "select * from j_kraken_payments\nwhere reference in ('LISTA_REFERENCE')\nand commodity = 'ELEC'",
    "query_payment_gas.sql":  "select * from j_kraken_payments\nwhere reference in ('LISTA_REFERENCE')\nand commodity = 'GAS'",
}


def _run_reference_payment_gui(hub_conn, kraken_conn, integration_conn, flow,
                                lista_reference, log):
    """Esegue le query payment con filtro reference (girano sempre)."""
    import psycopg2
    table       = TARGET_TABLES_PAYMENT[flow]
    lbl         = QUERY_LABELS.get(flow, flow)

    log(f"\n── {lbl}  [RUN] ──", "section")
    try:
        cur = integration_conn.cursor()
        cur.execute(f"TRUNCATE TABLE {table};")
        integration_conn.commit(); cur.close()
        log(f"[OK] Truncate '{table}'", "ok")

        query = _PAYMENT_QUERIES_REFERENCE[flow]
        query = query.replace("'LISTA_REFERENCE'", lista_reference)
        exec_conn = hub_conn

        cur = exec_conn.cursor()
        try:
            cur.execute(query)
        except Exception as e:
            cur.close()
            log(f"[ERRORE] Esecuzione query '{lbl}' fallita: {e}", "error")
            exec_conn.rollback()
            return None
        columns = [d[0] for d in cur.description]
        rows = cur.fetchall(); cur.close()

        if flow == "query_payment_elec.sql":
            columns = ["prm_id" if c == "supply_point" else c for c in columns]
            # Rimuove commodity — non presente in test_payments
            idx_drop = [i for i, c in enumerate(columns) if c == "commodity"]
            if idx_drop:
                columns = [c for i,c in enumerate(columns) if i not in idx_drop]
                rows = [tuple(v for i,v in enumerate(row) if i not in idx_drop) for row in rows]
        if flow == "query_payment_gas.sql":
            columns = ["pce_id" if c == "supply_point" else c for c in columns]
            # Rimuove commodity — non presente in test_payments_gas
            idx_drop = [i for i, c in enumerate(columns) if c == "commodity"]
            if idx_drop:
                columns = [c for i,c in enumerate(columns) if i not in idx_drop]
                rows = [tuple(v for i,v in enumerate(row) if i not in idx_drop) for row in rows]

        _commit_rows(integration_conn, table, columns, rows, log)
        return columns, rows

    except Exception as e:
        log(f"[ERRORE] '{lbl}': {e}", "error")
        try:
            hub_conn.rollback()
        except Exception:
            pass


def run_pipeline_reference(flags, log, on_done, env="INTEGRATION"):
    import psycopg2
    _reload_env_into_os()

    try:

        try:
            lista_reference = load_reference_data()
        except (FileNotFoundError, ValueError) as e:
            log(f"[ERRORE] {e}", "error")
            on_done(success=False); return

        log(f"[INFO] Caricate {lista_reference.count(',') + 1} reference dal file.", "info")

        conns = setup_kraken_connections(env, log, on_done)
        if conns is None: return
        kraken_conn, tunnel, integration_conn, hub_conn = conns

        # Payment sempre eseguiti
        payment_results = {}
        for flow in FLOWS_REFERENCE_PRIMARY:
            result = _run_reference_payment_gui(hub_conn, kraken_conn, integration_conn,
                                                flow, lista_reference, log)
            if result is not None:
                payment_results[flow] = result

        # Estrai PRM e Kraken Account dai risultati payment in memoria
        log("\n[INFO] Estrazione PRM e Kraken Account dai risultati payment ...", "info")
        prm_kraken_set = set()
        prm_set        = set()
        kraken_set     = set()

        for flow, prm_col in [("query_payment_elec.sql", "prm_id"), ("query_payment_gas.sql", "pce_id")]:
            if flow not in payment_results:
                continue
            columns, rows = payment_results[flow]
            col_idx = {c: i for i, c in enumerate(columns)}
            for row in rows:
                prm    = (str(row[col_idx[prm_col]]) if prm_col in col_idx else "").strip()
                kraken = (str(row[col_idx["account_number"]]) if "account_number" in col_idx else "").strip()
                if prm and kraken:
                    prm_kraken_set.add(f"{prm}{kraken}")
                    prm_set.add(prm)
                    kraken_set.add(kraken)

        if not prm_set:
            log("[INFO] Nessun PRM/Kraken estratto dai payment — flussi secondari saltati.", "warn")
        else:
            log(f"[INFO] {len(prm_set)} coppie distinte PRM/Kraken estratte.", "ok")
            lista_prm_kraken = ", ".join(f"'{v}'" for v in sorted(prm_kraken_set))
            lista_prm        = ", ".join(f"'{v}'" for v in sorted(prm_set))
            lista_kraken     = ", ".join(f"'{v}'" for v in sorted(kraken_set))

            for flow in FLOWS_REFERENCE_SECONDARY:
                if flags.get(flow, False):
                    _run_payment_query_gui(hub_conn, kraken_conn, integration_conn,
                                           flow, flags, lista_prm_kraken, lista_prm, lista_kraken, log)

        kraken_conn.close(); integration_conn.close(); hub_conn.close(); tunnel.stop()
        log("\n[INFO] Pipeline reference completata con successo.", "ok")
        on_done(success=True)

    except Exception as e:
        log(f"\n[ERRORE CRITICO] {e}", "error")
        on_done(success=False)


def _run_payment_query_gui(hub_conn, kraken_conn, integration_conn, flow, flags,
                            lista_prm_kraken, lista_prm, lista_kraken, log):
    import psycopg2
    table       = TARGET_TABLES_PAYMENT[flow]
    run_flag    = flags.get(flow, True)
    lbl         = QUERY_LABELS.get(flow, flow)

    log(f"\n── {lbl}  [{'RUN' if run_flag else 'SKIP'}] ──", "section")
    try:
        cur = integration_conn.cursor()
        cur.execute(f"TRUNCATE TABLE {table};")
        integration_conn.commit(); cur.close()
        log(f"[OK] Truncate '{table}'", "ok")

        if not run_flag:
            log("[SKIP] Query saltata (flag N).", "warn")
            return

        # Query da HUB (con fetch da hub_config): eseguite su Kraken
        if flow in _HUB_META_QUERIES:
            log(f"[INFO] Caricamento query '{lbl}' da hub_config_query_kraken ...", "info")
            query = load_query_from_hub(hub_conn, flow, lista_prm_kraken, lista_prm, lista_kraken)
            if query is None:
                log(f"[ERRORE] Query non trovata in hub_config_query_kraken per '{lbl}'.", "error")
                return
            hname = _HUB_META_QUERIES.get(flow, flow)
            log(f"[OK] Query {hname} recuperata da HUB PROD, procedo al lancio.", "ok")
            exec_conn = kraken_conn
        else:
            # Query payment: inline nello script, eseguite su HUB
            query = _PAYMENT_QUERIES[flow]
            query = query.replace("'LISTA_PRM_E_KRAKEN_ACCOUNT'", lista_prm_kraken)
            query = query.replace("'LISTA_KRAKEN_ACCOUNT'", lista_kraken)
            exec_conn = hub_conn

        cur = exec_conn.cursor()
        try:
            cur.execute(query)
        except Exception as e:
            cur.close()
            log(f"[ERRORE] Esecuzione query '{lbl}' fallita: {e}", "error")
            exec_conn.rollback()
            return
        columns = [d[0] for d in cur.description]
        rows = cur.fetchall(); cur.close()

        if flow in _HUB_META_QUERIES:
            rows = normalize_timestamps(rows)

        if flow == "query_agreement.sql":
            columns = ["pod" if c == "supply_point" else "update_at" if c == "updated_at" else c for c in columns]

        if flow in ("query_invoice_elec.sql", "query_invoice_gas.sql"):
            idx_drop = [i for i, c in enumerate(columns) if c == "created_at"]
            if idx_drop:
                columns = [c for i, c in enumerate(columns) if i not in idx_drop]
                rows = [tuple(v for i, v in enumerate(row) if i not in idx_drop) for row in rows]

        if flow == "query_payment_elec.sql":
            columns = ["prm_id" if c == "supply_point" else c for c in columns]
            idx_drop = [i for i, c in enumerate(columns) if c == "commodity"]
            if idx_drop:
                columns = [c for i,c in enumerate(columns) if i not in idx_drop]
                rows = [tuple(v for i,v in enumerate(row) if i not in idx_drop) for row in rows]

        if flow == "query_payment_gas.sql":
            columns = ["pce_id" if c == "supply_point" else c for c in columns]
            idx_drop = [i for i, c in enumerate(columns) if c == "commodity"]
            if idx_drop:
                columns = [c for i,c in enumerate(columns) if i not in idx_drop]
                rows = [tuple(v for i,v in enumerate(row) if i not in idx_drop) for row in rows]

        _commit_rows(integration_conn, table, columns, rows, log)

    except Exception as e:
        log(f"[ERRORE] '{lbl}': {e}", "error")
        try:
            hub_conn.rollback()
        except Exception:
            pass


def run_pipeline(flags, log, on_done, env="INTEGRATION"):
    import psycopg2
    _reload_env_into_os()

    try:
        # Pulizia output

        # Input
        try:
            lista_prm_kraken, lista_prm, lista_kraken = load_input_data()
        except (FileNotFoundError, ValueError) as e:
            log(f"[ERRORE] {e}", "error")
            on_done(success=False); return

        log(f"[INFO] Caricate righe dal file di input.", "info")

        # Source DB
        log(f"\n[INFO] Connessione Kraken: {os.getenv('KRAKEN_HOST')} / {os.getenv('KRAKEN_NAME')} ...", "info")
        try:
            kraken_conn = get_kraken_connection()
            log("[INFO] Connessione Kraken attiva ✓", "ok")
        except (psycopg2.OperationalError, EnvironmentError) as e:
            log(f"[ERRORE] Connessione Kraken fallita: {e}", "error")
            on_done(success=False); return

        # SSH Tunnel
        _ssh_host = os.getenv("SSH_RECETTE_HOST") if env == "RECETTE" else os.getenv("SSH_HOST")
        _db_host  = os.getenv("RECETTE_HOST")      if env == "RECETTE" else os.getenv("INTEGRATION_HOST")
        _db_name  = os.getenv("RECETTE_NAME")      if env == "RECETTE" else os.getenv("INTEGRATION_NAME")
        log(f"[INFO] Apertura tunnel SSH verso {_ssh_host} ...", "info")
        try:
            tunnel = open_ssh_tunnel(env)
            log(f"[INFO] Tunnel attivo su porta locale {tunnel.local_bind_port}", "info")
        except Exception as e:
            log(f"[ERRORE] Tunnel SSH fallito: {e}", "error")
            kraken_conn.close()
            on_done(success=False); return

        # Target DB
        try:
            integration_conn = get_integration_connection(tunnel, env)
            log(f"[INFO] Connessione {env.capitalize()}: {_db_host} / {_db_name} ✓", "ok")
        except psycopg2.OperationalError as e:
            log(f"[ERRORE] Connessione {env.capitalize()} fallita: {e}", "error")
            kraken_conn.close(); tunnel.stop()
            on_done(success=False); return

        # HUB (tutte le query)
        log(f"\n[INFO] Connessione HUB: {os.getenv('HUB_HOST')} ...", "info")
        try:
            hub_conn = get_hub_connection()
            log("[INFO] Connessione HUB attiva ✓", "ok")
        except (psycopg2.OperationalError, EnvironmentError) as e:
            log(f"[ERRORE] Connessione HUB fallita: {e}", "error")
            kraken_conn.close(); integration_conn.close(); tunnel.stop()
            on_done(success=False); return

        # Query payment
        for qf in PAYMENT_QUERY_FILES:
            _run_payment_query_gui(hub_conn, kraken_conn, integration_conn, qf, flags,
                                   lista_prm_kraken, lista_prm, lista_kraken, log)

        kraken_conn.close(); integration_conn.close(); hub_conn.close(); tunnel.stop()
        log("\n[INFO] Pipeline completata con successo.", "ok")
        on_done(success=True)

    except Exception as e:
        log(f"\n[ERRORE CRITICO] {e}", "error")
        on_done(success=False)


# ════════════════════════════════════════════════════════════════════════════
# ANALYSIS DATA EXTRACTOR — costanti e pipeline
# ════════════════════════════════════════════════════════════════════════════

_ADE_TARGET_TABLES = {
    "query_customer.sql":     "j_kraken_customer",
    "query_agreement.sql":    "j_kraken_agreement",
    "query_pp_elec.sql":      "j_kraken_payment_plan",
    "query_pp_gas.sql":       "j_kraken_payment_plan",
    "query_renewal.sql":      "j_kraken_renewal",
    "query_invoice_elec.sql": "j_kraken_invoice",
    "query_invoice_gas.sql":  "j_kraken_invoice",
    "query_payment_elec.sql": "j_kraken_payments",
    "query_payment_gas.sql":  "j_kraken_payments",
    "query_cheque_energie.sql":     "j_cheque_energie_registrati",
    "query_cheque_energie_kh.sql": "j_cheque_energie_utilizzati",
}

_ADE_QUERY_FLAGS = {
    "query_customer.sql":     "ADE_RUN_CUSTOMER",
    "query_agreement.sql":    "ADE_RUN_AGREEMENT",
    "query_pp_elec.sql":      "ADE_RUN_PP_ELEC",
    "query_pp_gas.sql":       "ADE_RUN_PP_GAS",
    "query_renewal.sql":      "ADE_RUN_RENEWAL",
    "query_invoice_elec.sql": "ADE_RUN_INVOICE_ELEC",
    "query_invoice_gas.sql":  "ADE_RUN_INVOICE_GAS",
    "query_payment_elec.sql": "ADE_RUN_PAYMENT_ELEC",
    "query_payment_gas.sql":  "ADE_RUN_PAYMENT_GAS",
    "query_cheque_energie.sql":     "ADE_RUN_CHEQUE_ENERGIE",
    "query_cheque_energie_kh.sql": "ADE_RUN_CHEQUE_ENERGIE_KH",
}

_ADE_QUERY_LABELS = {
    "query_customer.sql":     "Customer",
    "query_agreement.sql":    "Agreement",
    "query_pp_elec.sql":      "Payment Plan Elec",
    "query_pp_gas.sql":       "Payment Plan Gas",
    "query_renewal.sql":      "Renewal",
    "query_invoice_elec.sql": "Invoice Elec",
    "query_invoice_gas.sql":  "Invoice Gas",
    "query_payment_elec.sql": "Payment Elec",
    "query_payment_gas.sql":  "Payment Gas",
    "query_cheque_energie.sql":     "Cheque Energie KJ",
    "query_cheque_energie_kh.sql": "Cheque Energie KH",
}

# Righe UI: (etichetta, [flow1, flow2, ...])
_ADE_UI_ROWS = [
    ("Customer",        ["query_customer.sql"]),
    ("Agreement",       ["query_agreement.sql"]),
    ("Payment Plan",    ["query_pp_elec.sql", "query_pp_gas.sql"]),
    ("Renewal",         ["query_renewal.sql"]),
    ("Invoice",         ["query_invoice_elec.sql", "query_invoice_gas.sql"]),
    ("Payment",         ["query_payment_elec.sql", "query_payment_gas.sql"]),
    ("Cheque Energie KJ", ["query_cheque_energie.sql"]),
    ("Cheque Energie KH", ["query_cheque_energie_kh.sql"]),
]

# Mapping hname per Kraken Full Data Extractor — estende _HUB_META_QUERIES
# aggiungendo i payment con query dedicate (SPLUS)
_ADE_HUB_META_QUERIES = {
    **_HUB_META_QUERIES,
    "query_payment_elec.sql": "QUERY_PAYMENTS_ELEC_SPLUS",
    "query_payment_gas.sql":  "QUERY_PAYMENTS_GAS_SPLUS",
    "query_cheque_energie.sql":     "QUERY_CHEQUE_ENERGIE_REGISTER",
    "query_cheque_energie_kh.sql": "CHEQUE_ENERGIE_USE",
}

# Queries payment inline (non presenti in hub_config_query_kraken)
_ADE_PAYMENT_QUERIES = {}


# Chiavi .env per i tempi di esecuzione (secondi, float)
_ADE_TIME_KEYS = {
    "query_customer.sql":     "ADE_TIME_CUSTOMER",
    "query_agreement.sql":    "ADE_TIME_AGREEMENT",
    "query_pp_elec.sql":      "ADE_TIME_PP_ELEC",
    "query_pp_gas.sql":       "ADE_TIME_PP_GAS",
    "query_renewal.sql":      "ADE_TIME_RENEWAL",
    "query_invoice_elec.sql": "ADE_TIME_INVOICE_ELEC",
    "query_invoice_gas.sql":  "ADE_TIME_INVOICE_GAS",
    "query_payment_elec.sql": "ADE_TIME_PAYMENT_ELEC",
    "query_payment_gas.sql":  "ADE_TIME_PAYMENT_GAS",
    "query_cheque_energie.sql":     "ADE_TIME_CHEQUE_ENERGIE",
    "query_cheque_energie_kh.sql": "ADE_TIME_CHEQUE_ENERGIE_KH",
}


def _ade_fmt_time(seconds: float) -> str:
    """Formatta i secondi in stringa leggibile: ~45s / ~2m 30s / ~1h 05m 30s."""
    s = int(round(seconds))
    if s < 60:
        return f"~{s}s"
    m, s = divmod(s, 60)
    if m < 60:
        return f"~{m}m {s:02d}s" if s else f"~{m}m"
    h, m = divmod(m, 60)
    return f"~{h}h {m:02d}m {s:02d}s" if s else f"~{h}h {m:02d}m"


def _ade_load_query(hub_conn, flow: str):
    """
    Carica la query da hub_config_query_kraken e rimuove le righe contenenti
    DATETOINSERT — estrazione full, nessun filtro aggiuntivo.
    Usa _ADE_HUB_META_QUERIES che include anche i payment SPLUS.
    """
    hname = _ADE_HUB_META_QUERIES.get(flow)
    if hname is None:
        return None
    cur = hub_conn.cursor()
    cur.execute("""
        SELECT hquery
        FROM hub_config_query_kraken hcqk
        WHERE hcqk.hname = %s AND hcqk.henv = 'PROD' AND NOT (hcqk.hutemporal_bound)
    """, (hname,))
    row = cur.fetchone()
    cur.close()
    if not row or not row[0]:
        return None
    lines = []
    for l in row[0].strip().splitlines():
        if "DATETOINSERT" in l or "{COMMODITY}" in l:
            stripped = l.lstrip()
            if stripped.lower().startswith("and "):
                lines.append("    and 1=1")
            elif stripped.lower().startswith("where "):
                lines.append("    where 1=1")
            else:
                lines.append("    1=1")
        else:
            lines.append(l)
    return "\n".join(lines)


def _ade_get_kraken_connection():
    """
    Connessione Kraken con TCP keepalive abilitato — usata da Analysis Data
    Extractor per evitare che la connessione cada durante query molto lunghe.
    keepalives_idle=60  → invia il primo probe dopo 60s di inattività TCP
    keepalives_interval=10 → ogni 10s se non risponde
    keepalives_count=5  → dopo 5 probe senza risposta chiude
    """
    import psycopg2
    return psycopg2.connect(
        host=os.getenv("KRAKEN_HOST"),
        port=int(os.getenv("KRAKEN_PORT", "5432")),
        dbname=os.getenv("KRAKEN_NAME"),
        user=os.getenv("KRAKEN_USER"),
        password=os.getenv("KRAKEN_PASSWORD"),
        keepalives=1,
        keepalives_idle=60,
        keepalives_interval=10,
        keepalives_count=5,
    )


def run_ade_pipeline(flags, log, on_done, app=None):
    """
    Pipeline Kraken Full Data Extractor:
    - Sorgente: Kraken PROD
    - Destinazione: HUB PROD (connessione diretta, nessun tunnel SSH)
    - Per ogni flow selezionato: TRUNCATE + query Kraken + bulk insert su HUB
    - Le tabelle condivise (PP, Invoice, Payment) vengono troncate una sola volta
    - I tempi di esecuzione per flow vengono salvati nel .env come previsione
    """
    import psycopg2, time
    _reload_env_into_os()

    def _stopped():
        return app is not None and getattr(app, "_stop_requested", False)

    try:
        log(f"[INFO] Connessione Kraken: {os.getenv('KRAKEN_HOST')} / {os.getenv('KRAKEN_NAME')} ...", "info")
        try:
            kraken_conn = _ade_get_kraken_connection()
            log("[OK] Connessione Kraken attiva ✓", "ok")
        except (psycopg2.OperationalError, EnvironmentError) as e:
            log(f"[ERRORE] Connessione Kraken fallita: {e}", "error")
            on_done(success=False); return

        log(f"[INFO] Connessione HUB: {os.getenv('HUB_HOST')} / {os.getenv('HUB_NAME')} ...", "info")
        try:
            hub_conn = psycopg2.connect(
                host=os.getenv("HUB_HOST"),
                port=int(os.getenv("HUB_PORT", "5432")),
                dbname=os.getenv("HUB_NAME"),
                user=os.getenv("HUB_USER"),
                password=os.getenv("HUB_PASSWORD"),
                keepalives=1,
                keepalives_idle=60,
                keepalives_interval=10,
                keepalives_count=5,
            )
            log("[OK] Connessione HUB attiva ✓", "ok")
        except (psycopg2.OperationalError, EnvironmentError) as e:
            log(f"[ERRORE] Connessione HUB fallita: {e}", "error")
            kraken_conn.close(); on_done(success=False); return

        truncated_tables = set()
        failed_tables    = set()  # tabelle con errori: i flow successivi sulla stessa vengono saltati
        elapsed_times: dict = {}

        for flow, flag_key in _ADE_QUERY_FLAGS.items():
            if not flags.get(flow, False):
                continue

            if _stopped():
                log("\n[WARN] Pipeline interrotta dall'utente.", "warn")
                break

            lbl   = _ADE_QUERY_LABELS[flow]
            table = _ADE_TARGET_TABLES[flow]

            # Salta se la tabella ha già avuto un errore in un flow precedente
            if table in failed_tables:
                log(f"\n[WARN] Salto '{lbl}': tabella '{table}' in errore.", "warn")
                continue

            log(f"\n── {lbl}  [RUN] ──", "section")

            # TRUNCATE (una sola volta per tabella)
            if table not in truncated_tables:
                try:
                    cur = hub_conn.cursor()
                    cur.execute(f"TRUNCATE TABLE {table};")
                    hub_conn.commit(); cur.close()
                    log(f"[OK] Truncate '{table}'", "ok")
                    truncated_tables.add(table)
                except Exception as e:
                    hub_conn.rollback()
                    log(f"[ERRORE] Truncate '{table}' fallita: {e}", "error")
                    continue

            # Carica query
            log(f"[INFO] Caricamento query '{lbl}' da hub_config_query_kraken ...", "info")
            query = _ade_load_query(hub_conn, flow)
            if query is None:
                log(f"[ERRORE] Query non trovata per '{lbl}'.", "error")
                failed_tables.add(table)
                continue
            hname = _ADE_HUB_META_QUERIES.get(flow, flow)
            log(f"[OK] Query {hname} recuperata da HUB PROD, procedo al lancio.", "ok")
            exec_conn = kraken_conn

            # Esecuzione con misurazione tempo + heartbeat ogni 60s
            BATCH_SIZE = 10_000
            t_start = time.time()
            stop_hb = threading.Event()

            def _heartbeat(label=lbl, t0=t_start, stop=stop_hb):
                while not stop.wait(60):
                    if _stopped():
                        break
                    elapsed = time.time() - t0
                    log(f"⏳ {label} — in esecuzione... ({_ade_fmt_time(elapsed)})", "info")

            hb_thread = threading.Thread(target=_heartbeat, daemon=True)
            hb_thread.start()

            # Reconnect Kraken se necessario
            if kraken_conn.closed:
                log("[WARN] Connessione Kraken persa, riconnessione in corso...", "warn")
                try:
                    kraken_conn = _ade_get_kraken_connection()
                    exec_conn   = kraken_conn
                    log("[OK] Riconnessione Kraken riuscita.", "ok")
                except Exception as e:
                    log(f"[ERRORE] Riconnessione Kraken fallita: {e}", "error")
                    failed_tables.add(table)
                    continue

            # Cursore server-side (named) per evitare OOM su query con molte righe
            cur_name = f"ade_{flow.replace('.', '_').replace('-', '_')}_{int(t_start)}"
            cur = exec_conn.cursor(cur_name)
            cur.itersize = BATCH_SIZE
            try:
                cur.execute(query)

                # Con cursori server-side description è disponibile solo dopo il primo fetch
                first_batch = cur.fetchmany(BATCH_SIZE)
                columns = [d[0] for d in cur.description]

                # Rinomina colonne
                if flow == "query_agreement.sql":
                    columns = ["pod" if c == "supply_point" else
                               "update_at" if c == "updated_at" else c
                               for c in columns]
                elif flow == "query_pp_elec.sql":
                    columns = ["supply_point" if c == "prm" else c for c in columns]
                elif flow == "query_pp_gas.sql":
                    columns = ["supply_point" if c == "pce" else c for c in columns]
                elif flow == "query_invoice_elec.sql":
                    columns = ["supply_point" if c == "prm" else c for c in columns]
                elif flow == "query_invoice_gas.sql":
                    columns = ["supply_point" if c == "pce" else c for c in columns]
                elif flow == "query_payment_elec.sql":
                    columns = ["supply_point" if c == "prm_id" else c for c in columns]
                    columns = columns + ["commodity"]
                elif flow == "query_payment_gas.sql":
                    columns = ["supply_point" if c == "pce_id" else c for c in columns]
                    columns = columns + ["commodity"]

                # Valore commodity da aggiungere a ogni riga
                _commodity = ("ELEC" if flow == "query_payment_elec.sql"
                              else "GAS" if flow == "query_payment_gas.sql"
                              else None)

                total_rows = 0
                batch_iter = [first_batch] if first_batch else []
                while True:
                    if batch_iter:
                        batch = batch_iter.pop(0)
                    else:
                        if _stopped():
                            break
                        batch = cur.fetchmany(BATCH_SIZE)
                    if not batch:
                        break
                    batch = normalize_timestamps(batch)
                    if _commodity:
                        batch = [row + (_commodity,) for row in batch]

                    if hub_conn.closed:
                        log("[WARN] Connessione HUB persa, riconnessione in corso...", "warn")
                        try:
                            hub_conn = psycopg2.connect(
                                host=os.getenv("HUB_HOST"),
                                port=int(os.getenv("HUB_PORT", "5432")),
                                dbname=os.getenv("HUB_NAME"),
                                user=os.getenv("HUB_USER"),
                                password=os.getenv("HUB_PASSWORD"),
                                keepalives=1,
                                keepalives_idle=60,
                                keepalives_interval=10,
                                keepalives_count=5,
                            )
                            log("[OK] Riconnessione HUB riuscita.", "ok")
                        except Exception as e:
                            log(f"[ERRORE] Riconnessione HUB fallita: {e}", "error")
                            break

                    hub_cur = hub_conn.cursor()
                    try:
                        bulk_insert(hub_cur, table, columns, batch)
                        hub_conn.commit(); hub_cur.close()
                        total_rows += len(batch)
                    except Exception as e:
                        hub_conn.rollback(); hub_cur.close()
                        log(f"[ERRORE] Insert batch in '{table}' fallito: {e}", "error")
                        break

                cur.close()
            except Exception as e:
                stop_hb.set()
                try: cur.close()
                except Exception: pass
                exec_conn.rollback()
                log(f"[ERRORE] Esecuzione query '{lbl}' fallita: {e}", "error")
                failed_tables.add(table)
                continue
            finally:
                stop_hb.set()

            t_query = time.time() - t_start
            if total_rows > 0:
                log(f"[OK] {total_rows} righe estratte e inserite in {_ade_fmt_time(t_query)}.", "ok")
            else:
                log(f"[INFO] Nessuna riga da inserire in '{table}'.", "info")

            # Aggiorna commento tabella dopo l'ultimo flow che la scrive
            last_flow_for_table = {t: None for t in set(_ADE_TARGET_TABLES.values())}
            for f, t in _ADE_TARGET_TABLES.items():
                if flags.get(f, False):
                    last_flow_for_table[t] = f
            if last_flow_for_table.get(table) == flow and total_rows > 0:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    cur2 = hub_conn.cursor()
                    cur2.execute(f"COMMENT ON TABLE {table} IS 'Ultima estrazione: {ts}'")
                    hub_conn.commit(); cur2.close()
                except Exception:
                    pass

            t_total = time.time() - t_start
            elapsed_times[flow] = t_total
            log(f"[INFO] Tempo totale '{lbl}': {_ade_fmt_time(t_total)}.", "info")

        kraken_conn.close(); hub_conn.close()

        # Salva i tempi nel .env come previsione per i run futuri
        if elapsed_times:
            time_data = {_ADE_TIME_KEYS[flow]: f"{elapsed:.1f}"
                         for flow, elapsed in elapsed_times.items()
                         if flow in _ADE_TIME_KEYS}
            try:
                _write_env(time_data)
                _reload_env_into_os()
            except Exception:
                pass

        log("\n[INFO] Pipeline completata con successo.", "ok")
        on_done(success=True, elapsed=elapsed_times)

    except Exception as e:
        log(f"\n[ERRORE CRITICO] {e}", "error")
        on_done(success=False, elapsed={})


class KrakenFullDataExtractor(_AppBase):

    def __init__(self, master):
        super().__init__(master, bg=BG)
        self._log_queue = queue.Queue()
        self._running        = False
        self._stop_requested = False
        self._flags          = {}
        self._flag_labels    = {}
        self._time_labels    = {}  # row_label -> StringVar con tempo stimato
        self._build_ui()
        self._load_flags()
        self._load_time_labels()
        self._poll_log()

    def _build_ui(self):
        self._status_var = tkinter.StringVar(value="Pronto.")
        Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, side="bottom")
        self._status_lbl = Label(self, textvariable=self._status_var, bg=BG, fg=TEXT_SEC,
                                  font=("Consolas", 9), anchor="w", pady=5)
        self._status_lbl.pack(fill="x", padx=24, side="bottom")

        body = Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(12, 0))

        left_wrapper = Frame(body, bg=BG_CARD, bd=0, highlightthickness=1,
                             highlightbackground=BORDER)
        left_wrapper.pack(side="left", fill="y")
        left_wrapper.pack_propagate(False)
        left_wrapper.configure(width=230)

        left = Frame(left_wrapper, bg=BG_CARD)
        left.pack(fill="both", expand=True)

        hdr = Frame(left, bg=BG_CARD2)
        hdr.pack(fill="x")
        Label(hdr, text="▼", bg=BG_CARD2, fg=ACCENT,
              font=("Consolas", 9)).pack(side="left", padx=(8, 4), pady=6)
        Label(hdr, text="Tabelle", bg=BG_CARD2, fg=TEXT_PRI,
              font=("Consolas", 10, "bold")).pack(side="left", pady=6)
        Frame(left, bg=BORDER, height=1).pack(fill="x")

        for row_label, flows in _ADE_UI_ROWS:
            for flow in flows:
                if flow not in self._flags:
                    self._flags[flow] = BooleanVar(value=False)

            row = Frame(left, bg=BG_CARD)
            row.pack(fill="x", padx=10, pady=2)

            init_val = self._flags[flows[0]].get()
            box = Label(row, text="☑" if init_val else "☐",
                        bg=BG_CARD,
                        fg=ACCENT if init_val else TEXT_SEC,
                        font=("Consolas", 12), cursor="hand2", width=2)
            box.pack(side="left", padx=(0, 6))
            for flow in flows:
                self._flag_labels[flow] = box

            lbl = Label(row, text=row_label, bg=BG_CARD, fg=TEXT_PRI,
                        font=("Consolas", 10), anchor="w", cursor="hand2")
            lbl.pack(side="left", fill="x", expand=True)

            # Label tempo stimato (a destra)
            time_var = tkinter.StringVar(value="")
            self._time_labels[row_label] = (time_var, flows)
            time_lbl = Label(row, textvariable=time_var, bg=BG_CARD, fg=TEXT_SEC,
                  font=("Consolas", 8), anchor="e")
            time_lbl.pack(side="right", padx=(0, 2))
            self._attach_tooltip(time_lbl, "Tempo stimato basato sull'ultima esecuzione")

            def _make_tog(qs=flows, b=box):
                def _toggle(e=None):
                    new_val = not self._flags[qs[0]].get()
                    for q in qs:
                        self._flags[q].set(new_val)
                    b.configure(text="☑" if new_val else "☐",
                                fg=ACCENT if new_val else TEXT_SEC)
                    self._save_flags()
                return _toggle
            tog = _make_tog()
            box.bind("<Button-1>", tog)
            lbl.bind("<Button-1>", tog)

        Frame(left, bg=BORDER, height=1).pack(fill="x", padx=10, pady=(8, 0))

        btn_frame = Frame(left, bg=BG_CARD)
        btn_frame.pack(fill="x", padx=10, pady=(8, 4), side="bottom")

        row_btn = Frame(btn_frame, bg=BG_CARD)
        row_btn.pack(fill="x")
        self._btn = self._make_btn(row_btn, "▶  Avvia", self._start)
        self._btn.pack(side="left", fill="x", expand=True, padx=(0, 3))
        self._btn_stop = self._make_btn(row_btn, "■  Stop", self._stop, color=ERROR)
        self._btn_stop.pack(side="left", fill="x", expand=True, padx=(3, 0))
        self._btn_stop.configure(fg=TEXT_SEC, cursor="arrow")

        right = Frame(body, bg=BG_CARD, bd=0, highlightthickness=1,
                      highlightbackground=BORDER)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self._build_log_panel(right, on_clear=self._clear_log)

    def _load_flags(self):
        data = _read_env_raw()
        for flow, flag_key in _ADE_QUERY_FLAGS.items():
            val = data.get(flag_key, "N").strip().upper() == "Y"
            self._flags[flow].set(val)
            box = self._flag_labels.get(flow)
            if box:
                box.configure(text="☑" if val else "☐",
                              fg=ACCENT if val else TEXT_SEC)

    def _load_time_labels(self):
        """Legge i tempi salvati nel .env e aggiorna le label di previsione."""
        data = _read_env_raw()
        for row_label, (time_var, flows) in self._time_labels.items():
            total = 0.0
            found = False
            for flow in flows:
                key = _ADE_TIME_KEYS.get(flow)
                if key and key in data:
                    try:
                        total += float(data[key])
                        found = True
                    except ValueError:
                        pass
            time_var.set(_ade_fmt_time(total) if found else "")

    def _save_flags(self):
        data = {_ADE_QUERY_FLAGS[flow]: ("Y" if var.get() else "N")
                for flow, var in self._flags.items()}
        try:
            _write_env(data)
            _reload_env_into_os()
        except Exception as e:
            messagebox.showerror("Errore salvataggio flags", str(e))

    def _stop(self):
        if not self._running:
            return
        self._stop_requested = True
        self._btn_stop.configure(fg=TEXT_SEC, cursor="arrow")
        self._status_var.set("Stop richiesto...")

    def _on_done(self, success: bool, elapsed: dict = {}):
        self._running        = False
        self._stop_requested = False
        color = SUCCESS if success else ERROR
        self._status_var.set("✓ Completato." if success else "✗ Terminato con errori.")
        self._btn.configure(fg=color, cursor="hand2")
        self._btn_stop.configure(fg=TEXT_SEC, cursor="arrow")
        self.after(3000, lambda: self._btn.configure(fg=ACCENT))
        if elapsed:
            self.after(0, self._load_time_labels)

    def _start(self):
        if self._running:
            return
        if not any(var.get() for var in self._flags.values()):
            self._status_var.set("⚠ Seleziona almeno un'entità.")
            return
        self._running        = True
        self._stop_requested = False
        self._btn.configure(fg=TEXT_SEC, cursor="arrow")
        self._btn_stop.configure(fg=ERROR, cursor="hand2")
        self._status_var.set("In esecuzione...")
        flags = {flow: var.get() for flow, var in self._flags.items()}
        threading.Thread(
            target=run_ade_pipeline,
            args=(flags, self._enqueue_log, self._on_done, self),
            daemon=True,
        ).start()


# ════════════════════════════════════════════════════════════════════════════
# GUI
# ════════════════════════════════════════════════════════════════════════════



# ════════════════════════════════════════════════════════════════════════════
# HUB CONSOLE
# ════════════════════════════════════════════════════════════════════════════

_HC_FLAGS = [
    ("CHANGE_BILLING_FREQUENCY_IS_ACTIVE", "Change Billing Frequency"),
    ("CUSTOMER_IS_ACTIVE",                 "Customer"),
    ("AGREEMENT_IS_ACTIVE",                "Agreement"),
    ("PP_IS_ACTIVE",                       "Payment Plan"),
    ("INVOICE_IS_ACTIVE",                  "Invoice"),
    ("PAYMENTS_IS_ACTIVE",                 "Payments"),
    ("CHEQUE_ENERGIE_IS_ACTIVE",           "Cheque Energie"),
]

_HC_RUN_KEY = "B2C_SAP_INTEGRATION_IS_ACTIVE"


class HubConsole(_AppBase):

    def __init__(self, master):
        super().__init__(master, bg=BG)
        self._log_queue  = queue.Queue()
        self._running    = False
        self._flag_vars  = {}   # hkey -> BooleanVar
        self._flag_boxes = {}   # hkey -> Label (checkbox widget)
        self._build_ui()
        self._load_flags_from_hub()
        self._poll_log()
        self._schedule_flag_refresh()

    def _build_ui(self):
        self._status_var = tkinter.StringVar(value="Pronto.")
        Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, side="bottom")
        Label(self, textvariable=self._status_var, bg=BG, fg=TEXT_SEC,
              font=("Consolas", 9), anchor="w", pady=5).pack(fill="x", padx=24, side="bottom")

        body = Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(12, 0))

        left_w = Frame(body, bg=BG_CARD, highlightthickness=1,
                       highlightbackground=BORDER)
        left_w.pack(side="left", fill="y")
        left_w.pack_propagate(False)
        left_w.configure(width=230)

        left = Frame(left_w, bg=BG_CARD)
        left.pack(fill="both", expand=True)

        hdr = Frame(left, bg=BG_CARD2)
        hdr.pack(fill="x")
        Label(hdr, text="▼", bg=BG_CARD2, fg=ACCENT,
              font=("Consolas", 9)).pack(side="left", padx=(8, 4), pady=6)
        Label(hdr, text="Flussi B2C", bg=BG_CARD2, fg=TEXT_PRI,
              font=("Consolas", 10, "bold")).pack(side="left", pady=6)
        Frame(left, bg=BORDER, height=1).pack(fill="x")

        for hkey, label in _HC_FLAGS:
            self._flag_vars[hkey] = BooleanVar(value=False)

            row = Frame(left, bg=BG_CARD)
            row.pack(fill="x", padx=10, pady=2)

            box = Label(row, text="☐", bg=BG_CARD, fg=TEXT_SEC,
                        font=("Consolas", 12), cursor="hand2", width=2)
            box.pack(side="left", padx=(0, 6))
            self._flag_boxes[hkey] = box

            lbl = Label(row, text=label, bg=BG_CARD, fg=TEXT_PRI,
                        font=("Consolas", 10), anchor="w", cursor="hand2")
            lbl.pack(side="left", fill="x", expand=True)

            def _make_tog(key=hkey, b=box):
                def _toggle(e=None):
                    new_val = not self._flag_vars[key].get()
                    self._flag_vars[key].set(new_val)
                    b.configure(text="☑" if new_val else "☐",
                                fg=ACCENT if new_val else TEXT_SEC)
                    self._update_flag_on_hub(key, new_val)
                return _toggle
            tog = _make_tog()
            box.bind("<Button-1>", tog)
            lbl.bind("<Button-1>", tog)

        Frame(left, bg=BORDER, height=1).pack(fill="x", padx=10, pady=(8, 0))

        cleanup_frame = Frame(left, bg=BG_CARD)
        cleanup_frame.pack(fill="x", padx=10, pady=(10, 0))
        Label(cleanup_frame, text="Cleanup", bg=BG_CARD, fg=TEXT_SEC,
              font=("Consolas", 8), anchor="w").pack(fill="x", pady=(0, 4))
        self._make_btn(cleanup_frame, "🧹  Pulisci B2C Customer",
                       lambda: self._run_cleanup("select run_cleanup_b2c_customer();"),
                       color=WARNING).pack(fill="x", pady=(0, 3))
        self._make_btn(cleanup_frame, "🧹  Pulisci B2C",
                       lambda: self._run_cleanup("select run_cleanup_b2c();"),
                       color=WARNING).pack(fill="x", pady=(0, 3))
        self._make_btn(cleanup_frame, "🧹  Pulisci B2C Input",
                       lambda: self._run_cleanup("select run_cleanup_b2c_kraken_input();"),
                       color=WARNING).pack(fill="x")

        Frame(left, bg=BORDER, height=1).pack(fill="x", padx=10, pady=(10, 0))

        btn_frame = Frame(left, bg=BG_CARD)
        btn_frame.pack(fill="x", padx=10, pady=(8, 4), side="bottom")
        self._btn = self._make_btn(btn_frame, "▶  Avvia Run", self._start)
        self._btn.pack(fill="x")

        right = Frame(body, bg=BG_CARD, highlightthickness=1,
                      highlightbackground=BORDER)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self._build_log_panel(right, on_clear=self._clear_log)

    def _schedule_flag_refresh(self):
        """Rilegge i flag da HUB ogni 30 secondi in background."""
        def _refresh():
            threading.Thread(target=self._load_flags_from_hub,
                             daemon=True).start()
            self._refresh_job = self.after(30_000, _refresh)
        self._refresh_job = self.after(30_000, _refresh)

    def _get_int_conn(self):
        """Apre tunnel SSH e restituisce (tunnel, conn) per l'ambiente corrente."""
        env = _get_target_env()
        tunnel = open_ssh_tunnel(env)
        conn   = get_integration_connection(tunnel, env)
        return tunnel, conn

    def _load_flags_from_hub(self):
        """Legge i flag dalla hub_config_db e aggiorna le checkbox."""
        try:
            tunnel, conn = self._get_int_conn()
            keys = [k for k, _ in _HC_FLAGS]
            placeholders = ",".join(["%s"] * len(keys))
            cur = conn.cursor()
            cur.execute(
                f"SELECT hkey, hvalue FROM hub_config_db WHERE hkey IN ({placeholders})",
                keys)
            rows = {r[0]: r[1] for r in cur.fetchall()}
            cur.close(); conn.close(); tunnel.stop()
            for hkey, _ in _HC_FLAGS:
                val = rows.get(hkey, "N").strip().upper() == "Y"
                self._flag_vars[hkey].set(val)
                box = self._flag_boxes[hkey]
                box.configure(text="☑" if val else "☐",
                              fg=ACCENT if val else TEXT_SEC)
            self._status_var.set("✓ Flag caricati da HUB.")
        except Exception as e:
            self._status_var.set(f"⚠ Impossibile leggere i flag: {e}")

    def _update_flag_on_hub(self, hkey: str, value: bool):
        """Aggiorna un singolo flag su hub_config_db in background."""
        hvalue = "Y" if value else "N"
        def _worker():
            try:
                tunnel, conn = self._get_int_conn()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE hub_config_db SET hvalue = %s WHERE hkey = %s",
                    (hvalue, hkey))
                conn.commit(); cur.close(); conn.close(); tunnel.stop()
                self.after(0, lambda: self._status_var.set(f"✓ {hkey} → {hvalue}"))
            except Exception as e:
                self.after(0, lambda: self._status_var.set(f"⚠ Errore update {hkey}: {e}"))
        threading.Thread(target=_worker, daemon=True).start()

    def _run_cleanup(self, query: str):
        """Chiede conferma poi esegue una funzione di cleanup in background."""
        label = query.strip().rstrip(";").replace("select ", "").replace("()", "")
        if not messagebox.askyesno("Conferma cleanup",
                                   f"Sei sicuro di voler eseguire:\n\n  {label}"):
            return
        def _worker():
            try:
                tunnel, conn = self._get_int_conn()
                cur = conn.cursor()
                cur.execute(query)
                conn.commit(); cur.close(); conn.close(); tunnel.stop()
                self._enqueue_log(f"[OK] {query.strip()}", "ok")
                self.after(0, lambda: self._status_var.set("✓ Cleanup completato."))
            except Exception as e:
                self._enqueue_log(f"[ERRORE] {e}", "error")
                self.after(0, lambda: self._status_var.set(f"⚠ Errore cleanup: {e}"))
        threading.Thread(target=_worker, daemon=True).start()

    def _start(self):
        if self._running:
            return
        self._running = True
        self._btn.configure(fg=TEXT_SEC, cursor="arrow")
        self._status_var.set("Avvio run...")
        threading.Thread(target=self._run_worker, daemon=True).start()

    def _run_worker(self):
        try:
            tunnel, conn = self._get_int_conn()
            cur = conn.cursor()
            cur.execute(
                "UPDATE hub_config_db SET hvalue = 'Y' WHERE hkey = %s",
                (_HC_RUN_KEY,))
            conn.commit(); cur.close(); conn.close(); tunnel.stop()
            self._enqueue_log("[OK] Run avviato: B2C_SAP_INTEGRATION_IS_ACTIVE → Y", "ok")
            self.after(0, self._done, True)
        except Exception as e:
            self._enqueue_log(f"[ERRORE] {e}", "error")
            self.after(0, self._done, False)

    def _done(self, success: bool):
        self._running = False
        self._status_var.set("✓ Completato." if success else "✗ Errore.")
        self._btn.configure(fg=SUCCESS if success else ERROR, cursor="hand2")
        self.after(3000, lambda: self._btn.configure(fg=ACCENT))



# ════════════════════════════════════════════════════════════════════════════
# BONIFICA PROD
# ════════════════════════════════════════════════════════════════════════════

_BP_FLAGS = [
    ("CUSTOMER",      "Customer"),
    ("AGREEMENT",     "Agreement"),
    ("PAYMENT_PLANS", "Payment Plans"),
    ("INVOICE",       "Invoice"),
]

_BP_ENV_KEYS = {
    "CUSTOMER":      "BP_RUN_CUSTOMER",
    "AGREEMENT":     "BP_RUN_AGREEMENT",
    "PAYMENT_PLANS": "BP_RUN_PAYMENT_PLANS",
    "INVOICE":       "BP_RUN_INVOICE",
}


class KrakenDataExtractor(_AppBase):

    def __init__(self, master):
        super().__init__(master, bg=BG)


        self._log_queue: queue.Queue           = queue.Queue()
        self._flags:            dict           = {}
        self._flags_identifier: dict           = {}
        self._flags_reference:  dict           = {}
        self._running    = False
        self._mode       = MODE_PRM

        self._build_ui()
        self._load_flags_from_env()
        self._load_input_into_table()
        self._load_identifier_into_table()
        self._load_reference_into_table()
        self._poll_log()


    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TNotebook",
                        background=BG, borderwidth=0, tabmargins=[0, 0, 0, 0])
        style.configure("Dark.TNotebook.Tab",
                        background=BG_CARD, foreground=TEXT_SEC,
                        font=("Consolas", 10), padding=[16, 6],
                        borderwidth=0)
        style.map("Dark.TNotebook.Tab",
                  background=[("selected", BG_CARD2)],
                  foreground=[("selected", TEXT_PRI)],
                  padding=[("selected", [16, 8]), ("!selected", [16, 6])])
        style.configure("Mode.TNotebook",
                        background=BG_CARD2, borderwidth=0, tabmargins=[0, 0, 0, 0])
        style.configure("Mode.TNotebook.Tab",
                        background=BG_CARD, foreground=TEXT_SEC,
                        font=("Consolas", 9), padding=[12, 2],
                        borderwidth=0)
        style.map("Mode.TNotebook.Tab",
                  background=[("selected", ACCENT2), ("!selected", BG_CARD)],
                  foreground=[("selected", TEXT_PRI), ("!selected", TEXT_SEC)],
                  padding=[("selected", [12, 5]), ("!selected", [12, 2])])

        nb = ttk.Notebook(self, style="Dark.TNotebook")
        nb.pack(fill="both", expand=True, padx=24, pady=(12, 0))

        tab_pipeline = Frame(nb, bg=BG)
        nb.add(tab_pipeline, text="  ▶  Pipeline  ")
        self._build_pipeline_tab(tab_pipeline)

        tab_input = Frame(nb, bg=BG)
        nb.add(tab_input, text="  📋  Data Input  ")
        self._build_input_tab(tab_input)


        self._status_var = tkinter.StringVar(value="Pronto.")
        self._status_lbl = Label(self, textvariable=self._status_var, bg=BG, fg=TEXT_SEC,
                                  font=("Consolas", 9), anchor="w", pady=5)
        self._status_lbl.pack(fill="x", padx=24, side="bottom")
        Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, side="bottom")

    # ── Tab Pipeline ─────────────────────────────────────────────────────

    def _build_pipeline_tab(self, parent):
        body = Frame(parent, bg=BG)
        body.pack(fill="both", expand=True)

        left_wrapper = Frame(body, bg=BG_CARD, bd=0, highlightthickness=1,
                             highlightbackground=BORDER)
        left_wrapper.pack(side="left", fill="y")
        left_wrapper.pack_propagate(False)
        left_wrapper.configure(width=220)

        sidebar = Frame(left_wrapper, bg=BG_CARD)
        sidebar.pack(fill="both", expand=True)

        self._accordion_sections = []  # lista di (content, arrow_var, hdr_frame)

        def _make_accordion(title, mode_const, btn_attr, flag_rows, flags_dict,
                            flag_labels_attr, default_open=False):
            hdr_frame = Frame(sidebar, bg=BG_CARD2, cursor="hand2")
            hdr_frame.pack(fill="x")

            arrow_var = tkinter.StringVar(value="▼" if default_open else "▶")
            Label(hdr_frame, textvariable=arrow_var, bg=BG_CARD2, fg=ACCENT,
                  font=("Consolas", 9)).pack(side="left", padx=(8, 4), pady=6)
            Label(hdr_frame, text=title, bg=BG_CARD2, fg=TEXT_PRI,
                  font=("Consolas", 10, "bold")).pack(side="left", pady=6)

            Frame(sidebar, bg=BORDER, height=1).pack(fill="x")

            content = Frame(sidebar, bg=BG_CARD)
            if default_open:
                content.pack(fill="x")

            self._accordion_sections.append((content, arrow_var))

            flag_labels = {}
            setattr(self, flag_labels_attr, flag_labels)

            for row_label, flows in flag_rows:
                for qf in flows:
                    if qf not in flags_dict:
                        flags_dict[qf] = BooleanVar(value=False)

                row = Frame(content, bg=BG_CARD)
                row.pack(fill="x", padx=10, pady=2)

                init_val = flags_dict[flows[0]].get()
                box = Label(row, text="☑" if init_val else "☐",
                            bg=BG_CARD,
                            fg=ACCENT if init_val else TEXT_SEC,
                            font=("Consolas", 12), cursor="hand2", width=2)
                box.pack(side="left", padx=(0, 6))
                for qf in flows:
                    flag_labels[qf] = box

                lbl = Label(row, text=row_label, bg=BG_CARD, fg=TEXT_PRI,
                            font=("Consolas", 10), anchor="w", cursor="hand2")
                lbl.pack(side="left", fill="x", expand=True)

                def _make_tog(qs=flows, b=box, fd=flags_dict):
                    def _toggle(e=None):
                        new_val = not fd[qs[0]].get()
                        for q in qs:
                            fd[q].set(new_val)
                        b.configure(text="☑" if new_val else "☐",
                                    fg=ACCENT if new_val else TEXT_SEC)
                        self._save_flags()
                    return _toggle
                tog = _make_tog()
                box.bind("<Button-1>", tog)
                lbl.bind("<Button-1>", tog)

            Frame(content, bg=BORDER, height=1).pack(fill="x", padx=10, pady=(8, 0))
            btn = self._make_btn(content, "▶  Avvia", self._start)
            btn.pack(fill="x", padx=10, pady=(8, 4))
            setattr(self, btn_attr, btn)
            Frame(sidebar, bg=BORDER, height=1).pack(fill="x")

            # Registra questa sezione per il comportamento mutualmente esclusivo
            self._accordion_sections.append((content, arrow_var))

            def _toggle_accordion(e=None):
                self._mode = mode_const
                self._status_var.set(f"Modalità: {mode_const}")
                # Chiude tutte le altre sezioni
                for c, av in self._accordion_sections:
                    if c is not content:
                        c.pack_forget()
                        av.set("▶")
                # Apre questa
                if not content.winfo_ismapped():
                    content.pack(fill="x", after=hdr_frame)
                    arrow_var.set("▼")

            hdr_frame.bind("<Button-1>", _toggle_accordion)
            for child in hdr_frame.winfo_children():
                child.bind("<Button-1>", _toggle_accordion)

        self._accordion_sections = []

        _make_accordion(
            "PRM", MODE_PRM, "_btn",
            [
                ("Customer",          ["query_customer.sql"]),
                ("Agreement",         ["query_agreement.sql"]),
                ("Payment Plan",      ["query_pp_elec.sql", "query_pp_gas.sql"]),
                ("Renewal",           ["query_renewal.sql"]),
                ("Invoice",           ["query_invoice_elec.sql", "query_invoice_gas.sql"]),
                ("Payment",           ["query_payment_elec.sql", "query_payment_gas.sql"]),
                ("Cheque Energie KJ", ["query_cheque_kj.sql"]),
                ("Cheque Energie KH", ["query_cheque_kh.sql"]),
            ],
            self._flags, "_flag_labels", default_open=True
        )

        _make_accordion(
            "Identifier", MODE_IDENTIFIER, "_btn_id",
            [
                ("Customer",          ["query_customer.sql"]),
                ("Agreement",         ["query_agreement.sql"]),
                ("Payment Plan",      ["query_pp_elec.sql", "query_pp_gas.sql"]),
                ("Renewal",           ["query_renewal.sql"]),
                ("Payment",           ["query_payment_elec.sql", "query_payment_gas.sql"]),
                ("Cheque Energie KJ", ["query_cheque_kj.sql"]),
                ("Cheque Energie KH", ["query_cheque_kh.sql"]),
            ],
            self._flags_identifier, "_flag_labels_id", default_open=False
        )

        _make_accordion(
            "Reference", MODE_REFERENCE, "_btn_ref",
            [
                ("Customer",          ["query_customer.sql"]),
                ("Agreement",         ["query_agreement.sql"]),
                ("Payment Plan",      ["query_pp_elec.sql", "query_pp_gas.sql"]),
                ("Renewal",           ["query_renewal.sql"]),
                ("Invoice",           ["query_invoice_elec.sql", "query_invoice_gas.sql"]),
                ("Cheque Energie KJ", ["query_cheque_kj.sql"]),
                ("Cheque Energie KH", ["query_cheque_kh.sql"]),
            ],
            self._flags_reference, "_flag_labels_ref", default_open=False
        )

        right = Frame(body, bg=BG_CARD, bd=0, highlightthickness=1,
                      highlightbackground=BORDER)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))

        self._build_log_panel(right, on_clear=self._clear_log)

    # ── Tab Impostazioni ─────────────────────────────────────────────────


    # ── Tab Data Input ────────────────────────────────────────────────────

    def _build_input_tab(self, parent):
        mode_nb = ttk.Notebook(parent, style="Mode.TNotebook")
        mode_nb.pack(fill="both", expand=True)

        tab_prm = Frame(mode_nb, bg=BG)
        mode_nb.add(tab_prm, text="  PRM  ")
        tab_id  = Frame(mode_nb, bg=BG)
        mode_nb.add(tab_id,  text="  Identifier  ")
        tab_ref = Frame(mode_nb, bg=BG)
        mode_nb.add(tab_ref, text="  Reference  ")

        # ── PRM ──────────────────────────────────────────────────────────
        hdr = Frame(tab_prm, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(12, 0))
        Label(hdr, text="Data Input  —  PRM", bg=BG, fg=TEXT_PRI,
              font=("Consolas", 11, "bold")).pack(side="left")
        Frame(tab_prm, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(8, 0))
        Label(tab_prm, text="Ogni riga rappresenta una coppia PRM ; Kraken Account da processare.",
              bg=BG, fg=TEXT_SEC, font=("Consolas", 9), anchor="w", pady=6).pack(fill="x", padx=16)

        toolbar = Frame(tab_prm, bg=BG)
        toolbar.pack(fill="x", padx=16, pady=(0, 6))
        self._make_btn(toolbar, "✏️  Modifica / Aggiungi", self._input_paste_popup, color=SUCCESS).pack(side="left", padx=(0, 6))
        self._make_btn(toolbar, "🗑  Svuota righe", self._input_clear_all, color=ERROR).pack(side="left")

        table_frame = Frame(tab_prm, bg=BG_CARD,
                            highlightthickness=1, highlightbackground=BORDER)
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        style = ttk.Style()
        style.configure("Input.Treeview",
                        background=BG_CARD, foreground=TEXT_PRI,
                        fieldbackground=BG_CARD, rowheight=26,
                        font=("Consolas", 10), borderwidth=0)
        style.configure("Input.Treeview.Heading",
                        background=BG_CARD2, foreground=ACCENT,
                        font=("Consolas", 9, "bold"), relief="flat")
        style.map("Input.Treeview",
                  background=[("selected", ACCENT2)],
                  foreground=[("selected", TEXT_PRI)])

        cols = ("prm", "kraken")
        self._input_tree = ttk.Treeview(table_frame, columns=cols,
                                        show="headings", style="Input.Treeview",
                                        selectmode="browse")
        self._input_tree.heading("prm",    text="PRM")
        self._input_tree.heading("kraken", text="Kraken Account")
        self._input_tree.column("prm",    width=260, minwidth=120, anchor="w")
        self._input_tree.column("kraken", width=260, minwidth=120, anchor="w")

        vsb = ttk.Scrollbar(table_frame, orient="vertical",
                            command=self._input_tree.yview,
                            style="Dark.Vertical.TScrollbar")
        def _prm_scroll(f, l):
            if float(f) <= 0.0 and float(l) >= 1.0:
                if vsb.winfo_ismapped():
                    vsb.after(1, vsb.pack_forget)
            else:
                if not vsb.winfo_ismapped():
                    vsb.after(1, lambda: vsb.pack(side="right", fill="y", before=self._input_tree))
            vsb.set(f, l)
        vsb.pack(side="right", fill="y")
        self._input_tree.configure(yscrollcommand=_prm_scroll)
        self._input_tree.pack(fill="both", expand=True)
        self._input_tree.bind("<Double-1>", self._input_edit_cell)

        footer = Frame(tab_prm, bg=BG)
        footer.pack(fill="x", padx=16, pady=(0, 4))
        self._input_count_var = tkinter.StringVar(value="")
        Label(footer, textvariable=self._input_count_var,
              bg=BG, fg=TEXT_SEC, font=("Consolas", 9)).pack(side="left")

        # ── Identifier ───────────────────────────────────────────────────
        hdr2 = Frame(tab_id, bg=BG)
        hdr2.pack(fill="x", padx=16, pady=(12, 0))
        Label(hdr2, text="Data Input  —  Identifier", bg=BG, fg=TEXT_PRI,
              font=("Consolas", 11, "bold")).pack(side="left")
        Frame(tab_id, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(8, 0))
        Label(tab_id, text="Ogni riga rappresenta un document identifier da processare.",
              bg=BG, fg=TEXT_SEC, font=("Consolas", 9), anchor="w", pady=6).pack(fill="x", padx=16)

        toolbar2 = Frame(tab_id, bg=BG)
        toolbar2.pack(fill="x", padx=16, pady=(0, 6))
        self._make_btn(toolbar2, "✏️  Modifica / Aggiungi", self._identifier_paste_popup, color=SUCCESS).pack(side="left", padx=(0, 6))
        self._make_btn(toolbar2, "🗑  Svuota righe", self._identifier_clear_all, color=ERROR).pack(side="left")

        table_frame2 = Frame(tab_id, bg=BG_CARD,
                             highlightthickness=1, highlightbackground=BORDER)
        table_frame2.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self._id_tree = ttk.Treeview(table_frame2, columns=("identifier",),
                                     show="headings", style="Input.Treeview",
                                     selectmode="browse")
        self._id_tree.heading("identifier", text="Document Identifier")
        self._id_tree.column("identifier", width=500, minwidth=200, anchor="w")

        vsb2 = ttk.Scrollbar(table_frame2, orient="vertical",
                             command=self._id_tree.yview,
                             style="Dark.Vertical.TScrollbar")
        def _id_scroll(f, l):
            if float(f) <= 0.0 and float(l) >= 1.0:
                if vsb2.winfo_ismapped():
                    vsb2.after(1, vsb2.pack_forget)
            else:
                if not vsb2.winfo_ismapped():
                    vsb2.after(1, lambda: vsb2.pack(side="right", fill="y", before=self._id_tree))
            vsb2.set(f, l)
        vsb2.pack(side="right", fill="y")
        self._id_tree.configure(yscrollcommand=_id_scroll)
        self._id_tree.pack(fill="both", expand=True)

        footer2 = Frame(tab_id, bg=BG)
        footer2.pack(fill="x", padx=16, pady=(0, 4))
        self._id_count_var = tkinter.StringVar(value="")
        Label(footer2, textvariable=self._id_count_var,
              bg=BG, fg=TEXT_SEC, font=("Consolas", 9)).pack(side="left")

        # ── Reference ────────────────────────────────────────────────────
        hdr3 = Frame(tab_ref, bg=BG)
        hdr3.pack(fill="x", padx=16, pady=(12, 0))
        Label(hdr3, text="Data Input  —  Reference", bg=BG, fg=TEXT_PRI,
              font=("Consolas", 11, "bold")).pack(side="left")
        Frame(tab_ref, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(8, 0))
        Label(tab_ref, text="Ogni riga rappresenta una payment reference da processare.",
              bg=BG, fg=TEXT_SEC, font=("Consolas", 9), anchor="w", pady=6).pack(fill="x", padx=16)

        toolbar3 = Frame(tab_ref, bg=BG)
        toolbar3.pack(fill="x", padx=16, pady=(0, 6))
        self._make_btn(toolbar3, "✏️  Modifica / Aggiungi", self._reference_paste_popup, color=SUCCESS).pack(side="left", padx=(0, 6))
        self._make_btn(toolbar3, "🗑  Svuota righe", self._reference_clear_all, color=ERROR).pack(side="left")

        table_frame3 = Frame(tab_ref, bg=BG_CARD,
                             highlightthickness=1, highlightbackground=BORDER)
        table_frame3.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self._ref_tree = ttk.Treeview(table_frame3, columns=("reference",),
                                      show="headings", style="Input.Treeview",
                                      selectmode="browse")
        self._ref_tree.heading("reference", text="Payment Reference")
        self._ref_tree.column("reference", width=500, minwidth=200, anchor="w")

        vsb3 = ttk.Scrollbar(table_frame3, orient="vertical",
                             command=self._ref_tree.yview,
                             style="Dark.Vertical.TScrollbar")
        def _ref_scroll(f, l):
            if float(f) <= 0.0 and float(l) >= 1.0:
                if vsb3.winfo_ismapped():
                    vsb3.after(1, vsb3.pack_forget)
            else:
                if not vsb3.winfo_ismapped():
                    vsb3.after(1, lambda: vsb3.pack(side="right", fill="y", before=self._ref_tree))
            vsb3.set(f, l)
        vsb3.pack(side="right", fill="y")
        self._ref_tree.configure(yscrollcommand=_ref_scroll)
        self._ref_tree.pack(fill="both", expand=True)

        footer3 = Frame(tab_ref, bg=BG)
        footer3.pack(fill="x", padx=16, pady=(0, 4))
        self._ref_count_var = tkinter.StringVar(value="")
        Label(footer3, textvariable=self._ref_count_var,
              bg=BG, fg=TEXT_SEC, font=("Consolas", 9)).pack(side="left")




    def _load_reference_into_table(self):
        if not hasattr(self, "_ref_tree"):
            return
        for row in self._ref_tree.get_children():
            self._ref_tree.delete(row)
        if not INPUT_FILE_REFERENCE.exists():
            self._ref_count_var.set("File non trovato — verrà creato al salvataggio.")
            return
        lines = INPUT_FILE_REFERENCE.read_text(encoding="utf-8").strip().splitlines()
        count = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            self._ref_tree.insert("", "end", values=(line,))
            count += 1
        self._ref_count_var.set(f"{count} reference caricate.")

    def _reference_paste_popup(self):
        self._paste_popup(
            title="Modifica / Aggiungi reference",
            subtitle="Una riga per reference. Righe vuote verranno ignorate.",
            tree=self._ref_tree, count_var=self._ref_count_var,
            empty_warning="⚠  Nessuna reference trovata.",
            count_label_fn=lambda n: f"{n} reference.",
            save_fn=self._save_reference_input,
        )

    def _identifier_paste_popup(self):
        self._paste_popup(
            title="Modifica / Aggiungi identifier",
            subtitle="Una riga per identifier. Righe vuote verranno ignorate.",
            tree=self._id_tree, count_var=self._id_count_var,
            empty_warning="⚠  Nessun identifier trovato.",
            count_label_fn=lambda n: f"{n} identifier.",
            save_fn=self._save_identifier_input,
        )

    def _input_paste_popup(self):
        self._paste_popup(
            title="Modifica / Aggiungi dati",
            subtitle=("Modifica, aggiungi o cancella righe. Formato: PRM;KrakenAccount\n"
                      "Le righe non valide verranno evidenziate in arancione."),
            tree=self._input_tree, count_var=self._input_count_var,
            empty_warning="⚠  Nessuna riga trovata.",
            count_label_fn=lambda n: f"{n} righe.",
            save_fn=self._save_input,
            two_column=True, W=560, H=460,
        )


    def _reference_clear_all(self):
        if not self._ref_tree.get_children():
            return
        if messagebox.askyesno("Svuota righe", "Sei sicuro di voler rimuovere tutte le reference?"):
            self._ref_tree.delete(*self._ref_tree.get_children())
            self._ref_count_var.set("0 reference.")
            self._save_reference_input()

    def _save_reference_input(self):
        rows = [self._ref_tree.item(iid, "values")[0]
                for iid in self._ref_tree.get_children()
                if self._ref_tree.item(iid, "values")]
        try:
            INPUT_FILE_REFERENCE.parent.mkdir(parents=True, exist_ok=True)
            INPUT_FILE_REFERENCE.write_text("\n".join(rows) + "\n" if rows else "", encoding="utf-8")
            self._status_var.set(f"✓ data_input_reference.txt salvato ({len(rows)} righe).")
        except Exception as e:
            messagebox.showerror("Errore salvataggio", str(e))

    def _load_input_into_table(self):
        """Legge data_input.txt e popola la tabella PRM."""
        if not hasattr(self, "_input_tree"):
            return
        for row in self._input_tree.get_children():
            self._input_tree.delete(row)
        if not INPUT_FILE.exists():
            self._input_count_var.set("File non trovato — verrà creato al salvataggio.")
            return
        lines = INPUT_FILE.read_text(encoding="utf-8").strip().splitlines()
        count = 0
        for line in lines:
            line = line.strip()
            if not line or line.lower().startswith("prm"):
                continue
            parts = line.split(";")
            if len(parts) == 2:
                self._input_tree.insert("", "end", values=(parts[0].strip(), parts[1].strip()))
                count += 1
            else:
                self._input_tree.insert("", "end", values=(line, ""))
        self._input_count_var.set(f"{count} righe caricate.")


    def _identifier_clear_all(self):
        if not self._id_tree.get_children():
            return
        if messagebox.askyesno("Svuota righe", "Sei sicuro di voler rimuovere tutti gli identifier?"):
            self._id_tree.delete(*self._id_tree.get_children())
            self._id_count_var.set("0 identifier.")
            self._save_identifier_input()

    def _save_identifier_input(self):
        rows = [self._id_tree.item(iid, "values")[0]
                for iid in self._id_tree.get_children()
                if self._id_tree.item(iid, "values")]
        try:
            INPUT_FILE_IDENTIFIER.parent.mkdir(parents=True, exist_ok=True)
            INPUT_FILE_IDENTIFIER.write_text("\n".join(rows) + "\n" if rows else "", encoding="utf-8")
            self._status_var.set(f"✓ data_input_identifier.txt salvato ({len(rows)} righe).")
        except Exception as e:
            messagebox.showerror("Errore salvataggio", str(e))

    def _load_identifier_into_table(self):
        if not hasattr(self, "_id_tree"):
            return
        for row in self._id_tree.get_children():
            self._id_tree.delete(row)
        if not INPUT_FILE_IDENTIFIER.exists():
            self._id_count_var.set("File non trovato — verrà creato al salvataggio.")
            return
        lines = INPUT_FILE_IDENTIFIER.read_text(encoding="utf-8").strip().splitlines()
        count = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            self._id_tree.insert("", "end", values=(line,))
            count += 1
        self._id_count_var.set(f"{count} identifier caricati.")

    def _input_clear_all(self):
        if not self._input_tree.get_children():
            return
        if messagebox.askyesno("Svuota righe", "Sei sicuro di voler rimuovere tutte le righe?"):
            self._input_tree.delete(*self._input_tree.get_children())
            self._update_input_count()
            self._save_input()

    def _input_edit_cell(self, event):
        """Apre un Entry inline sulla cella cliccata."""
        region = self._input_tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        col_id = self._input_tree.identify_column(event.x)
        col = "prm" if col_id == "#1" else "kraken"
        iid = self._input_tree.identify_row(event.y)
        if not iid:
            return
        self._input_start_edit(iid, col)

    def _input_start_edit(self, iid, col):
        """Posiziona un Entry sovrapposto alla cella per la modifica."""
        col_index = 0 if col == "prm" else 1
        # Bbox della cella
        bbox = self._input_tree.bbox(iid, col)
        if not bbox:
            return
        x, y, w, h = bbox

        current_val = self._input_tree.item(iid, "values")
        val = current_val[col_index] if current_val else ""

        var = StringVar(value=val)
        entry = tkinter.Entry(self._input_tree, textvariable=var,
                              bg=BG_INPUT, fg=TEXT_PRI, insertbackground=TEXT_PRI,
                              font=("Consolas", 10), relief="flat", bd=2,
                              highlightthickness=1, highlightbackground=ACCENT)
        entry.place(x=x, y=y, width=w, height=h)
        entry.focus_set()
        entry.select_range(0, "end")

        def _commit(e=None):
            vals = list(self._input_tree.item(iid, "values"))
            while len(vals) < 2:
                vals.append("")
            vals[col_index] = var.get().strip()
            self._input_tree.item(iid, values=vals)
            entry.destroy()
            self._update_input_count()
            # Tab → passa alla colonna successiva
            if e and e.keysym == "Tab":
                next_col = "kraken" if col == "prm" else "prm"
                self.after(50, lambda: self._input_start_edit(iid, next_col))

        def _cancel(e=None):
            entry.destroy()

        entry.bind("<Return>",  _commit)
        entry.bind("<Tab>",     _commit)
        entry.bind("<Escape>",  _cancel)
        entry.bind("<FocusOut>", _commit)

    def _update_input_count(self):
        n = len(self._input_tree.get_children())
        self._input_count_var.set(f"{n} righe.")

    def _save_input(self):
        """Scrive le righe della tabella in data_input.txt."""
        rows = []
        for iid in self._input_tree.get_children():
            vals = self._input_tree.item(iid, "values")
            prm    = vals[0].strip() if len(vals) > 0 else ""
            kraken = vals[1].strip() if len(vals) > 1 else ""
            if prm or kraken:          # ignora righe completamente vuote
                rows.append(f"{prm};{kraken}")

        if not rows:
            try:
                INPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
                INPUT_FILE.write_text("", encoding="utf-8")
                self._status_var.set("✓ data_input.txt svuotato.")
            except Exception as e:
                messagebox.showerror("Errore salvataggio", str(e))
            return

        try:
            INPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
            content = "\n".join(rows) + "\n"
            INPUT_FILE.write_text(content, encoding="utf-8")
            self._status_var.set(f"✓ data_input.txt salvato ({len(rows)} righe).")
            self._update_input_count()
        except Exception as e:
            messagebox.showerror("Errore salvataggio", str(e))

    # ── Flag helpers ──────────────────────────────────────────────────────

    def _load_flags_from_env(self):
        data = _read_env_raw()
        seen_boxes = set()
        for qf, var in self._flags.items():
            env_key = FLAG_ENV_KEYS[qf]
            val = data.get(env_key, "Y").strip().upper() == "Y"
            var.set(val)
            box = self._flag_labels[qf]
            if id(box) not in seen_boxes:
                seen_boxes.add(id(box))
                box.configure(text="☑" if val else "☐",
                              fg=ACCENT if val else TEXT_SEC)

        seen_boxes_id = set()
        missing_id = {}
        for qf, var in self._flags_identifier.items():
            env_key = QUERY_FLAGS_IDENTIFIER[qf]
            if env_key not in data:
                missing_id[env_key] = "N"
            val = data.get(env_key, "N").strip().upper() == "Y"
            var.set(val)
            box = self._flag_labels_id[qf]
            if id(box) not in seen_boxes_id:
                seen_boxes_id.add(id(box))
                box.configure(text="☑" if val else "☐",
                              fg=ACCENT if val else TEXT_SEC)
        if missing_id:
            try:
                _write_env(missing_id)
                _reload_env_into_os()
            except Exception:
                pass

        seen_boxes_ref = set()
        missing_ref = {}
        for qf, var in self._flags_reference.items():
            env_key = QUERY_FLAGS_REFERENCE[qf]
            if env_key not in data:
                missing_ref[env_key] = "N"
            val = data.get(env_key, "N").strip().upper() == "Y"
            var.set(val)
            box = self._flag_labels_ref[qf]
            if id(box) not in seen_boxes_ref:
                seen_boxes_ref.add(id(box))
                box.configure(text="☑" if val else "☐",
                              fg=ACCENT if val else TEXT_SEC)
        if missing_ref:
            try:
                _write_env(missing_ref)
                _reload_env_into_os()
            except Exception:
                pass

    def _save_flags(self):
        data = {FLAG_ENV_KEYS[qf]: ("Y" if var.get() else "N")
                for qf, var in self._flags.items()}
        data.update({QUERY_FLAGS_IDENTIFIER[qf]: ("Y" if var.get() else "N")
                     for qf, var in self._flags_identifier.items()})
        data.update({QUERY_FLAGS_REFERENCE[qf]: ("Y" if var.get() else "N")
                     for qf, var in self._flags_reference.items()})
        try:
            _write_env(data)
            _reload_env_into_os()
            self._status_var.set("✓ Flag salvati nel .env.")
        except Exception as e:
            messagebox.showerror("Errore salvataggio flags", str(e))

    # ── .env helpers ──────────────────────────────────────────────────────



    # ── Pipeline ──────────────────────────────────────────────────────────

    def _start(self):
        if self._running:
            return
        self._running = True
        self._btn.configure(fg=TEXT_SEC, cursor="arrow")
        self._btn_id.configure(fg=TEXT_SEC, cursor="arrow")
        self._btn_ref.configure(fg=TEXT_SEC, cursor="arrow")
        self._status_var.set("In esecuzione...")

        env = _get_target_env()
        if self._mode == MODE_PRM:
            flags = {qf: var.get() for qf, var in self._flags.items()}
            threading.Thread(target=run_pipeline,
                             args=(flags, self._enqueue_log, self._on_done, env),
                             daemon=True).start()
        elif self._mode == MODE_IDENTIFIER:
            flags = {qf: var.get() for qf, var in self._flags_identifier.items()}
            threading.Thread(target=run_pipeline_identifier,
                             args=(flags, self._enqueue_log, self._on_done, env),
                             daemon=True).start()
        else:
            flags = {qf: var.get() for qf, var in self._flags_reference.items()}
            threading.Thread(target=run_pipeline_reference,
                             args=(flags, self._enqueue_log, self._on_done, env),
                             daemon=True).start()

    def _on_done(self, success: bool):
        self._running = False
        color = SUCCESS if success else ERROR
        msg   = "✓ Completato con successo." if success else "✗ Terminato con errori."
        self._status_var.set(msg)
        self._btn.configure(fg=color, cursor="hand2")
        self._btn_id.configure(fg=color, cursor="hand2")
        self._btn_ref.configure(fg=color, cursor="hand2")
        self.after(3000, lambda: (
            self._btn.configure(fg=ACCENT),
            self._btn_id.configure(fg=ACCENT),
            self._btn_ref.configure(fg=ACCENT),
        ))

    # ── Utility ───────────────────────────────────────────────────────────




# ════════════════════════════════════════════════════════════════════════════
# DELTA RECOVERY
# ════════════════════════════════════════════════════════════════════════════

import os
import queue
import threading
import tkinter
from pathlib import Path
from tkinter import Frame, Label, Scrollbar, StringVar, Text, Tk, ttk
from tkinter import messagebox, filedialog

_QUERIES_DIR = _HERE / "input" / "delta recovery" / "queries"

# ── Modalità pipeline ─────────────────────────────────────────────────────────
# Ogni voce: (env_key, label descrittiva)
# Aggiungere qui le modalità future.
PIPELINE_MODES = [
    ("MODE_DELTA_RECOVERY",   "NO_PAYMENT_PLAN_FOUND"),
    ("MODE_MULTIPLE_PP",      "MULTIPLE_PAYMENT_PLAN_FOUND_FOR_PAYMENT_DATE"),
    ("MODE_NO_PP_FOR_DATE",   "NO_PAYMENT_PLAN_FOUND_FOR_PAYMENT_DATE"),
]

# ── Definizioni query ─────────────────────────────────────────────────────────
QUERY_SQL_FILES = {
    "MODE_DELTA_RECOVERY": _QUERIES_DIR / "no_payment_plan_found.sql",
    "MODE_MULTIPLE_PP":    _QUERIES_DIR / "multiple_payment_plan_found.sql",
    "MODE_NO_PP_FOR_DATE": _QUERIES_DIR / "no_payment_plan_found_for_date.sql",
}

def _load_query(mode_key: str) -> str:
    """Legge la query dal file .sql se esiste, altrimenti ritorna stringa vuota."""
    sql_path = QUERY_SQL_FILES.get(mode_key)
    if sql_path and sql_path.exists():
        return sql_path.read_text(encoding="utf-8").strip()
    return ""

def _save_query(mode_key: str, text: str):
    """Salva la query nel file .sql dedicato."""
    sql_path = QUERY_SQL_FILES[mode_key]
    sql_path.parent.mkdir(parents=True, exist_ok=True)
    sql_path.write_text(text.strip() + "\n", encoding="utf-8")

def delta_run_pipeline(app, log, on_done, target: str,
                 mode_delta_recovery: bool = True,
                 mode_multiple_pp: bool = False,
                 mode_no_pp_for_date: bool = False,
                 run_enabled: bool = False):
    """Estrae i pagamenti recuperabili da HUB e li inserisce su Recette/Integration."""
    import psycopg2
    import time

    _reload_env()

    delta_table = "ztemp_pp_delta_payment_cluster"
    pp_table    = "payment_plans"

    # (tabella sorgente HUB, tabella destinazione)
    KRAKEN_TABLES = [
        ("z_pagamenti_kraken_ele_2304", "test_payments"),
        ("z_pagamenti_kraken_gas_2304", "test_payments_gas"),
    ]

    # Carica le query dai file .sql (con fallback hardcoded)
    QUERY_IDS_NO_PAYMENT_PLAN = _load_query("MODE_DELTA_RECOVERY")
    QUERY_IDS_MULTIPLE_PP     = _load_query("MODE_MULTIPLE_PP")
    QUERY_IDS_NO_PP_FOR_DATE  = _load_query("MODE_NO_PP_FOR_DATE")

    def _query_kraken(hub_conn, kraken_table, ids):
        array_literal = ", ".join(f"'{i}'" for i in ids)
        query = f"""
SELECT zpke.*
FROM {kraken_table} zpke
JOIN unnest(ARRAY[{array_literal}]) AS x(payrepay)
    ON x.payrepay = concat('P', zpke.payment_id, 'R', zpke.repayment_id)
;
"""
        cur = hub_conn.cursor()
        try:
            cur.execute(query)
            columns = [d[0] for d in cur.description]
            rows    = cur.fetchall()
        finally:
            cur.close()
        return columns, rows

    def _bulk_insert(tgt_conn, tgt_table, columns, rows):
        from io import StringIO
        import csv as _csv
        log(f"[INFO] Inserimento in '{tgt_table}' ({len(rows)} righe) ...", "info")
        buffer = StringIO()
        writer = _csv.writer(buffer, delimiter="\t",
                             quotechar="\x01", quoting=_csv.QUOTE_MINIMAL)
        for row in rows:
            writer.writerow([
                "\x02NULL\x02" if v is None else ("" if v == "" else v)
                for v in row
            ])
        buffer.seek(0)
        cols = ", ".join(columns)
        cur = tgt_conn.cursor()
        try:
            cur.copy_expert(
                f"COPY {tgt_table} ({cols}) FROM STDIN WITH "
                f"(FORMAT CSV, DELIMITER E'\\t', QUOTE E'\\x01', NULL E'\\x02NULL\\x02')",
                buffer,
            )
            tgt_conn.commit()
        except Exception:
            tgt_conn.rollback()
            cur.close()
            raise
        cur.close()

    app._active_hub_conn = None
    app._active_tgt_conn = None

    try:
        # ── Connessione HUB ───────────────────────────────────────────────────
        log(f"[INFO] Connessione HUB: {os.getenv('HUB_HOST')} / {os.getenv('HUB_NAME')} ...", "info")
        try:
            hub_conn = get_hub_connection()
            app._active_hub_conn = hub_conn
            log("[OK] Connessione HUB attiva ✓", "ok")
        except (psycopg2.OperationalError, EnvironmentError) as e:
            log(f"[ERRORE] Connessione HUB fallita: {e}", "error")
            on_done(success=False); return

        # ── Tunnel SSH + connessione destinazione ─────────────────────────────
        log(f"\n[INFO] Apertura tunnel SSH verso {target} ...", "info")
        try:
            tunnel = open_ssh_tunnel(target)
            log(f"[INFO] Tunnel attivo su porta locale {tunnel.local_bind_port}", "info")
        except Exception as e:
            log(f"[ERRORE] Tunnel SSH fallito: {e}", "error")
            hub_conn.close(); on_done(success=False); return

        prefix = "RECETTE" if target == "RECETTE" else "INTEGRATION"
        log(f"\n[INFO] Connessione {target}: {os.getenv(f'{prefix}_HOST')} ...", "info")
        try:
            tgt_conn = get_integration_connection(tunnel, target)
            app._active_tgt_conn = tgt_conn
            log(f"[OK] Connessione {target} attiva ✓", "ok")
        except psycopg2.OperationalError as e:
            log(f"[ERRORE] Connessione {target} fallita: {e}", "error")
            hub_conn.close(); tunnel.stop(); on_done(success=False); return

        # ── Guardia di sicurezza ──────────────────────────────────────────────
        hub_host = (os.getenv("HUB_HOST", "").strip().lower(),
                    os.getenv("HUB_NAME", "").strip().lower())
        tgt_host = (os.getenv(f"{prefix}_HOST", "").strip().lower(),
                    os.getenv(f"{prefix}_NAME", "").strip().lower())
        if hub_host == tgt_host:
            log(f"[ERRORE CRITICO] HUB e {target} puntano allo stesso host+database.", "error")
            hub_conn.close(); tgt_conn.close(); tunnel.stop(); on_done(success=False); return

        # ── Guardia modalità ──────────────────────────────────────────────────
        if not mode_delta_recovery and not mode_multiple_pp and not mode_no_pp_for_date:
            log("[WARN] Nessuna modalità selezionata — nessuna operazione eseguita.", "warn")
            hub_conn.close(); tgt_conn.close(); tunnel.stop(); on_done(success=False); return

        # ── Helper: estrai ID → query kraken → insert destinazione ───────────
        def _run_mode(label: str, query_ids: str):
            log(f"\n══ {label} ══", "section")

            if not query_ids or not query_ids.strip():
                log(f"[WARN] Query {label} non trovata, inserisci query e riavvia.", "warn")
                return {}

            # Step 1: estrazione ID
            log(f"[INFO] Estrazione ID recuperabili ...", "info")
            start = time.time()
            cur = hub_conn.cursor()
            try:
                cur.execute(query_ids)
                id_list = [row[0] for row in cur.fetchall()]
            except Exception as e:
                log(f"[ERRORE] Query ID fallita: {e}", "error")
                raise
            finally:
                cur.close()

            log(f"[OK] {len(id_list)} ID estratti in {time.time()-start:.1f}s", "ok")

            if app._stop_requested:
                raise InterruptedError("Stop richiesto dall'utente.")

            if not id_list:
                log("[WARN] Nessun ID trovato — modalità saltata.", "warn")
                return {}

            # Step 2: kraken → insert per ogni commodity
            counts = {}  # tgt_table -> n righe inserite
            for kraken_table, tgt_table in KRAKEN_TABLES:
                if app._stop_requested:
                    raise InterruptedError("Stop richiesto dall'utente.")

                log(f"\n── {kraken_table}  →  {tgt_table} ──", "section")
                log(f"[INFO] Query su HUB ...", "info")
                start = time.time()
                try:
                    columns, rows = _query_kraken(hub_conn, kraken_table, id_list)
                except Exception as e:
                    log(f"[ERRORE] Query fallita su {kraken_table}: {e}", "error")
                    raise

                log(f"[OK] {len(rows)} righe estratte in {time.time()-start:.1f}s", "ok")

                if not rows:
                    log(f"[WARN] Nessun risultato — {tgt_table} non aggiornata.", "warn")
                    counts[tgt_table] = 0
                    continue

                try:
                    _bulk_insert(tgt_conn, tgt_table, columns, rows)
                    log(f"[OK] '{tgt_table}' aggiornata con {len(rows)} righe.", "ok")
                    counts[tgt_table] = len(rows)
                except Exception as e:
                    log(f"[ERRORE] Insert su '{tgt_table}' fallito: {e}", "error")
                    raise

                if app._stop_requested:
                    raise InterruptedError("Stop richiesto dall'utente.")

            return counts

        # ── TRUNCATE una volta sola per ogni tabella di destinazione ─────────
        log("\n── Pulizia tabelle destinazione ──", "section")
        cur = tgt_conn.cursor()
        try:
            for _, tgt_table in KRAKEN_TABLES:
                log(f"[INFO] TRUNCATE {tgt_table} ...", "info")
                cur.execute(f"TRUNCATE TABLE {tgt_table};")
            tgt_conn.commit()
            log("[OK] Tabelle pulite ✓", "ok")
        except Exception as e:
            tgt_conn.rollback()
            cur.close()
            log(f"[ERRORE] TRUNCATE fallita: {e}", "error")
            hub_conn.close(); tgt_conn.close(); tunnel.stop(); on_done(success=False); return
        cur.close()

        # ── Esecuzione modalità attive ────────────────────────────────────────
        recap = {}  # label -> {tgt_table: count}

        if mode_delta_recovery:
            recap["NO_PAYMENT_PLAN_FOUND"] = \
                _run_mode("NO_PAYMENT_PLAN_FOUND", QUERY_IDS_NO_PAYMENT_PLAN)

        if not app._stop_requested and mode_multiple_pp:
            recap["MULTIPLE_PAYMENT_PLAN_FOUND_FOR_PAYMENT_DATE"] = \
                _run_mode("MULTIPLE_PAYMENT_PLAN_FOUND_FOR_PAYMENT_DATE", QUERY_IDS_MULTIPLE_PP)

        if not app._stop_requested and mode_no_pp_for_date:
            recap["NO_PAYMENT_PLAN_FOUND_FOR_PAYMENT_DATE"] = \
                _run_mode("NO_PAYMENT_PLAN_FOUND_FOR_PAYMENT_DATE", QUERY_IDS_NO_PP_FOR_DATE)

        # ── Recap finale ──────────────────────────────────────────────────────
        COMMODITY_LABEL = {
            "test_payments":     "ELE",
            "test_payments_gas": "GAS",
        }
        log("\n══ RECAP ══", "section")
        total_per_table = {}
        for label, counts in recap.items():
            log(f"\n  {label}", "section")
            for tgt_table, n in counts.items():
                commodity = COMMODITY_LABEL.get(tgt_table, tgt_table)
                log(f"    {commodity:<6} {n:>6} righe", "ok" if n > 0 else "warn")
                total_per_table[tgt_table] = total_per_table.get(tgt_table, 0) + n
        if len(recap) > 1:
            log("\n  TOTALE (tutte le modalità)", "section")
            for tgt_table, n in total_per_table.items():
                commodity = COMMODITY_LABEL.get(tgt_table, tgt_table)
                log(f"    {commodity:<6} {n:>6} righe", "ok" if n > 0 else "warn")

        log("\n[INFO] Pipeline completata con successo.", "ok")

        # ── Avvia run (se abilitato, prima di chiudere le connessioni) ────────
        if run_enabled and not app._stop_requested:
            log("\n── Avvia run ──", "section")
            _execute_run(app, log, target, tgt_conn=tgt_conn, tunnel=tunnel)

        hub_conn.close()
        tgt_conn.close()
        tunnel.stop()

        on_done(success=True)

    except InterruptedError as e:
        log(f"\n[WARN] {e}", "warn")
        for obj in ("hub_conn", "tgt_conn", "tunnel"):
            try: eval(obj).close() if obj != "tunnel" else eval(obj).stop()
            except Exception: pass
        log("\nSCRIPT BLOCCATO", "error")
        on_done(success=False)
    except Exception as e:
        import traceback
        log(f"\n[ERRORE CRITICO] {e}", "error")
        for line in traceback.format_exc().splitlines():
            log(f"  {line}", "error")
        on_done(success=False)


# ════════════════════════════════════════════════════════════════════════════
# Run
# ════════════════════════════════════════════════════════════════════════════

_RUN_QUERIES = [
    "TRUNCATE staging_payments;",
    "TRUNCATE TABLE sap_filter_contract_batch CASCADE;",
    "UPDATE hub_config_db SET hvalue = 'N' WHERE hkey = 'CUSTOMER_IS_ACTIVE';",
    "UPDATE hub_config_db SET hvalue = 'N' WHERE hkey = 'AGREEMENT_IS_ACTIVE';",
    "UPDATE hub_config_db SET hvalue = 'N' WHERE hkey = 'PP_IS_ACTIVE';",
    "UPDATE hub_config_db SET hvalue = 'N' WHERE hkey = 'INVOICE_IS_ACTIVE';",
    "UPDATE hub_config_db SET hvalue = 'Y' WHERE hkey = 'PAYMENTS_IS_ACTIVE';",
    "UPDATE hub_config_db SET hvalue  = 'Y' WHERE hkey = 'B2C_SAP_INTEGRATION_IS_ACTIVE';",
]

def _execute_run(app, log, target: str, tgt_conn=None, tunnel=None):
    """Esegue le query di run su target.
    Se tgt_conn è None apre un nuovo tunnel SSH, altrimenti riusa la connessione esistente.
    """
    _owns_conn = tgt_conn is None
    _tunnel = None
    try:
        if _owns_conn:
            _reload_env()
            log(f"[INFO] Apertura tunnel SSH verso {target} ...", "info")
            _tunnel = open_ssh_tunnel(target)
            tgt_conn = get_integration_connection(_tunnel, target)
            app._active_tgt_conn = tgt_conn
        cur = tgt_conn.cursor()
        try:
            for query in _RUN_QUERIES:
                if app._stop_requested:
                    tgt_conn.rollback()
                    log("SCRIPT BLOCCATO", "error")
                    return
                log(f"[INFO] {query}", "info")
                cur.execute(query)
            tgt_conn.commit()
        except Exception as e:
            tgt_conn.rollback()
            raise e
        finally:
            cur.close()
        log("RUN AVVIATO", "ok")
    except Exception as e:
        import traceback
        log(f"[ERRORE] {e}", "error")
        for line in traceback.format_exc().splitlines():
            log(f"  {line}", "error")
    finally:
        if _owns_conn:
            if tgt_conn:
                tgt_conn.close()
            if _tunnel:
                _tunnel.stop()


class BonificaProd(_AppBase):

    def __init__(self, master):
        super().__init__(master, bg=BG)
        self._log_queue  = queue.Queue()
        self._running    = False
        self._flag_vars  = {}
        self._flag_boxes = {}
        self._build_ui()
        self._load_bp_flags()
        self._poll_log()

    def _load_bp_flags(self):
        data = _read_env_raw()
        for hkey, env_key in _BP_ENV_KEYS.items():
            val = data.get(env_key, "N").strip().upper() == "Y"
            if hkey in self._flag_vars:
                self._flag_vars[hkey].set(val)
                box = self._flag_boxes.get(hkey)
                if box:
                    box.configure(text="☑" if val else "☐",
                                  fg=ACCENT if val else TEXT_SEC)

    def _save_bp_flags(self):
        data = {_BP_ENV_KEYS[k]: ("Y" if v.get() else "N")
                for k, v in self._flag_vars.items()
                if k in _BP_ENV_KEYS}
        try:
            _write_env(data)
            _reload_env_into_os()
        except Exception:
            pass

    def _build_ui(self):
        self._status_var = tkinter.StringVar(value="Pronto.")
        Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, side="bottom")
        Label(self, textvariable=self._status_var, bg=BG, fg=TEXT_SEC,
              font=("Consolas", 9), anchor="w", pady=5).pack(fill="x", padx=24, side="bottom")

        body = Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(12, 0))

        left_w = Frame(body, bg=BG_CARD, highlightthickness=1,
                       highlightbackground=BORDER)
        left_w.pack(side="left", fill="y")
        left_w.pack_propagate(False)
        left_w.configure(width=230)

        left = Frame(left_w, bg=BG_CARD)
        left.pack(fill="both", expand=True)

        hdr = Frame(left, bg=BG_CARD2)
        hdr.pack(fill="x")
        Label(hdr, text="▼", bg=BG_CARD2, fg=ACCENT,
              font=("Consolas", 9)).pack(side="left", padx=(8, 4), pady=6)
        Label(hdr, text="Flussi", bg=BG_CARD2, fg=TEXT_PRI,
              font=("Consolas", 10, "bold")).pack(side="left", pady=6)
        Frame(left, bg=BORDER, height=1).pack(fill="x")

        for hkey, label in _BP_FLAGS:
            self._flag_vars[hkey] = BooleanVar(value=False)
            row = Frame(left, bg=BG_CARD)
            row.pack(fill="x", padx=10, pady=2)
            box = Label(row, text="☐", bg=BG_CARD, fg=TEXT_SEC,
                        font=("Consolas", 12), cursor="hand2", width=2)
            box.pack(side="left", padx=(0, 6))
            self._flag_boxes[hkey] = box
            lbl_w = Label(row, text=label, bg=BG_CARD, fg=TEXT_PRI,
                          font=("Consolas", 10), anchor="w", cursor="hand2")
            lbl_w.pack(side="left", fill="x", expand=True)

            def _make_tog(key=hkey, b=box):
                def _toggle(e=None):
                    new_val = not self._flag_vars[key].get()
                    self._flag_vars[key].set(new_val)
                    b.configure(text="☑" if new_val else "☐",
                                fg=ACCENT if new_val else TEXT_SEC)
                    self._save_bp_flags()
                return _toggle
            tog = _make_tog()
            box.bind("<Button-1>", tog)
            lbl_w.bind("<Button-1>", tog)

        Frame(left, bg=BORDER, height=1).pack(fill="x", padx=10, pady=(8, 0))

        btn_frame = Frame(left, bg=BG_CARD)
        btn_frame.pack(fill="x", padx=10, pady=(8, 4), side="bottom")
        self._btn = self._make_btn(btn_frame, "▶  Avvia", self._start)
        self._btn.pack(fill="x")

        right = Frame(body, bg=BG_CARD, highlightthickness=1,
                      highlightbackground=BORDER)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self._build_log_panel(right, on_clear=self._clear_log)

    def _get_int_conn(self):
        env    = _get_target_env()
        tunnel = open_ssh_tunnel(env)
        conn   = get_integration_connection(tunnel, env)
        return tunnel, conn

    def _start(self):
        if self._running:
            return
        self._running = True
        self._btn.configure(fg=TEXT_SEC, cursor="arrow")
        self._status_var.set("In esecuzione...")
        threading.Thread(target=self._run_worker, daemon=True).start()

    def _run_worker(self):
        import psycopg2
        tunnel = hub_conn = int_conn = None
        try:
            self._enqueue_log("[INFO] Apertura tunnel SSH...", "info")
            tunnel, int_conn = self._get_int_conn()
            self._enqueue_log("[OK] Connessione Integration/Recette attiva ✓", "ok")
            self._enqueue_log("[INFO] Connessione HUB PROD...", "info")
            hub_conn = get_hub_connection()
            self._enqueue_log("[OK] Connessione HUB PROD attiva ✓", "ok")
        except Exception as e:
            self._enqueue_log(f"[ERRORE CRITICO] {e}", "error")
            self.after(0, self._done, False)
            return

        success = True

        # ── CUSTOMER ─────────────────────────────────────────────────────
        if self._flag_vars.get("CUSTOMER", BooleanVar()).get():
            try:
                self._enqueue_log("\n── Customer  [RUN] ──", "section")
                cur = hub_conn.cursor()
                cur.execute("TRUNCATE TABLE z_bonifiche_customer_from_test;")
                cur.close()
                self._enqueue_log("[OK] Truncate 'z_bonifiche_customer_from_test'", "ok")
                cur_count = int_conn.cursor()
                cur_count.execute("SELECT COUNT(*) FROM customer")
                row_count = cur_count.fetchone()[0]
                cur_count.close()
                self._enqueue_log(f"[OK] {row_count} righe trovate in 'customer' su {_get_target_env()}.", "ok")
                cur = int_conn.cursor("bp_customer")
                cur.itersize = 10_000
                cur.execute("SELECT * FROM customer")
                first_batch = cur.fetchmany(10_000)
                columns = [d[0] for d in cur.description]
                total = 0
                batches = [first_batch] if first_batch else []
                while True:
                    batch = batches.pop(0) if batches else cur.fetchmany(10_000)
                    if not batch:
                        break
                    batch = normalize_timestamps(batch)
                    hub_cur = hub_conn.cursor()
                    bulk_insert(hub_cur, "z_bonifiche_customer_from_test", columns, batch)
                    hub_cur.close()
                    total += len(batch)
                cur.close()
                self._enqueue_log(f"[OK] {total} righe trasferite in 'z_bonifiche_customer_from_test'.", "ok")
                self._enqueue_log("\n── Step 1: Controllo customer mancanti da PROD ──", "section")
                cur = hub_conn.cursor()
                cur.execute("""
                    SELECT COUNT(*) FROM z_bonifiche_customer_from_test ct
                    LEFT JOIN customer c ON c.id_kraken = ct.id_kraken
                    WHERE c.id_kraken IS NULL
                """)
                missing = cur.fetchone()[0]
                cur.close()
                self._enqueue_log(f"[OK] {missing} customer mancanti in PROD.", "ok")
                self._enqueue_log("\n── Step 2: Inserimento customer mancanti ──", "section")
                cur = hub_conn.cursor()
                cur.execute("""
                    INSERT INTO customer (
                        action, bpkind, building, cel_number, city1, country, customer_type, floor,
                        house_num1, hub_updated_at, id_kraken, kraken_bp_id, name_first, name_last,
                        post_code1, reltyp, segment, smtp_addr, smtp_addr2, str_suppl1, street,
                        taxnum_1, taxnum_2, taxnum_3, tel_number, type, updated_at, urn,
                        zzbpregroupe, zzstatutdere
                    )
                    SELECT
                        ct.action, ct.bpkind, ct.building, ct.cel_number, ct.city1, ct.country,
                        ct.customer_type, ct.floor, ct.house_num1, ct.hub_updated_at, ct.id_kraken,
                        ct.kraken_bp_id, ct.name_first, ct.name_last, ct.post_code1, ct.reltyp,
                        ct.segment, ct.smtp_addr, ct.smtp_addr2, ct.str_suppl1, ct.street,
                        ct.taxnum_1, ct.taxnum_2, ct.taxnum_3, ct.tel_number, ct.type,
                        ct.updated_at, ct.urn, ct.zzbpregroupe, ct.zzstatutdere
                    FROM z_bonifiche_customer_from_test ct
                    LEFT JOIN customer c ON c.id_kraken = ct.id_kraken
                    WHERE c.id_kraken IS NULL
                """)
                inserted = cur.rowcount
                cur.close()
                self._enqueue_log(f"[OK] {inserted} customer inseriti in 'customer'.", "ok")
                hub_conn.commit()
                self._enqueue_log("[OK] Commit Customer eseguita ✓", "ok")
            except Exception as e:
                hub_conn.rollback()
                self._enqueue_log(f"[ERRORE] Customer — rollback eseguito: {e}", "error")
                success = False

        # ── AGREEMENT ────────────────────────────────────────────────────
        if self._flag_vars.get("AGREEMENT", BooleanVar()).get():
            try:
                self._enqueue_log("\n── Agreement  [RUN] ──", "section")
                cur = hub_conn.cursor()
                cur.execute("TRUNCATE TABLE z_bonifiche_agreement_from_test;")
                cur.close()
                self._enqueue_log("[OK] Truncate 'z_bonifiche_agreement_from_test'", "ok")
                cur_count = int_conn.cursor()
                cur_count.execute("SELECT COUNT(*) FROM agreement")
                row_count = cur_count.fetchone()[0]
                cur_count.close()
                self._enqueue_log(f"[OK] {row_count} righe trovate in 'agreement' su {_get_target_env()}.", "ok")
                cur = int_conn.cursor("bp_agreement")
                cur.itersize = 10_000
                cur.execute("SELECT * FROM agreement")
                first_batch = cur.fetchmany(10_000)
                columns = [d[0] for d in cur.description]
                total = 0
                batches = [first_batch] if first_batch else []
                while True:
                    batch = batches.pop(0) if batches else cur.fetchmany(10_000)
                    if not batch:
                        break
                    batch = normalize_timestamps(batch)
                    hub_cur = hub_conn.cursor()
                    bulk_insert(hub_cur, "z_bonifiche_agreement_from_test", columns, batch)
                    hub_cur.close()
                    total += len(batch)
                cur.close()
                self._enqueue_log(f"[OK] {total} righe trasferite in 'z_bonifiche_agreement_from_test'.", "ok")
                self._enqueue_log("\n── Step 1: Controllo agreement da aggiornare ──", "section")
                cur = hub_conn.cursor()
                cur.execute("""
                    SELECT COUNT(*) FROM z_bonifiche_agreement_from_test at
                    LEFT JOIN agreement a ON a.agreement_id = at.agreement_id
                    WHERE a.agreement_id IS NOT NULL
                """)
                to_update = cur.fetchone()[0]
                cur.close()
                self._enqueue_log(f"[OK] {to_update} agreement da aggiornare in PROD.", "ok")
                self._enqueue_log("\n── Step 2: Aggiornamento agreement esistenti ──", "section")
                cur = hub_conn.cursor()
                cur.execute("""
                    UPDATE agreement a
                    SET zahlkond       = at.zahlkond,
                        start_date     = at.start_date,
                        end_date       = at.end_date,
                        agreement_type = at.agreement_type,
                        action         = at.action
                    FROM z_bonifiche_agreement_from_test at
                    WHERE a.agreement_id = at.agreement_id
                    AND a.agreement_id IS NOT NULL
                """)
                updated = cur.rowcount
                cur.close()
                self._enqueue_log(f"[OK] {updated} agreement aggiornati.", "ok")
                self._enqueue_log("\n── Step 3: Controllo agreement mancanti da PROD ──", "section")
                cur = hub_conn.cursor()
                cur.execute("""
                    SELECT COUNT(*) FROM z_bonifiche_agreement_from_test at
                    LEFT JOIN agreement a ON a.agreement_id = at.agreement_id
                    WHERE a.agreement_id IS NULL
                """)
                missing = cur.fetchone()[0]
                cur.close()
                self._enqueue_log(f"[OK] {missing} agreement mancanti in PROD.", "ok")
                self._enqueue_log("\n── Step 4: Inserimento agreement mancanti ──", "section")
                cur = hub_conn.cursor()
                cur.execute("""
                    INSERT INTO agreement (
                        action, agreement_id, agreement_type, ezawe, ins_date, invoice_created_at,
                        last_invoice_created_at, number, prm_pce, sparte, updated_at, urn,
                        start_date, end_date, zahlkond, customer_id, plan_type
                    )
                    SELECT
                        at.action, at.agreement_id, at.agreement_type, at.ezawe, at.ins_date,
                        at.invoice_created_at, at.last_invoice_created_at, at.number, at.prm_pce,
                        at.sparte, at.updated_at, at.urn, at.start_date, at.end_date, at.zahlkond,
                        (SELECT customer_id FROM customer WHERE id_kraken = at.number) AS customer_id,
                        at.plan_type
                    FROM z_bonifiche_agreement_from_test at
                    LEFT JOIN agreement a ON a.agreement_id = at.agreement_id
                    WHERE a.agreement_id IS NULL
                """)
                inserted = cur.rowcount
                cur.close()
                self._enqueue_log(f"[OK] {inserted} agreement inseriti in 'agreement'.", "ok")
                hub_conn.commit()
                self._enqueue_log("[OK] Commit Agreement eseguita ✓", "ok")
            except Exception as e:
                hub_conn.rollback()
                self._enqueue_log(f"[ERRORE] Agreement — rollback eseguito: {e}", "error")
                success = False

        # ── PAYMENT PLANS ─────────────────────────────────────────────────
        if self._flag_vars.get("PAYMENT_PLANS", BooleanVar()).get():
            try:
                self._enqueue_log("\n── Payment Plans  [RUN] ──", "section")

                # TRUNCATE e ricarica payment_plans_from_integration
                cur = hub_conn.cursor()
                cur.execute("TRUNCATE TABLE payment_plans_from_integration;")
                cur.close()
                self._enqueue_log("[OK] Truncate 'payment_plans_from_integration'", "ok")

                # Conta righe sull'ambiente di test
                cur_count = int_conn.cursor()
                cur_count.execute("SELECT COUNT(*) FROM payment_plans")
                row_count = cur_count.fetchone()[0]
                cur_count.close()
                self._enqueue_log(f"[OK] {row_count} righe trovate in 'payment_plans' su {_get_target_env()}.", "ok")

                # Trasferisce da Integration/Recette a HUB
                cur = int_conn.cursor("bp_payment_plans")
                cur.itersize = 10_000
                cur.execute("SELECT * FROM payment_plans")
                first_batch = cur.fetchmany(10_000)
                columns = [d[0] for d in cur.description]
                total = 0
                batches = [first_batch] if first_batch else []
                while True:
                    batch = batches.pop(0) if batches else cur.fetchmany(10_000)
                    if not batch:
                        break
                    batch = normalize_timestamps(batch)
                    hub_cur = hub_conn.cursor()
                    bulk_insert(hub_cur, "payment_plans_from_integration", columns, batch)
                    hub_cur.close()
                    total += len(batch)
                cur.close()
                self._enqueue_log(f"[OK] {total} righe trasferite in 'payment_plans_from_integration'.", "ok")

                # Se la tabella from_integration è vuota, logga warning e salta
                cur = hub_conn.cursor()
                cur.execute("SELECT COUNT(*) FROM payment_plans_from_integration")
                check_count = cur.fetchone()[0]
                cur.close()
                if check_count == 0:
                    self._enqueue_log("[WARN] 'payment_plans_from_integration' è vuota — DELETE e INSERT saltate.", "warn")
                else:
    
                    # Conteggio as-is piani in PROD da bonificare
                    self._enqueue_log("\n── Step 1: Conteggio piani in PROD da bonificare ──", "section")
                    cur = hub_conn.cursor()
                    cur.execute("""
                        SELECT COUNT(*) FROM (
                            SELECT DISTINCT p.prm, p.number, p.valid_from
                            FROM payment_plans p
                            JOIN payment_plans_from_integration i
                              ON i.prm = p.prm
                             AND i.number = p.number
                        ) sub
                    """)
                    to_delete = cur.fetchone()[0]
                    cur.close()
                    self._enqueue_log(f"[OK] {to_delete} piani da bonificare in PROD.", "ok")
    
                    # STEP 1 — DELETE
                    self._enqueue_log("\n── Step 2: Cancellazione piani da bonificare ──", "section")
                    cur = hub_conn.cursor()
                    cur.execute("""
                        DELETE FROM payment_plans p1
                        WHERE EXISTS (
                            SELECT 1 FROM payment_plans_from_integration p2
                            WHERE p1.prm = p2.prm
                              AND p1.number = p2.number
                        )
                    """)
                    deleted = cur.rowcount
                    cur.close()
                    self._enqueue_log(f"[OK] {deleted} piani eliminati da 'payment_plans'.", "ok")
    
                    # STEP 2 — INSERT
                    self._enqueue_log("\n── Step 3: Reinserimento piani bonificati ──", "section")
                    cur = hub_conn.cursor()
                    cur.execute("""
                        INSERT INTO payment_plans (
                            bill_finalized_at, bill_number, bill_template_code, billing_scheduled_date,
                            comodity, component_split, history, hub_update_at, import_supplier_bill_id,
                            number, payment_amount, payment_day, payment_schedule_id, plan_type_id,
                            prm, reference, updated_at, valid_from, valid_to, sap_agreement_id,
                            hub_create_at, is_renewal, kraken_original_valid_from, kraken_original_valid_to,
                            period_valid_to, is_reactivation
                        )
                        SELECT
                            bill_finalized_at, bill_number, bill_template_code, billing_scheduled_date,
                            comodity, component_split, history, hub_update_at, import_supplier_bill_id,
                            number, payment_amount, payment_day, payment_schedule_id, plan_type_id,
                            prm, reference, updated_at, valid_from, valid_to, sap_agreement_id,
                            hub_create_at, is_renewal, kraken_original_valid_from, kraken_original_valid_to,
                            period_valid_to, is_reactivation
                        FROM payment_plans_from_integration
                    """)
                    inserted = cur.rowcount
                    cur.close()
                    self._enqueue_log(f"[OK] {inserted} piani reinseriti in 'payment_plans'.", "ok")
    
                    hub_conn.commit()
                    self._enqueue_log("[OK] Commit Payment Plans eseguita ✓", "ok")

            except Exception as e:
                hub_conn.rollback()
                self._enqueue_log(f"[ERRORE] Payment Plans — rollback eseguito: {e}", "error")
                success = False

        # ── INVOICE ───────────────────────────────────────────────────────
        if self._flag_vars.get("INVOICE", BooleanVar()).get():
            try:
                self._enqueue_log("\n── Invoice  [RUN] ──", "section")

                # TRUNCATE e ricarica invoice_from_integration
                cur = hub_conn.cursor()
                cur.execute("TRUNCATE TABLE invoice_from_integration;")
                cur.close()
                self._enqueue_log("[OK] Truncate 'invoice_from_integration'", "ok")

                # Conta righe sull'ambiente di test
                cur_count = int_conn.cursor()
                cur_count.execute("SELECT COUNT(*) FROM invoice")
                row_count = cur_count.fetchone()[0]
                cur_count.close()
                self._enqueue_log(f"[OK] {row_count} righe trovate in 'invoice' su {_get_target_env()}.", "ok")

                # Trasferisce da Integration/Recette a HUB
                cur = int_conn.cursor("bp_invoice")
                cur.itersize = 10_000
                cur.execute("SELECT * FROM invoice")
                first_batch = cur.fetchmany(10_000)
                columns = [d[0] for d in cur.description]
                total = 0
                batches = [first_batch] if first_batch else []
                while True:
                    batch = batches.pop(0) if batches else cur.fetchmany(10_000)
                    if not batch:
                        break
                    batch = normalize_timestamps(batch)
                    hub_cur = hub_conn.cursor()
                    bulk_insert(hub_cur, "invoice_from_integration", columns, batch)
                    hub_cur.close()
                    total += len(batch)
                cur.close()
                self._enqueue_log(f"[OK] {total} righe trasferite in 'invoice_from_integration'.", "ok")

                # Warning se la tabella è vuota
                if total == 0:
                    self._enqueue_log("[WARN] 'invoice_from_integration' è vuota — UPDATE e INSERT non effettuate.", "warn")
                else:
                    self._enqueue_log("\n── Step 1: Controllo invoice da aggiornare ──", "section")
                    cur = hub_conn.cursor()
                    cur.execute("""
                        SELECT COUNT(*) FROM invoice_from_integration ii
                        LEFT JOIN invoice i ON i.identifier = ii.identifier
                        WHERE i.identifier IS NOT NULL
                    """)
                    to_update = cur.fetchone()[0]
                    cur.close()
                    self._enqueue_log(f"[OK] {to_update} invoice da aggiornare in PROD.", "ok")
    
                    self._enqueue_log("\n── Step 1.2: Aggiornamento invoice esistenti ──", "section")
                    cur = hub_conn.cursor()
                    cur.execute("""
                        UPDATE invoice i
                        SET agreement_id        = ii.agreement_id,
                            payment_plan        = ii.payment_plan,
                            template_code       = ii.template_code,
                            is_monthly_billing  = ii.is_monthly_billing
                        FROM invoice_from_integration ii
                        WHERE i.identifier = ii.identifier
                          AND i.identifier IS NOT NULL
                    """)
                    updated = cur.rowcount
                    cur.close()
                    self._enqueue_log(f"[OK] {updated} invoice aggiornate.", "ok")
    
                    # STEP 2 — Inserimento invoice mancanti
                    self._enqueue_log("\n── Step 2: Controllo invoice mancanti da PROD ──", "section")
                    cur = hub_conn.cursor()
                    cur.execute("""
                        SELECT COUNT(*) FROM invoice_from_integration ii
                        LEFT JOIN invoice i ON i.identifier = ii.identifier
                        WHERE i.identifier IS NULL
                    """)
                    missing = cur.fetchone()[0]
                    cur.close()
                    self._enqueue_log(f"[OK] {missing} invoice mancanti in PROD.", "ok")
    
                    self._enqueue_log("\n── Step 2.2: Inserimento invoice mancanti ──", "section")
                    cur = hub_conn.cursor()
                    cur.execute("""
                        INSERT INTO invoice (
                            account_type, comodity, document_type, finalized_at, history, hub_updated_at,
                            identifier, invoice_amount, is_monthly_billing, issued_by_id,
                            last_payment_schedule_id, ledger_type, number, original_statement_identifier,
                            payment_amount_rb, payment_at, payment_id, payment_plan, prm,
                            reconciliation_status, reference, reference_rb, template_code,
                            template_split_json, to_be_paid_amount, turpe_json_components,
                            vat_json_components, agreement_id, kraken_version, is_negative
                        )
                        SELECT
                            ifi.account_type, ifi.comodity, ifi.document_type, ifi.finalized_at,
                            ifi.history, ifi.hub_updated_at, ifi.identifier, ifi.invoice_amount,
                            ifi.is_monthly_billing, ifi.issued_by_id, ifi.last_payment_schedule_id,
                            ifi.ledger_type, ifi.number, ifi.original_statement_identifier,
                            ifi.payment_amount_rb, ifi.payment_at, ifi.payment_id, ifi.payment_plan,
                            ifi.prm, ifi.reconciliation_status, ifi.reference, ifi.reference_rb,
                            ifi.template_code, ifi.template_split_json, ifi.to_be_paid_amount,
                            ifi.turpe_json_components, ifi.vat_json_components, ifi.agreement_id,
                            ifi.kraken_version, ifi.is_negative
                        FROM invoice_from_integration ifi
                        LEFT JOIN invoice i ON i.identifier = ifi.identifier
                        WHERE i.identifier IS NULL
                    """)
                    inserted = cur.rowcount
                    cur.close()
                    self._enqueue_log(f"[OK] {inserted} invoice inserite in 'invoice'.", "ok")
    
                    hub_conn.commit()
                    self._enqueue_log("[OK] Commit Invoice eseguita ✓", "ok")

            except Exception as e:
                hub_conn.rollback()
                self._enqueue_log(f"[ERRORE] Invoice — rollback eseguito: {e}", "error")
                success = False

        if hub_conn:
            hub_conn.close()
        if int_conn:
            int_conn.close()
        if tunnel:
            tunnel.stop()
        self.after(0, self._done, success)

    def _done(self, success: bool):
        self._running = False
        self._status_var.set("✓ Completato." if success else "✗ Errore.")
        self._btn.configure(fg=SUCCESS if success else ERROR, cursor="hand2")
        self.after(3000, lambda: self._btn.configure(fg=ACCENT))



class DeltaRecovery(_AppBase):
    def __init__(self, master):
        super().__init__(master, bg=BG)

        self._log_queue: queue.Queue = queue.Queue()
        self._running        = False
        self._stop_requested = False

        self._build_ui()
        self._poll_log()




    def _build_ui(self):
        self._status_var = tkinter.StringVar(value="Pronto.")
        Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, side="bottom")
        self._status_lbl = Label(self, textvariable=self._status_var, bg=BG, fg=TEXT_SEC,
                                  font=("Consolas", 9), anchor="w", pady=5)
        self._status_lbl.pack(fill="x", padx=24, side="bottom")
        self._build_notebook([
            ("  ▶  Pipeline  ", self._build_pipeline_tab),
            ("  ✎  Query  ",   self._build_query_tab),
        ])

    # ── Tab Pipeline ──────────────────────────────────────────────────────

    def _build_pipeline_tab(self, parent):
        left, right = self._build_panel_layout(parent, left_width=280)

        # Intestazione pannello sinistro
        hdr_left = Frame(left, bg=BG_CARD2)
        hdr_left.pack(fill="x")
        Label(hdr_left, text="Pagamenti", bg=BG_CARD2, fg=TEXT_PRI,
              font=("Consolas", 9, "bold"), padx=14, pady=10,
              anchor="w").pack(fill="x")
        Frame(left, bg=BORDER, height=1).pack(fill="x")

        # --- Sezione modalità (checkbox) ---

        _pre = _read_env_raw()
        def _bv(key):
            v = _pre.get(key, "")
            if v == "":
                return False
            return v.lower() in {"1", "true", "yes", "y", "on"}

        self._mode_vars = {}
        for env_key, _ in PIPELINE_MODES:
            self._mode_vars[env_key] = tkinter.BooleanVar(value=_bv(env_key))

        _FLAG_MAP = {id(var): env_key for env_key, var in
                     ((ek, self._mode_vars[ek]) for ek, _ in PIPELINE_MODES)}

        def _make_row_check(par, var, label_text):
            row = Frame(par, bg=BG_CARD)
            row.pack(fill="x", padx=14, pady=3)
            box = Label(row, text="☑" if var.get() else "☐",
                        bg=BG_CARD, fg=ACCENT if var.get() else TEXT_SEC,
                        font=("Consolas", 12), cursor="hand2", width=2)
            box.pack(side="left", padx=(0, 6))
            lbl = Label(row, text=label_text, bg=BG_CARD, fg=TEXT_PRI,
                        font=("Consolas", 10), cursor="hand2",
                        wraplength=220, justify="left")
            lbl.pack(side="left")

            def _toggle(e=None):
                var.set(not var.get())
                box.configure(text="☑" if var.get() else "☐",
                              fg=ACCENT if var.get() else TEXT_SEC)
                env_key = _FLAG_MAP.get(id(var))
                if env_key:
                    _write_env({env_key: "true" if var.get() else "false"})

            box.bind("<Button-1>", _toggle)
            lbl.bind("<Button-1>", _toggle)
            row.bind("<Button-1>", _toggle)

        for env_key, label_text in PIPELINE_MODES:
            _make_row_check(left, self._mode_vars[env_key], label_text)

        Frame(left, bg=BORDER, height=1).pack(fill="x", padx=14, pady=(8, 0))

        # --- Bottoni (ancorati in fondo) ---
        # Con side="bottom" l'ordine è invertito: il primo pack va più in basso
        btn_frame = Frame(left, bg=BG_CARD)
        btn_frame.pack(fill="x", padx=14, pady=12, side="bottom")

        # Avvia + Stop
        row1 = Frame(btn_frame, bg=BG_CARD)
        row1.pack(fill="x", side="bottom")

        # Checkbox — pack per ultima, finisce in cima
        run_row = Frame(btn_frame, bg=BG_CARD)
        run_row.pack(fill="x", side="bottom", pady=(0, 8))

        self._btn = self._make_btn(row1, "▶  Avvia", self._start)
        self._btn.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self._btn_stop = self._make_btn(row1, "■  Stop", self._stop, color=ERROR)
        self._btn_stop.pack(side="left", fill="x", expand=True, padx=(3, 0))
        self._btn_stop.configure(fg=TEXT_SEC, cursor="arrow")

        # Contenuto checkbox

        self._run_enabled_var = tkinter.BooleanVar(value=_bv("RUN_ENABLED"))

        _run_checked_init = self._run_enabled_var.get()
        run_box = Label(run_row, text="☑" if _run_checked_init else "☐",
                        bg=BG_CARD, fg=ACCENT if _run_checked_init else TEXT_SEC,
                        font=("Consolas", 12), cursor="hand2")
        run_box.pack(side="left", padx=(0, 6))
        run_lbl = Label(run_row, text="Avvia run", bg=BG_CARD, fg=TEXT_PRI,
                        font=("Consolas", 10), cursor="hand2")
        run_lbl.pack(side="left")

        def _toggle_run(e=None):
            self._run_enabled_var.set(not self._run_enabled_var.get())
            checked = self._run_enabled_var.get()
            run_box.configure(text="☑" if checked else "☐",
                              fg=ACCENT if checked else TEXT_SEC)
            _write_env({"RUN_ENABLED": "true" if checked else "false"})

        run_box.bind("<Button-1>", _toggle_run)
        run_lbl.bind("<Button-1>", _toggle_run)
        run_row.bind("<Button-1>", _toggle_run)

        self._build_log_panel(right, on_clear=self._clear_log)

    # ── Tab Query ─────────────────────────────────────────────────────────

    def _build_query_tab(self, parent):
        self._query_editors = {}  # mode_key -> Text widget

        # Notebook interno — stesso stile del principale
        inner_nb = ttk.Notebook(parent, style="Dark.TNotebook")
        inner_nb.pack(fill="both", expand=True, padx=16, pady=12)

        for env_key, label_text in PIPELINE_MODES:
            sql_path = QUERY_SQL_FILES[env_key]

            tab = Frame(inner_nb, bg=BG)
            inner_nb.add(tab, text=f"  {label_text}  ")

            # Corpo della tab
            body = Frame(tab, bg=BG)
            body.pack(fill="both", expand=True, padx=16, pady=(12, 0))

            # Riga info file
            Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(0, 8))

            # Editor query
            editor_frame = Frame(body, bg=BG_INPUT, highlightthickness=1,
                                 highlightbackground=BORDER)
            editor_frame.pack(fill="both", expand=True)

            editor_scroll_y = ttk.Scrollbar(editor_frame,
                                        style="Dark.Vertical.TScrollbar")
            editor_scroll_x = ttk.Scrollbar(editor_frame, orient="horizontal",
                                        style="Dark.Horizontal.TScrollbar")
            editor_scroll_y.pack(side="right", fill="y")
            editor_scroll_x.pack(side="bottom", fill="x")

            editor = Text(editor_frame, bg=BG_INPUT, fg=TEXT_PRI,
                          font=("Consolas", 10), relief="flat", bd=0,
                          wrap="none", padx=10, pady=8,
                          insertbackground=ACCENT, selectbackground=ACCENT2)
            editor.pack(fill="both", expand=True)

            def _make_yscroll(sy, ed):
                def _ys(f, l):
                    if float(f) <= 0.0 and float(l) >= 1.0:
                        if sy.winfo_ismapped(): sy.pack_forget()
                    else:
                        if not sy.winfo_ismapped():
                            sy.pack(side="right", fill="y", before=ed)
                    sy.set(f, l)
                return _ys

            def _make_xscroll(sx, ed):
                def _xs(f, l):
                    if float(f) <= 0.0 and float(l) >= 1.0:
                        if sx.winfo_ismapped(): sx.pack_forget()
                    else:
                        if not sx.winfo_ismapped():
                            sx.pack(side="bottom", fill="x", before=ed)
                    sx.set(f, l)
                return _xs

            editor.configure(yscrollcommand=_make_yscroll(editor_scroll_y, editor),
                             xscrollcommand=_make_xscroll(editor_scroll_x, editor))
            editor_scroll_y.config(command=editor.yview)
            editor_scroll_x.config(command=editor.xview)

            # Pre-carica la query
            editor.insert("1.0", _load_query(env_key))
            self._query_editors[env_key] = editor

            # Barra inferiore: status + bottoni
            bar = Frame(body, bg=BG)
            bar.pack(fill="x", pady=(8, 0))

            status_var = StringVar(value="")
            status_lbl = Label(bar, textvariable=status_var, bg=BG, fg=TEXT_SEC,
                               font=("Consolas", 8), anchor="w")
            status_lbl.pack(side="left", fill="x", expand=True)

            def _make_validate_and_save(ek=env_key, ed=editor, sv=status_var, sl=status_lbl):
                def _run_vs():
                    text = ed.get("1.0", "end-1c").strip()
                    if not text:
                        sv.set("⚠ Query vuota.")
                        sl.configure(fg=WARNING)
                        return
                    sv.set("⏳ Validazione in corso ...")
                    sl.configure(fg=TEXT_SEC)
                    self.update()
                    def _run():
                        try:
                            conn = get_hub_connection()
                            cur  = conn.cursor()
                            cur.execute(f"SELECT * FROM ({text}) AS _q LIMIT 0")
                            cur.close()
                            conn.close()
                            try:
                                _save_query(ek, text)
                                self.after(0, lambda: (
                                    sv.set(f"✓ Valida e salvata — {QUERY_SQL_FILES[ek].name}"),
                                    sl.configure(fg=SUCCESS)))
                                self.after(3000, lambda: (sv.set(""), sl.configure(fg=TEXT_SEC)))
                            except Exception as ex:
                                self.after(0, lambda e=ex: (
                                    sv.set(f"✗ Errore salvataggio: {e}"),
                                    sl.configure(fg=ERROR)))
                        except Exception as ex:
                            msg = str(ex).splitlines()[0]
                            self.after(0, lambda m=msg: (
                                sv.set(f"✗ {m}"),
                                sl.configure(fg=ERROR)))
                    threading.Thread(target=_run, daemon=True).start()
                return _run_vs

            self._make_btn(bar, "✔  Valida e salva", _make_validate_and_save(), color=ACCENT).pack(side="right")

    # ── Tab About ─────────────────────────────────────────────────────────

    def _start(self):
        if self._running:
            return
        # Guardia: almeno una modalità selezionata
        if not any(var.get() for var in self._mode_vars.values()):
            self._status_var.set("⚠ Seleziona almeno una modalità.")
            return
        self._running = True
        self._stop_requested = False
        self._btn.configure(fg=TEXT_SEC, cursor="arrow")
        self._btn_stop.configure(fg=ERROR, cursor="hand2")
        target = _get_target_env()
        self._status_var.set(f"In esecuzione → {target} ...")
        threading.Thread(
            target=delta_run_pipeline,
            args=(self, self._enqueue_log, self._on_done, target,
                  self._mode_vars["MODE_DELTA_RECOVERY"].get(),
                  self._mode_vars["MODE_MULTIPLE_PP"].get(),
                  self._mode_vars["MODE_NO_PP_FOR_DATE"].get(),
                  self._run_enabled_var.get()),
            daemon=True,
        ).start()






# ════════════════════════════════════════════════════════════════════════════
# FOLDER CLEANER
# ════════════════════════════════════════════════════════════════════════════

import os
import shutil

_FC_TXT = _HERE / "input" / "folder cleaner" / "folders.txt"


def _fc_load_folders() -> list:
    if not _FC_TXT.exists():
        _FC_TXT.parent.mkdir(parents=True, exist_ok=True)
        _FC_TXT.write_text("", encoding="utf-8")
        return []
    return [line.strip() for line in _FC_TXT.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")]


def _fc_delete(folders: list, log) -> None:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    for folder in folders:
        if not os.path.isdir(folder):
            log(f"[SKIP] Non trovata o non è una cartella: {folder}", "warn")
            continue
        entries = os.listdir(folder)
        files = [e for e in entries if os.path.isfile(os.path.join(folder, e)) or
                                       os.path.islink(os.path.join(folder, e))]
        dirs  = [e for e in entries if os.path.isdir(os.path.join(folder, e))]
        total = len(entries)
        deleted_files = deleted_dirs = errors = done = 0

        def _rm(filename, _folder=folder):
            os.remove(os.path.join(_folder, filename))

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(_rm, f): f for f in files}
            for future in as_completed(futures):
                done += 1
                try:
                    future.result()
                    deleted_files += 1
                except Exception as e:
                    log(f"[WARN] Impossibile eliminare \'{futures[future]}\': {e}", "warn")
                    errors += 1
                if done % 100 == 0:
                    log(f"[INFO] Eliminati {done}/{total} elementi...", "progress")

        for d in dirs:
            done += 1
            try:
                shutil.rmtree(os.path.join(folder, d))
                deleted_dirs += 1
            except Exception as e:
                log(f"[WARN] Impossibile eliminare \'{d}\': {e}", "warn")
                errors += 1
            if done % 100 == 0:
                log(f"[INFO] Eliminati {done}/{total} elementi...", "progress")

        if total % 100 != 0:
            log(f"[INFO] Eliminati {total}/{total} elementi...", "progress")

        parts = []
        if deleted_files: parts.append(f"{deleted_files} file")
        if deleted_dirs:  parts.append(f"{deleted_dirs} cartella/e")
        summary = ", ".join(parts) if parts else "nulla"
        status  = f" ({errors} errori)" if errors else ""
        log(f"[OK] Eliminati {summary} in \'{folder}\'{status}", "ok")


def folder_cleaner_run_pipeline(log, on_done):
    try:
        folders = _fc_load_folders()
        if not folders:
            log("[WARN] folders.txt è vuoto o contiene solo commenti.", "warn")
            on_done(success=False)
            return
        log(f"[INFO] {len(folders)} cartella/e trovata/e", "info")
        _fc_delete(folders, log)
        log("\n[INFO] Pulizia completata.", "ok")
        on_done(success=True)
    except Exception as e:
        log(f"[ERRORE] {e}", "error")
        on_done(success=False)


class FolderCleaner(_AppBase):

    def __init__(self, master):
        super().__init__(master, bg=BG)
        self._log_queue   = queue.Queue()
        self._running     = False
        self._folders: list = []
        self._build_ui()
        self._load_folders()
        self._poll_log()

    def _build_ui(self):
        self._status_var = tkinter.StringVar(value="Pronto.")
        Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, side="bottom")
        self._status_lbl = Label(self, textvariable=self._status_var, bg=BG, fg=TEXT_SEC,
                                  font=("Consolas", 9), anchor="w", pady=5)
        self._status_lbl.pack(fill="x", padx=24, side="bottom")

        body = Frame(self, bg=BG, highlightthickness=1, highlightbackground=BORDER)
        body.pack(fill="both", expand=True, padx=24, pady=(12, 0))

        paned = tkinter.PanedWindow(body, orient="vertical", bg=BORDER,
                                    sashwidth=5, sashrelief="flat", bd=0)
        paned.pack(fill="both", expand=True)

        # ── Pannello superiore: lista cartelle ────────────────────────────
        top = Frame(paned, bg=BG_CARD, bd=0, highlightthickness=1,
                    highlightbackground=BORDER)

        hdr = Frame(top, bg=BG_CARD)
        hdr.pack(fill="x")
        Label(hdr, text="CARTELLE", bg=BG_CARD, fg=TEXT_SEC,
              font=("Consolas", 9, "bold"), pady=10, padx=14).pack(side="left")

        def _icon_btn(parent, symbol, command, color=ACCENT, tip=""):
            lbl = Label(parent, text=symbol, bg=BG_CARD, fg=color,
                        font=("Consolas", 14), cursor="hand2", padx=10, pady=6)
            lbl.bind("<Button-1>", lambda e: command())
            lbl.bind("<Enter>",    lambda e: (lbl.configure(bg=BG_HOVER),
                                              self._status_var.set(tip) if tip else None))
            lbl.bind("<Leave>",    lambda e: (lbl.configure(bg=BG_CARD),
                                              self._status_var.set("Pronto.")))
            return lbl

        # Ordine invertito: 🗑 → + → ▶  (pack side=right → appare sinistra→destra)
        _icon_btn(hdr, "🗑", self._remove_all, ERROR,  "Rimuovi tutto").pack(side="right", padx=(0, 4))
        _icon_btn(hdr, "+", self._browse_folder, SUCCESS, "Aggiungi cartella").pack(side="right", padx=(0, 4))
        self._btn = _icon_btn(hdr, "▶", self._start, ACCENT, "Avvia pulizia")
        self._btn.pack(side="right", padx=(0, 8))
        Frame(top, bg=BORDER, height=1).pack(fill="x", padx=14)

        # Canvas scrollabile per le righe cartelle
        canvas_frame = Frame(top, bg=BG_CARD)
        canvas_frame.pack(fill="both", expand=True, padx=6, pady=6)
        vsb = ttk.Scrollbar(canvas_frame, style="Dark.Vertical.TScrollbar")
        vsb.pack(side="right", fill="y")
        self._fc_vsb = vsb
        self._fc_canvas = tkinter.Canvas(canvas_frame, bg=BG_CARD,
                                         highlightthickness=0,
                                         yscrollcommand=vsb.set)
        self._fc_canvas.pack(side="left", fill="both", expand=True)
        vsb.config(command=self._fc_canvas.yview)
        self._fc_inner = Frame(self._fc_canvas, bg=BG_CARD)
        self._fc_win   = self._fc_canvas.create_window(
            (0, 0), window=self._fc_inner, anchor="nw")
        self._fc_inner.bind("<Configure>", self._fc_update_scroll)
        self._fc_canvas.bind("<Configure>", lambda e: (
            self._fc_canvas.itemconfig(self._fc_win, width=e.width),
            self._fc_update_scroll()
        ))
        self._fc_canvas.bind("<Enter>", lambda e: self._fc_canvas.bind_all(
            "<MouseWheel>", lambda e: self._fc_canvas.yview_scroll(
                -1*(e.delta//120), "units")))
        self._fc_canvas.bind("<Leave>", lambda e: self._fc_canvas.unbind_all(
            "<MouseWheel>"))

        Label(top, text="# Le righe che iniziano con # sono commenti",
              bg=BG_CARD, fg=TEXT_SEC, font=("Consolas", 8),
              anchor="w", padx=14, pady=4).pack(fill="x")
        paned.add(top, minsize=80, height=180, stretch="never")

        # ── Pannello inferiore: log ───────────────────────────────────────
        bottom = Frame(paned, bg=BG_CARD, bd=0, highlightthickness=1,
                       highlightbackground=BORDER)
        self._build_log_panel(bottom, on_clear=self._clear_log)
        paned.add(bottom, minsize=100, stretch="always")

    def _poll_log(self):
        """Override: gestisce il livello 'progress' che sovrascrive l'ultima riga."""
        try:
            while True:
                msg, level = self._log_queue.get_nowait()
                self._log_box.configure(state="normal")
                if level == "progress":
                    last      = self._log_box.index("end-1c linestart")
                    line_text = self._log_box.get(last, "end-1c")
                    if line_text.startswith("["):
                        self._log_box.delete(last, "end-1c")
                        self._log_box.insert("end-1c", msg, "info")
                    else:
                        self._log_box.insert("end", msg + "\n", "info")
                else:
                    self._log_box.insert("end", msg + "\n", level)
                self._log_box.see("end")
                self._log_box.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(80, self._poll_log)

    def _on_done(self, success: bool):
        self._running = False
        if success:
            self._status_var.set("✓ Pulizia completata.")
            self._btn.configure(fg=SUCCESS, cursor="hand2")
        else:
            self._status_var.set("✗ Terminato con errori o avvisi.")
            self._btn.configure(fg=ERROR, cursor="hand2")
        self.after(3000, self._update_btn_state)

    # ── Lista cartelle ──────────────────────────────────────────────────────

    def _fc_update_scroll(self, _e=None):
        """Aggiorna la scrollregion e mostra/nasconde la scrollbar."""
        self._fc_canvas.update_idletasks()
        content_h = self._fc_inner.winfo_reqheight()
        canvas_h  = self._fc_canvas.winfo_height()
        if content_h > canvas_h:
            if not self._fc_vsb.winfo_ismapped():
                self._fc_vsb.pack(side="right", fill="y")
            self._fc_canvas.configure(scrollregion=(0, 0, 0, content_h))
        else:
            if self._fc_vsb.winfo_ismapped():
                self._fc_vsb.pack_forget()
            self._fc_canvas.configure(scrollregion=(0, 0, 0, canvas_h))
            self._fc_canvas.yview_moveto(0)

    def _load_folders(self):
        """Carica da file e ri-renderizza la lista."""
        raw = _FC_TXT.read_text(encoding="utf-8") if _FC_TXT.exists() else ""
        self._folders = [l.strip() for l in raw.splitlines()
                         if l.strip() and not l.strip().startswith("#")]
        self._render_rows()
        self._update_btn_state()

    def _render_rows(self):
        """Ri-disegna tutte le righe nel canvas."""
        for w in self._fc_inner.winfo_children():
            w.destroy()
        for path in self._folders:
            row = Frame(self._fc_inner, bg=BG_CARD)
            row.pack(fill="x", padx=6, pady=1)
            x_lbl = Label(row, text="✕", bg=BG_CARD, fg=ERROR,
                          font=("Consolas", 10, "bold"), cursor="hand2",
                          padx=8, pady=4)
            x_lbl.pack(side="left")
            x_lbl.bind("<Button-1>", lambda e, p=path: self._remove_line(p))
            x_lbl.bind("<Enter>",    lambda e, l=x_lbl: l.configure(bg=BG_HOVER))
            x_lbl.bind("<Leave>",    lambda e, l=x_lbl: l.configure(bg=BG_CARD))
            Label(row, text=path, bg=BG_CARD, fg=TEXT_PRI,
                  font=("Consolas", 10), anchor="w", pady=4).pack(
                  side="left", fill="x", expand=True)
            Frame(self._fc_inner, bg=BORDER, height=1).pack(fill="x", padx=6)
        self._fc_update_scroll()

    def _save_folders(self):
        """Salva la lista corrente su file."""
        content = "\n".join(self._folders)
        try:
            _FC_TXT.parent.mkdir(parents=True, exist_ok=True)
            _FC_TXT.write_text(content, encoding="utf-8")
            self._status_var.set("✓ folders.txt salvato.")
        except Exception as e:
            messagebox.showerror("Errore salvataggio", str(e))

    def _update_btn_state(self):
        has = bool(self._folders)
        self._btn.configure(fg=ACCENT if has else TEXT_SEC,
                            cursor="hand2" if has else "arrow")

    def _remove_line(self, path: str):
        if path in self._folders:
            self._folders.remove(path)
            self._render_rows()
            self._save_folders()
            self._update_btn_state()

    def _remove_all(self):
        if not self._folders:
            return
        if not messagebox.askyesno("Rimuovi tutto",
                                   "Rimuovere tutte le cartelle dalla lista?"):
            return
        self._folders.clear()
        self._render_rows()
        self._save_folders()
        self._update_btn_state()

    def _browse_folder(self):
        path = filedialog.askdirectory(title="Seleziona cartella da aggiungere")
        if not path:
            return
        if self._check_duplicate(path, self._folders):
            return
        self._folders.append(path)
        self._render_rows()
        self._save_folders()
        self._update_btn_state()

    def _start(self):
        if self._running or not self._folders:
            return
        self._running = True
        self._btn.configure(fg=TEXT_SEC, cursor="arrow")
        self._status_var.set("In esecuzione...")
        threading.Thread(
            target=folder_cleaner_run_pipeline,
            args=(self._enqueue_log, self._on_done),
            daemon=True,
        ).start()

# ════════════════════════════════════════════════════════════════════════════
# SHELL — Finestra principale con sidebar verticale
# ════════════════════════════════════════════════════════════════════════════


_SB_BG       = "#0d1020"
_SB_BG_SEL   = "#1a1d27"
_SB_ITEM_BG  = "#131628"
_SB_ACCENT   = "#4f8ef7"
_SB_ACCENT2  = "#7c3aed"
_SB_TEXT     = "#8892b0"
_SB_TEXT_SEL = "#f0f2ff"
_SB_BORDER   = "#2a2d3e"


# ════════════════════════════════════════════════════════════════════════════
# FOLDER MOVER
# ════════════════════════════════════════════════════════════════════════════

import shutil as _shutil

_FM_TXT = _HERE / "input" / "folder mover" / "folders.txt"


def _fm_load_entries() -> list:
    if not _FM_TXT.exists():
        _FM_TXT.parent.mkdir(parents=True, exist_ok=True)
        _FM_TXT.write_text("", encoding="utf-8")
        return []
    return [line.strip() for line in _FM_TXT.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")]


def _fm_copy_files(entries: list, log, cancel_event) -> bool:
    if len(entries) % 2 != 0:
        log("[ERRORE] Il numero di righe deve essere pari (coppie sorgente/destinazione).", "error")
        return False

    pairs = [(entries[i], entries[i + 1]) for i in range(0, len(entries), 2)]

    for source, destination in pairs:
        if cancel_event.is_set():
            log("[INFO] Copia annullata.", "warn")
            return False

        if not os.path.isdir(source):
            log(f"[SKIP] Sorgente non trovata: {source}", "warn")
            continue

        if os.path.exists(destination):
            _shutil.rmtree(destination)
            log(f"[INFO] Destinazione svuotata: \'{destination}\'", "info")

        os.makedirs(destination, exist_ok=True)
        log(f"[INFO] Copia: \'{source}\' → \'{destination}\'", "info")

        files = [f for f in os.listdir(source)
                 if os.path.isfile(os.path.join(source, f))]
        total = len(files)
        errors = copied = 0
        for filename in files:
            if cancel_event.is_set():
                log("[INFO] Copia annullata.", "warn")
                return False
            try:
                _shutil.copyfile(os.path.join(source, filename),
                                 os.path.join(destination, filename))
                copied += 1
            except Exception as e:
                log(f"[WARN] Errore copiando \'{filename}\': {e}", "warn")
                errors += 1
            if (copied + errors) % 100 == 0:
                log(f"[INFO] Copiati {copied + errors}/{total} file...", "progress")

        if total % 100 != 0:
            log(f"[INFO] Copiati {total}/{total} file...", "progress")
        log(f"[OK] {copied} file copiati da \'{source}\' a \'{destination}\'"
            + (f" ({errors} errori)" if errors else ""), "ok")

    return True


def folder_mover_run_pipeline(log, on_done, cancel_event):
    try:
        entries = _fm_load_entries()
        if not entries:
            log("[WARN] folders.txt è vuoto o contiene solo commenti.", "warn")
            on_done(success=False)
            return
        log(f"[INFO] {len(entries) // 2} coppia/e trovata/e", "info")
        ok = _fm_copy_files(entries, log, cancel_event)
        if ok:
            log("\n[INFO] Copia completata.", "ok")
        on_done(success=ok)
    except Exception as e:
        log(f"[ERRORE] {e}", "error")
        on_done(success=False)


class FolderMover(_AppBase):

    def __init__(self, master):
        super().__init__(master, bg=BG)
        self._log_queue     = queue.Queue()
        self._running       = False
        self._pairs_data    = []
        self._selected_pair = None
        self._cancel_event  = threading.Event()
        self._build_ui()
        self._load_into_list()
        self._poll_log()

    def _build_ui(self):
        self._status_var = tkinter.StringVar(value="Pronto.")
        Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, side="bottom")
        self._status_lbl = Label(self, textvariable=self._status_var, bg=BG, fg=TEXT_SEC,
                                  font=("Consolas", 9), anchor="w", pady=5)
        self._status_lbl.pack(fill="x", padx=24, side="bottom")

        body = Frame(self, bg=BG, highlightthickness=1, highlightbackground=BORDER)
        body.pack(fill="both", expand=True, padx=24, pady=(12, 0))

        paned = tkinter.PanedWindow(body, orient="vertical", bg=BORDER,
                                    sashwidth=5, sashrelief="flat", bd=0)
        paned.pack(fill="both", expand=True)

        # ── Pannello superiore: lista coppie ──────────────────────────────
        top = Frame(paned, bg=BG_CARD, bd=0, highlightthickness=1,
                    highlightbackground=BORDER)

        hdr = Frame(top, bg=BG_CARD)
        hdr.pack(fill="x")
        Label(hdr, text="COPPIE  SORGENTE → DESTINAZIONE", bg=BG_CARD, fg=TEXT_SEC,
              font=("Consolas", 9, "bold"), pady=10, padx=14).pack(side="left")

        def _icon_btn(parent, symbol, command, color=ACCENT, tip=""):
            lbl = Label(parent, text=symbol, bg=BG_CARD, fg=color,
                        font=("Consolas", 14), cursor="hand2", padx=10, pady=6)
            lbl.bind("<Button-1>", lambda e: command())
            lbl.bind("<Enter>",    lambda e: (lbl.configure(bg=BG_HOVER),
                                              self._status_var.set(tip) if tip else None))
            lbl.bind("<Leave>",    lambda e: (lbl.configure(bg=BG_CARD),
                                              self._status_var.set("Pronto.")))
            return lbl

        _icon_btn(hdr, "🗑", self._remove_all,  ERROR,   "Rimuovi tutto").pack(side="right", padx=(0, 4))
        _icon_btn(hdr, "+", self._browse_pair,  SUCCESS, "Aggiungi coppia").pack(side="right", padx=(0, 4))
        self._btn = _icon_btn(hdr, "▶", self._start, ACCENT, "Avvia copia")
        self._btn.pack(side="right", padx=(0, 8))
        Frame(top, bg=BORDER, height=1).pack(fill="x", padx=14)

        # Canvas scrollabile
        canvas_frame = Frame(top, bg=BG_CARD)
        canvas_frame.pack(fill="both", expand=True, padx=6, pady=6)
        self._fm_vsb = ttk.Scrollbar(canvas_frame, style="Dark.Vertical.TScrollbar")
        self._fm_vsb.pack(side="right", fill="y")
        self._fm_canvas = tkinter.Canvas(canvas_frame, bg=BG_CARD,
                                         highlightthickness=0,
                                         yscrollcommand=self._fm_vsb.set)
        self._fm_canvas.pack(side="left", fill="both", expand=True)
        self._fm_vsb.config(command=self._fm_canvas.yview)
        self._fm_inner = Frame(self._fm_canvas, bg=BG_CARD)
        self._fm_win = self._fm_canvas.create_window(
            (0, 0), window=self._fm_inner, anchor="nw")
        self._fm_inner.bind("<Configure>", self._fm_update_scroll)
        self._fm_canvas.bind("<Configure>", lambda e: (
            self._fm_canvas.itemconfig(self._fm_win, width=e.width),
            self._fm_update_scroll()
        ))
        self._fm_canvas.bind("<Enter>", lambda e: self._fm_canvas.bind_all(
            "<MouseWheel>", lambda e: self._fm_canvas.yview_scroll(
                -1*(e.delta//120), "units")))
        self._fm_canvas.bind("<Leave>", lambda e: self._fm_canvas.unbind_all(
            "<MouseWheel>"))

        self._warn_label = Label(top, text="", bg=BG_CARD, fg=WARNING,
                                 font=("Consolas", 8), anchor="w", padx=14, pady=2)
        self._warn_label.pack(fill="x")
        paned.add(top, minsize=80, height=220, stretch="never")

        # ── Pannello inferiore: log ───────────────────────────────────────
        bottom = Frame(paned, bg=BG_CARD, bd=0, highlightthickness=1,
                       highlightbackground=BORDER)
        self._build_log_panel(bottom, on_clear=self._clear_log)
        paned.add(bottom, minsize=100, stretch="always")

    def _fm_update_scroll(self, _e=None):
        self._fm_canvas.update_idletasks()
        content_h = self._fm_inner.winfo_reqheight()
        canvas_h  = self._fm_canvas.winfo_height()
        if content_h > canvas_h:
            if not self._fm_vsb.winfo_ismapped():
                self._fm_vsb.pack(side="right", fill="y")
            self._fm_canvas.configure(scrollregion=(0, 0, 0, content_h))
        else:
            if self._fm_vsb.winfo_ismapped():
                self._fm_vsb.pack_forget()
            self._fm_canvas.configure(scrollregion=(0, 0, 0, canvas_h))
            self._fm_canvas.yview_moveto(0)

    def _poll_log(self):
        """Override: gestisce il livello 'progress' che sovrascrive l'ultima riga."""
        try:
            while True:
                msg, level = self._log_queue.get_nowait()
                self._log_box.configure(state="normal")
                if level == "progress":
                    last      = self._log_box.index("end-1c linestart")
                    line_text = self._log_box.get(last, "end-1c")
                    if line_text.startswith("["):
                        self._log_box.delete(last, "end-1c")
                        self._log_box.insert("end-1c", msg, "info")
                    else:
                        self._log_box.insert("end", msg + "\n", "info")
                else:
                    self._log_box.insert("end", msg + "\n", level)
                self._log_box.see("end")
                self._log_box.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(80, self._poll_log)

    def _on_done(self, success: bool):
        self._running = False
        if success:
            self._status_var.set("✓ Copia completata.")
            self._btn.configure(fg=SUCCESS, cursor="hand2")
        else:
            self._status_var.set("✗ Terminato con errori o avvisi.")
            self._btn.configure(fg=ERROR, cursor="hand2")
        self.after(3000, self._update_btn_state)

    # ── Lista coppie ──────────────────────────────────────────────────────

    def _load_into_list(self):
        raw = _FM_TXT.read_text(encoding="utf-8") if _FM_TXT.exists() else ""
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        self._pairs_data = []
        for i in range(0, len(lines) - 1, 2):
            self._pairs_data.append((lines[i], lines[i + 1]))
        orphan = lines[-1] if len(lines) % 2 != 0 and lines else None
        self._selected_pair = None
        self._redraw_pairs(orphan)

    def _redraw_pairs(self, orphan=None):
        for w in self._fm_inner.winfo_children():
            w.destroy()
        for idx, (src, dst) in enumerate(self._pairs_data):
            self._draw_pair_row(idx, src, dst)
        self._warn_label.configure(
            text=f"⚠  Riga orfana (senza destinazione): {orphan}" if orphan else "")
        self._update_btn_state()
        self._fm_update_scroll()

    def _draw_pair_row(self, idx: int, src: str, dst: str):
        is_sel = (idx == self._selected_pair)
        row_bg = BG_HOVER if is_sel else BG_CARD

        row = Frame(self._fm_inner, bg=row_bg, cursor="hand2")
        row.pack(fill="x", pady=(0, 1))

        x_lbl = Label(row, text="✕", bg=row_bg, fg=ERROR,
                      font=("Consolas", 10, "bold"), cursor="hand2", padx=8, pady=6)
        x_lbl.pack(side="left")
        x_lbl.bind("<Button-1>", lambda e, i=idx: self._remove_by_index(i))
        x_lbl.bind("<Enter>",    lambda e, l=x_lbl: l.configure(bg=BG_HOVER))
        x_lbl.bind("<Leave>",    lambda e, l=x_lbl, b=row_bg: l.configure(bg=b))

        col = Frame(row, bg=row_bg)
        col.pack(side="left", fill="x", expand=True, pady=4, padx=(0, 6))

        src_row = Frame(col, bg=row_bg)
        src_row.pack(fill="x")
        Label(src_row, text="SRC", bg=row_bg, fg=ACCENT,
              font=("Consolas", 8, "bold"), padx=4).pack(side="left")
        Label(src_row, text=src, bg=row_bg, fg=TEXT_PRI,
              font=("Consolas", 9), anchor="w").pack(side="left", fill="x", expand=True)

        dst_row = Frame(col, bg=row_bg)
        dst_row.pack(fill="x")
        Label(dst_row, text="DST", bg=row_bg, fg=ACCENT2,
              font=("Consolas", 8, "bold"), padx=4).pack(side="left")
        Label(dst_row, text=dst, bg=row_bg, fg=TEXT_SEC,
              font=("Consolas", 9), anchor="w").pack(side="left", fill="x", expand=True)

        for w in [row, col, src_row, dst_row] + list(src_row.winfo_children()) + list(dst_row.winfo_children()):
            w.bind("<Button-1>", lambda e, i=idx: self._select_pair(i))

        Frame(self._fm_inner, bg=BORDER, height=1).pack(fill="x", padx=6)

    def _select_pair(self, idx: int):
        self._selected_pair = idx
        self._redraw_pairs()

    def _remove_by_index(self, idx: int):
        self._pairs_data.pop(idx)
        self._selected_pair = None
        self._save_and_reload()

    def _remove_pair(self):
        if self._selected_pair is None:
            self._status_var.set("⚠ Seleziona una coppia prima di rimuoverla.")
            return
        self._pairs_data.pop(self._selected_pair)
        self._selected_pair = None
        self._save_and_reload()

    def _remove_all(self):
        if not self._pairs_data:
            return
        if not messagebox.askyesno("Rimuovi tutto",
                                   "Rimuovere tutte le coppie dalla lista?"):
            return
        self._pairs_data.clear()
        self._selected_pair = None
        self._save_and_reload()

    def _save_and_reload(self):
        lines = []
        for src, dst in self._pairs_data:
            lines.append(src)
            lines.append(dst)
        content = "\n".join(lines)
        try:
            _FM_TXT.parent.mkdir(parents=True, exist_ok=True)
            _FM_TXT.write_text(content, encoding="utf-8")
            self._status_var.set("✓ folders.txt salvato.")
        except Exception as e:
            messagebox.showerror("Errore salvataggio", str(e))
        self._redraw_pairs()

    def _browse_pair(self):
        src = filedialog.askdirectory(title="Seleziona cartella SORGENTE")
        if not src:
            return
        dst = filedialog.askdirectory(title="Seleziona cartella DESTINAZIONE")
        if not dst:
            return
        if os.path.normpath(src) == os.path.normpath(dst):
            messagebox.showerror("Percorsi identici",
                                 "Sorgente e destinazione non possono essere la stessa cartella.")
            return
        if (src, dst) in self._pairs_data:
            self._warn_status("⚠ Coppia già presente nella lista.")
            return
        self._pairs_data.append((src, dst))
        self._save_and_reload()

    def _update_btn_state(self):
        has = bool(self._pairs_data)
        self._btn.configure(fg=ACCENT if has else TEXT_SEC,
                            cursor="hand2" if has else "arrow")

    def _start(self):
        if self._running or not self._pairs_data:
            return
        self._cancel_event.clear()
        self._running = True
        self._btn.configure(fg=TEXT_SEC, cursor="arrow")
        self._status_var.set("In esecuzione...")
        threading.Thread(
            target=folder_mover_run_pipeline,
            args=(self._enqueue_log, self._on_done, self._cancel_event),
            daemon=True,
        ).start()


def _make_flag_icon(master=None):
    """Crea un PhotoImage 32x32 con la bandiera francese per l'icona della finestra."""
    img = tkinter.PhotoImage(width=32, height=32, master=master)
    for y in range(32):
        for x in range(32):
            if x < 11:
                color = "#002395"
            elif x < 21:
                color = "#ffffff"
            else:
                color = "#ED2939"
            img.put(color, (x, y))
    return img




# ════════════════════════════════════════════════════════════════════════════
# ZIP FOLDER
# ════════════════════════════════════════════════════════════════════════════

import zipfile as _zipfile

_ZF_TXT        = _HERE / "input" / "zip folder" / "folders.txt"
_ZF_DEFAULT_OUT = _HERE / "output" / "zip folder"


def _zf_load_folders() -> list:
    if not _ZF_TXT.exists():
        _ZF_TXT.parent.mkdir(parents=True, exist_ok=True)
        _ZF_TXT.write_text("", encoding="utf-8")
        return []
    folders = []
    for line in _ZF_TXT.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fp = Path(line)
        if fp.exists() and fp.is_dir():
            folders.append(fp)
    return folders


def _zf_zip_folder(input_path, output_dir, log, cancel_event, filter_str="") -> bool:
    import time
    zip_path  = output_dir / f"{input_path.name}.zip"
    all_files = [f for f in input_path.rglob("*") if f.is_file()]
    if filter_str:
        files = [f for f in all_files if filter_str in f.name]
        log(f"[INFO] Filtro '{filter_str}': {len(files)}/{len(all_files)} file.", "info")
    else:
        files = all_files
    total = len(files)
    if not files:
        log(f"[WARN] Nessun file in '{input_path.name}', saltata.", "warn")
        return False
    log(f"[INFO] ZIP: '{input_path.name}' ({total} file)...", "info")
    with _zipfile.ZipFile(zip_path, "w", _zipfile.ZIP_DEFLATED) as zf:
        for i, file in enumerate(files, 1):
            if cancel_event.is_set():
                log("[INFO] Operazione annullata.", "warn")
                return False
            arcname = file.relative_to(input_path)
            t0 = time.monotonic()
            zf.write(file, arcname)
            elapsed = time.monotonic() - t0
            if elapsed > 2:
                size_mb = file.stat().st_size / 1024 / 1024
                log(f"[WARN] File lento ({elapsed:.1f}s, {size_mb:.1f} MB): {file.name}", "warn")
            if i % 100 == 0:
                log(f"[INFO] Compressi {i}/{total} file...", "progress")
    if total % 100 != 0:
        log(f"[INFO] Compressi {total}/{total} file...", "progress")
    size_kb = zip_path.stat().st_size / 1024
    log(f"[OK] {zip_path.name}  ({size_kb:.1f} KB)", "ok")
    return True


def zip_folder_run_pipeline(output_dir, log, on_done, cancel_event, filter_str=""):
    try:
        folders = _zf_load_folders()
        if not folders:
            log("[WARN] Nessuna cartella valida in folders.txt.", "warn")
            on_done(success=False)
            return
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        info = f" | filtro: '{filter_str}'" if filter_str else ""
        log(f"[INFO] {len(folders)} cartella/e — output: '{output_dir}'{info}", "info")
        ok = skipped = 0
        for folder in folders:
            if cancel_event.is_set():
                log("[INFO] Operazione annullata.", "warn")
                on_done(success=False)
                return
            log(f"\n── {folder.name} ──", "section")
            if _zf_zip_folder(folder, output_dir, log, cancel_event, filter_str):
                ok += 1
            else:
                skipped += 1
        log(f"\n[INFO] Completati: {ok}  |  Saltati: {skipped}  |  Output: '{output_dir}'", "ok")
        on_done(success=True)
    except Exception as e:
        log(f"[ERRORE] {e}", "error")
        on_done(success=False)


class ZipFolder(_AppBase):

    def __init__(self, master):
        super().__init__(master, bg=BG)
        self._log_queue     = queue.Queue()
        self._running       = False
        self._folders_data  = []
        self._cancel_event  = threading.Event()
        self._output_dir    = str(_ZF_DEFAULT_OUT)
        self._build_ui()
        self._load_into_list()
        self._update_btn_state()
        self._poll_log()

    def _build_ui(self):
        self._status_var = tkinter.StringVar(value="Pronto.")
        Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, side="bottom")
        self._status_lbl = Label(self, textvariable=self._status_var, bg=BG, fg=TEXT_SEC,
                                  font=("Consolas", 9), anchor="w", pady=5)
        self._status_lbl.pack(fill="x", padx=24, side="bottom")

        body = Frame(self, bg=BG, highlightthickness=1, highlightbackground=BORDER)
        body.pack(fill="both", expand=True, padx=24, pady=(12, 0))

        paned = tkinter.PanedWindow(body, orient="vertical",
                                    bg=BORDER, sashwidth=5,
                                    sashrelief="flat", bd=0)
        paned.pack(fill="both", expand=True)

        # ── Pannello superiore: lista cartelle ───────────────────────────
        top = Frame(paned, bg=BG_CARD, bd=0, highlightthickness=1,
                     highlightbackground=BORDER)

        hdr = Frame(top, bg=BG_CARD)
        hdr.pack(fill="x")
        Label(hdr, text="CARTELLE", bg=BG_CARD, fg=TEXT_SEC,
              font=("Consolas", 9, "bold"), pady=10, padx=14).pack(side="left")

        def _icon_btn(parent, symbol, command, color=ACCENT, tip=""):
            lbl = Label(parent, text=symbol, bg=BG_CARD, fg=color,
                        font=("Consolas", 14), cursor="hand2", padx=10, pady=6)
            lbl.bind("<Button-1>", lambda e: command())
            lbl.bind("<Enter>",    lambda e: (lbl.configure(bg=BG_HOVER),
                                              self._status_var.set(tip) if tip else None))
            lbl.bind("<Leave>",    lambda e: (lbl.configure(bg=BG_CARD),
                                              self._status_var.set("Pronto.")))
            return lbl

        _icon_btn(hdr, "🗑", self._clear_all,    ERROR,   "Rimuovi tutto").pack(side="right", padx=(0, 4))
        _icon_btn(hdr, "+", self._browse_folder, SUCCESS, "Aggiungi cartella").pack(side="right", padx=(0, 4))
        self._btn = _icon_btn(hdr, "▶", self._start, ACCENT, "Avvia ZIP")
        self._btn.pack(side="right", padx=(0, 8))
        Frame(top, bg=BORDER, height=1).pack(fill="x", padx=14)

        # Canvas scrollabile per lista cartelle
        canvas_frame = Frame(top, bg=BG_CARD)
        canvas_frame.pack(fill="both", expand=True, padx=6, pady=6)
        self._zf_vsb = ttk.Scrollbar(canvas_frame, style="Dark.Vertical.TScrollbar")
        self._zf_vsb.pack(side="right", fill="y")
        self._zf_canvas = tkinter.Canvas(canvas_frame, bg=BG_CARD,
                                         highlightthickness=0,
                                         yscrollcommand=self._zf_vsb.set)
        self._zf_canvas.pack(side="left", fill="both", expand=True)
        self._zf_vsb.config(command=self._zf_canvas.yview)
        self._zf_inner = Frame(self._zf_canvas, bg=BG_CARD)
        self._zf_win = self._zf_canvas.create_window((0, 0), window=self._zf_inner, anchor="nw")
        self._zf_inner.bind("<Configure>", self._zf_update_scroll)
        self._zf_canvas.bind("<Configure>", lambda e: (
            self._zf_canvas.itemconfig(self._zf_win, width=e.width),
            self._zf_update_scroll()
        ))
        self._zf_canvas.bind("<Enter>", lambda e: self._zf_canvas.bind_all(
            "<MouseWheel>", lambda e: self._zf_canvas.yview_scroll(-1*(e.delta//120), "units")))
        self._zf_canvas.bind("<Leave>", lambda e: self._zf_canvas.unbind_all("<MouseWheel>"))

        paned.add(top, minsize=80, height=180, stretch="never")

        # ── Pannello centrale: filtro e output dir ───────────────────────
        opts = Frame(paned, bg=BG_CARD, bd=0, highlightthickness=1,
                     highlightbackground=BORDER)
        filter_row = Frame(opts, bg=BG_CARD)
        filter_row.pack(fill="x", padx=14, pady=(6, 2))
        self._filter_enabled = tkinter.BooleanVar(value=False)
        tkinter.Checkbutton(
            filter_row, text="Filtra per testo nel nome file",
            variable=self._filter_enabled,
            bg=BG_CARD, fg=TEXT_SEC, selectcolor=BG_INPUT,
            activebackground=BG_CARD, activeforeground=TEXT_PRI,
            font=("Consolas", 9), cursor="hand2",
            command=self._on_filter_toggle,
        ).pack(side="left")
        self._filter_var = tkinter.StringVar()
        self._filter_entry = tkinter.Entry(
            filter_row, textvariable=self._filter_var,
            bg=BG_INPUT, fg=TEXT_PRI, insertbackground=TEXT_PRI,
            relief="flat", font=("Consolas", 9),
            disabledbackground=BG_INPUT, disabledforeground=TEXT_SEC,
            state="disabled",
        )
        self._filter_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))
        Frame(opts, bg=BORDER, height=1).pack(fill="x", padx=14)
        out_row = Frame(opts, bg=BG_CARD)
        out_row.pack(fill="x", padx=14, pady=(4, 6))
        Label(out_row, text="Output", bg=BG_CARD, fg=TEXT_SEC,
              font=("Consolas", 9, "bold"), width=7, anchor="w").pack(side="left")
        self._out_var = tkinter.StringVar(value=str(_ZF_DEFAULT_OUT))
        tkinter.Entry(out_row, textvariable=self._out_var,
                      bg=BG_INPUT, fg=TEXT_PRI, insertbackground=TEXT_PRI,
                      relief="flat", font=("Consolas", 9)).pack(
                      side="left", fill="x", expand=True, padx=(6, 4))
        browse_out = Label(out_row, text="📁", bg=BG_CARD, fg=ACCENT,
                           cursor="hand2", font=("Consolas", 12))
        browse_out.pack(side="left")
        browse_out.bind("<Button-1>", lambda e: self._browse_output())
        paned.add(opts, minsize=60, height=70, stretch="never")

        # ── Pannello inferiore: log ──────────────────────────────────────
        bottom = Frame(paned, bg=BG_CARD, bd=0, highlightthickness=1,
                       highlightbackground=BORDER)
        self._build_log_panel(bottom, on_clear=self._clear_log)
        paned.add(bottom, minsize=100, stretch="always")

    # ── Lista cartelle ────────────────────────────────────────────────────

    def _zf_update_scroll(self, _e=None):
        self._zf_canvas.update_idletasks()
        content_h = self._zf_inner.winfo_reqheight()
        canvas_h  = self._zf_canvas.winfo_height()
        if content_h > canvas_h:
            if not self._zf_vsb.winfo_ismapped():
                self._zf_vsb.pack(side="right", fill="y")
            self._zf_canvas.configure(scrollregion=(0, 0, 0, content_h))
        else:
            if self._zf_vsb.winfo_ismapped():
                self._zf_vsb.pack_forget()
            self._zf_canvas.configure(scrollregion=(0, 0, 0, canvas_h))
            self._zf_canvas.yview_moveto(0)

    def _load_into_list(self):
        raw = _ZF_TXT.read_text(encoding="utf-8") if _ZF_TXT.exists() else ""
        self._folders_data = [l.strip() for l in raw.splitlines() if l.strip()]
        self._redraw_folders()

    def _redraw_folders(self):
        for w in self._zf_inner.winfo_children():
            w.destroy()
        for path in self._folders_data:
            row = Frame(self._zf_inner, bg=BG_CARD)
            row.pack(fill="x", padx=6, pady=1)
            x_lbl = Label(row, text="✕", bg=BG_CARD, fg=ERROR,
                          font=("Consolas", 10, "bold"), cursor="hand2",
                          padx=8, pady=4)
            x_lbl.pack(side="left")
            x_lbl.bind("<Button-1>", lambda e, p=path: self._remove_by_path(p))
            x_lbl.bind("<Enter>",    lambda e, l=x_lbl: l.configure(bg=BG_HOVER))
            x_lbl.bind("<Leave>",    lambda e, l=x_lbl: l.configure(bg=BG_CARD))
            Label(row, text=path, bg=BG_CARD, fg=TEXT_PRI,
                  font=("Consolas", 10), anchor="w", pady=4).pack(
                  side="left", fill="x", expand=True)
            Frame(self._zf_inner, bg=BORDER, height=1).pack(fill="x", padx=6)
        self._update_btn_state()
        self._zf_update_scroll()

    def _remove_by_path(self, path):
        if path in self._folders_data:
            self._folders_data.remove(path)
            self._save_and_reload()

    def _remove_by_index(self, idx):
        self._folders_data.pop(idx)
        self._save_and_reload()

    def _clear_all(self):
        if not self._folders_data:
            return
        if not messagebox.askyesno("Svuota tutto", "Rimuovere tutti i percorsi dalla lista?"):
            return
        self._folders_data.clear()
        self._save_and_reload()

    def _save_and_reload(self):
        content = "\n".join(self._folders_data)
        try:
            _ZF_TXT.parent.mkdir(parents=True, exist_ok=True)
            _ZF_TXT.write_text(content, encoding="utf-8")
            self._status_var.set("✓ folders.txt salvato.")
        except Exception as e:
            messagebox.showerror("Errore salvataggio", str(e))
        self._redraw_folders()

    def _update_btn_state(self):
        has = bool(self._folders_data)
        self._btn.configure(fg=ACCENT if has else TEXT_SEC,
                            cursor="hand2" if has else "arrow")

    def _browse_folder(self):
        path = filedialog.askdirectory(title="Seleziona cartella da zippare")
        if not path:
            return
        if self._check_duplicate(path, self._folders_data):
            return
        self._folders_data.append(path)
        self._save_and_reload()

    def _browse_output(self):
        path = filedialog.askdirectory(title="Seleziona cartella di output")
        if path:
            self._out_var.set(path)
            self._status_var.set(f"Output: {path}")

    def _on_filter_toggle(self):
        state = "normal" if self._filter_enabled.get() else "disabled"
        self._filter_entry.configure(state=state)
        if state == "normal":
            self._filter_entry.focus_set()

    # ── Pipeline ─────────────────────────────────────────────────────────

    def _poll_log(self):
        try:
            while True:
                msg, level = self._log_queue.get_nowait()
                self._log_box.configure(state="normal")
                if level == "progress":
                    last      = self._log_box.index("end-1c linestart")
                    last_text = self._log_box.get(last, "end-1c")
                    if "[INFO] Compressi" in last_text:
                        self._log_box.delete(last, "end-1c")
                        self._log_box.insert("end-1c", msg, "info")
                    else:
                        self._log_box.insert("end", msg + "\n", "info")
                else:
                    self._log_box.insert("end", msg + "\n", level)
                self._log_box.see("end")
                self._log_box.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(80, self._poll_log)

    def _on_done(self, success: bool):
        self._running = False
        if success:
            self._status_var.set("✓ ZIP completati.")
            self._btn.configure(fg=SUCCESS, cursor="hand2")
        else:
            self._status_var.set("✗ Terminato con errori o avvisi.")
            self._btn.configure(fg=ERROR, cursor="hand2")
        self.after(3000, self._update_btn_state)

    def _start(self):
        if self._running or not self._folders_data:
            return
        self._cancel_event.clear()
        output_dir = self._out_var.get().strip() or str(_ZF_DEFAULT_OUT)
        self._running = True
        self._btn.configure(fg=TEXT_SEC, cursor="arrow")
        self._status_var.set("In esecuzione...")
        filter_str = self._filter_var.get().strip() if self._filter_enabled.get() else ""
        threading.Thread(
            target=zip_folder_run_pipeline,
            args=(output_dir, self._enqueue_log, self._on_done,
                  self._cancel_event, filter_str),
            daemon=True,
        ).start()



# ════════════════════════════════════════════════════════════════════════════
# PAYMENT PLANS FILTER
# ════════════════════════════════════════════════════════════════════════════

_PP_BASE = _HERE / "input" / "payment plans filter"
_PP_FILTER_FILES = {
    "agreement_id":           _PP_BASE / "filter_agreement_id.txt",
    "supply_code_number":     _PP_BASE / "filter_prm_kraken.txt",
    "agreement_id_plan_type": _PP_BASE / "filter_agreement_plan_type.txt",
}
_PP_FILTER_LABELS = {
    "agreement_id":           "Agreement ID",
    "supply_code_number":     "Prm + Kraken Account",
    "agreement_id_plan_type": "Agreement ID + Plan Type",
}
_PP_FILTER_KEY_OPTIONS = [
    "Agreement ID", "Prm + Kraken Account", "Agreement ID + Plan Type"]
_PP_FILTER_KEY_MAP = {
    "Agreement ID":             "agreement_id",
    "Prm + Kraken Account":     "supply_code_number",
    "Agreement ID + Plan Type": "agreement_id_plan_type",
}
_PP_FILTER_KEY_MAP_INV = {v: k for k, v in _PP_FILTER_KEY_MAP.items()}
_PP_DEFAULTS = {
    "PP_OUTPUT_SUBFOLDER":  "output",
    "PP_ZIP_FILENAME":      "plan.zip",
    "PP_MAGHEGGIO":         "false",
    "PP_PROGRESS_INTERVAL": "100",
    "PP_AGREEMENT_ID_COL":  "0",
    "PP_NUMBER_COL":        "4",
    "PP_SUPPLY_CODE_COL":   "3",
    "PP_PLAN_TYPE_ID_COL":  "11",
    "PP_FILTER_KEY":        "agreement_id",
}


def _pp_get(key):
    return _read_env_raw().get(key, _PP_DEFAULTS.get(key, ""))


def _pp_build_filter_key(columns, cfg):
    key_type = cfg["filter_key"]
    try:
        if key_type == "supply_code_number":
            return columns[cfg["supply_code_col"]] + ";" + columns[cfg["number_col"]]
        elif key_type == "agreement_id_plan_type":
            return columns[cfg["agreement_id_col"]] + ";" + columns[cfg["plan_type_id_col"]]
        else:
            return columns[cfg["agreement_id_col"]]
    except IndexError:
        return ""


def _pp_process_file(input_path, filter_set, output_path, cfg, log_fn):
    magheggio    = cfg["magheggio_c_in_u"]
    output_lines = []
    distinct_old = set()
    distinct_new = set()
    try:
        with input_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                cols = line.split(";")
                agreement_id = cols[cfg["agreement_id_col"]] if cols else ""
                distinct_old.add(agreement_id)
                key = _pp_build_filter_key(cols, cfg)
                if key in filter_set:
                    if magheggio:
                        line = line.replace(";C;", ";U;")
                    output_lines.append(line)
                    distinct_new.add(agreement_id)
        if not output_lines:
            log_fn(f"[INFO] {input_path.name} — tutte le righe filtrate, saltata.", "info")
            return len(distinct_old), 0
        out_name   = output_path.name
        if magheggio:
            out_name = out_name.replace("_C_", "_U_")
        final_path = output_path.with_name(out_name)
        final_path.write_text("\n".join(output_lines), encoding="utf-8", newline="\n")
        log_fn(
            f"[OK] {input_path.name}  \u2192  "
            f"{len(distinct_old)} originali / {len(distinct_new)} mantenuti", "ok")
        return len(distinct_old), len(distinct_new)
    except Exception as e:
        log_fn(f"[ERRORE] {input_path.name}: {e}", "error")
        return 0, 0


def pp_run_pipeline(cfg_data, log_fn, on_done):
    try:
        import re as _re, shutil as _sh
        input_folder = Path(cfg_data["input_folder"]).resolve()
        out_sub      = cfg_data["output_subfolder"]
        out_path     = Path(out_sub)
        output_folder = out_path if out_path.is_absolute() else input_folder / out_sub
        zip_out_dir  = _HERE / "output" / "payment plans filter"
        zip_out_dir.mkdir(parents=True, exist_ok=True)
        zip_path     = zip_out_dir / cfg_data["zip_filename"]
        filter_file   = _PP_FILTER_FILES.get(cfg_data["filter_key"],
                                              _PP_FILTER_FILES["agreement_id"])

        if not input_folder.is_dir():
            log_fn(f"[ERRORE] Cartella input non trovata: {input_folder}", "error")
            on_done(success=False); return
        if not filter_file.is_file():
            log_fn(f"[ERRORE] File filtro non trovato: {filter_file}", "error")
            on_done(success=False); return

        if output_folder.exists():
            _sh.rmtree(output_folder)
        output_folder.mkdir(parents=True)
        log_fn(f"[INFO] Cartella output: {output_folder}", "info")

        filter_set = set()
        with filter_file.open("r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if s:
                    filter_set.add(s)
        log_fn(f"[INFO] Filtro caricato: {len(filter_set)} ID", "info")

        _PAT = _re.compile(r'^K[EG]_PP_[MCRU]_.*\.csv$', _re.IGNORECASE)
        csv_files = sorted(f for f in input_folder.glob("K[EG]_PP_*.csv")
                           if _PAT.match(f.name))
        if not csv_files:
            log_fn("[ERRORE] Nessun file CSV trovato.", "error")
            on_done(success=False); return

        log_fn(f"\n[INFO] File da elaborare: {len(csv_files)}", "info")
        total_old = total_new = 0
        interval  = int(cfg_data.get("progress_interval", 100))
        for i, csv_path in enumerate(csv_files, 1):
            old, new = _pp_process_file(
                csv_path, filter_set, output_folder / csv_path.name, cfg_data, log_fn)
            total_old += old
            total_new += new
            if i % interval == 0 or i == len(csv_files):
                log_fn(f"[INFO] Avanzamento: {i}/{len(csv_files)} file", "info")

        output_files = [f for f in output_folder.rglob("*") if f.is_file()]
        log_fn("\n\u2500\u2500 Riepilogo \u2500\u2500", "section")
        log_fn(f"[INFO] Input: {len(csv_files)}  |  Output: {len(output_files)}", "info")
        log_fn(f"[INFO] ID originali: {total_old}  |  mantenuti: {total_new}", "info")

        if output_files:
            import zipfile as _zf_pp
            log_fn(f"\n[INFO] ZIP: {zip_path.name} ...", "info")
            with _zf_pp.ZipFile(zip_path, "w", _zf_pp.ZIP_DEFLATED) as zf:
                for file in output_files:
                    zf.write(file, file.relative_to(output_folder))
            log_fn(f"[OK] ZIP creato: {zip_path}", "ok")
        else:
            log_fn("[WARN] Nessun file da comprimere.", "warn")

        log_fn("\n[INFO] Completato con successo.", "ok")
        on_done(success=True)
    except Exception as e:
        log_fn(f"\n[ERRORE CRITICO] {e}", "error")
        on_done(success=False)


class PaymentPlansFilter(_AppBase):

    def __init__(self, master):
        super().__init__(master, bg=BG)
        self._log_queue     = queue.Queue()
        self._running       = False
        self._filter_trees  = {}
        self._filter_counts = {}
        self._build_ui()
        self._load_fields()
        self._load_all_filters()
        self._poll_log()

    def _build_ui(self):
        self._status_var = tkinter.StringVar(value="Pronto.")
        Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, side="bottom")
        self._status_lbl = Label(self, textvariable=self._status_var, bg=BG, fg=TEXT_SEC,
                                  font=("Consolas", 9), anchor="w", pady=5)
        self._status_lbl.pack(fill="x", padx=24, side="bottom")
        self._build_notebook([
            ("▶  Pipeline",      self._build_pipeline_tab),
            ("🔍  Filtro",       self._build_filter_tab),
        ])

    # ── Tab Pipeline ──────────────────────────────────────────────────────

    def _build_pipeline_tab(self, parent):
        body = Frame(parent, bg=BG)
        body.pack(fill="both", expand=True)

        top = Frame(body, bg=BG_CARD, bd=0, highlightthickness=1,
                    highlightbackground=BORDER)
        top.pack(fill="x", pady=(0, 8))

        hdr = Frame(top, bg=BG_CARD)
        hdr.pack(fill="x")
        Label(hdr, text="ESECUZIONE", bg=BG_CARD, fg=TEXT_SEC,
              font=("Consolas", 9, "bold"), pady=10, padx=14).pack(side="left")

        def _icon_btn(symbol, command, color=ACCENT, tip=""):
            lbl = Label(hdr, text=symbol, bg=BG_CARD, fg=color,
                        font=("Consolas", 14), cursor="hand2", padx=10, pady=6)
            lbl.bind("<Button-1>", lambda e: command())
            lbl.bind("<Enter>",    lambda e: (lbl.configure(bg=BG_HOVER),
                                              self._status_var.set(tip) if tip else None))
            lbl.bind("<Leave>",    lambda e: (lbl.configure(bg=BG_CARD),
                                              self._status_var.set("Pronto.")))
            return lbl

        self._btn = _icon_btn("▶", self._start, ACCENT, "Avvia pipeline")
        self._btn.pack(side="right", padx=(0, 8))
        Frame(top, bg=BORDER, height=1).pack(fill="x", padx=14)

        row1 = Frame(top, bg=BG_CARD)
        row1.pack(fill="x", padx=14, pady=(8, 4))
        Label(row1, text="Cartella input:", bg=BG_CARD, fg=TEXT_SEC,
              font=("Consolas", 9), width=14, anchor="w").pack(side="left")
        browse_btn = Label(row1, text="\U0001f4c1", bg=BG_CARD, fg=TEXT_SEC,
                           font=("Consolas", 11), cursor="hand2", padx=4)
        browse_btn.pack(side="left")
        self._input_lbl = Label(row1, text="\u2014", bg=BG_CARD, fg=ACCENT,
                                font=("Consolas", 9), anchor="w")
        self._input_lbl.pack(side="left", fill="x", expand=True)

        def _browse_input(e=None):
            folder = filedialog.askdirectory(title="Seleziona cartella input")
            if folder:
                _write_env({"PP_INPUT_FOLDER": folder})
                self._update_input_label()

        browse_btn.bind("<Button-1>", _browse_input)
        self._input_lbl.bind("<Button-1>", _browse_input)

        row2 = Frame(top, bg=BG_CARD)
        row2.pack(fill="x", padx=14, pady=(0, 8))
        Label(row2, text="Chiave filtro:", bg=BG_CARD, fg=TEXT_SEC,
              font=("Consolas", 9), width=14, anchor="w").pack(side="left")
        self._fk_var = tkinter.StringVar()
        fk_btn = Frame(row2, bg=BG_INPUT, highlightthickness=1,
                       highlightbackground=BORDER, cursor="hand2")
        fk_btn.pack(side="left")
        fk_lbl = Label(fk_btn, textvariable=self._fk_var, bg=BG_INPUT, fg=TEXT_PRI,
                       font=("Consolas", 9), padx=10, pady=4, width=24, anchor="w")
        fk_lbl.pack(side="left")
        Label(fk_btn, text="\u25be", bg=BG_INPUT, fg=TEXT_SEC,
              font=("Consolas", 9), padx=6).pack(side="left")

        def _open_fk_menu(e=None):
            menu = tkinter.Menu(self, tearoff=0, bg=BG_CARD2, fg=TEXT_PRI,
                                activebackground=ACCENT2, activeforeground=TEXT_PRI,
                                font=("Consolas", 9), bd=0, relief="flat")
            for opt in _PP_FILTER_KEY_OPTIONS:
                menu.add_command(label=opt, command=lambda o=opt: (
                    self._fk_var.set(o),
                    _write_env({"PP_FILTER_KEY": _PP_FILTER_KEY_MAP.get(o, o)})))
            menu.post(fk_btn.winfo_rootx(),
                      fk_btn.winfo_rooty() + fk_btn.winfo_height())

        fk_btn.bind("<Button-1>", _open_fk_menu)
        fk_lbl.bind("<Button-1>", _open_fk_menu)

        # Magheccio
        row3 = Frame(top, bg=BG_CARD)
        row3.pack(fill="x", padx=14, pady=(0, 10))
        self._mag_var = tkinter.BooleanVar(
            value=_pp_get("PP_MAGHEGGIO").lower() == "true")
        self._mag_box = Label(row3,
                              text="☑" if self._mag_var.get() else "☐",
                              bg=BG_CARD,
                              fg=ACCENT if self._mag_var.get() else TEXT_SEC,
                              font=("Consolas", 12), cursor="hand2", width=2)
        self._mag_box.pack(side="left", padx=(0, 6))
        mag_lbl = Label(row3, text="Trasforma file  ;C;  →  ;U;",
                        bg=BG_CARD, fg=TEXT_PRI, font=("Consolas", 10),
                        cursor="hand2")
        mag_lbl.pack(side="left")

        def _toggle_mag(e=None):
            val = not self._mag_var.get()
            self._mag_var.set(val)
            self._mag_box.configure(text="☑" if val else "☐",
                                    fg=ACCENT if val else TEXT_SEC)
            _write_env({"PP_MAGHEGGIO": "true" if val else "false"})

        self._mag_box.bind("<Button-1>", _toggle_mag)
        mag_lbl.bind("<Button-1>", _toggle_mag)
        row3.bind("<Button-1>", _toggle_mag)

        log_frame = Frame(body, bg=BG_CARD, bd=0, highlightthickness=1,
                          highlightbackground=BORDER)
        log_frame.pack(fill="both", expand=True)
        self._build_log_panel(log_frame, on_clear=self._clear_log)

    # ── Tab Filtro ────────────────────────────────────────────────────────

    def _build_filter_tab(self, parent):
        style = ttk.Style()
        style.configure("PPFilter.Treeview",
                        background=BG_CARD, foreground=TEXT_PRI,
                        fieldbackground=BG_CARD, rowheight=26,
                        font=("Consolas", 10), borderwidth=0)
        style.configure("PPFilter.Treeview.Heading",
                        background=BG_CARD2, foreground=ACCENT,
                        font=("Consolas", 9, "bold"), relief="flat")
        style.map("PPFilter.Treeview",
                  background=[("selected", ACCENT2)],
                  foreground=[("selected", TEXT_PRI)])
        style.configure("PPSub.TNotebook",
                        background=BG, borderwidth=0, tabmargins=[0, 0, 0, 0])
        style.configure("PPSub.TNotebook.Tab",
                        background=BG_CARD, foreground=TEXT_SEC,
                        font=("Consolas", 9), padding=[12, 2], borderwidth=0)
        style.map("PPSub.TNotebook.Tab",
                  background=[("selected", ACCENT2), ("!selected", BG_CARD)],
                  foreground=[("selected", TEXT_PRI), ("!selected", TEXT_SEC)],
                  padding=[("selected", [12, 5]), ("!selected", [12, 2])])

        sub_nb = ttk.Notebook(parent, style="PPSub.TNotebook")
        sub_nb.pack(fill="both", expand=True)
        for internal_key, label in _PP_FILTER_LABELS.items():
            tab = Frame(sub_nb, bg=BG)
            sub_nb.add(tab, text=f"  {label}  ")
            self._build_filter_subtab(tab, internal_key, label)

    def _build_filter_subtab(self, parent, internal_key, label):
        hdr = Frame(parent, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(12, 0))
        Label(hdr, text=label, bg=BG, fg=TEXT_PRI,
              font=("Consolas", 11, "bold")).pack(side="left")
        Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(8, 0))
        Label(parent, text="Ogni riga rappresenta un ID da mantenere nel filtraggio.",
              bg=BG, fg=TEXT_SEC, font=("Consolas", 9), anchor="w",
              pady=6).pack(fill="x", padx=16)

        toolbar = Frame(parent, bg=BG)
        toolbar.pack(fill="x", padx=16, pady=(0, 6))
        self._make_btn(toolbar, "\u270f\ufe0f  Modifica / Aggiungi",
                       lambda ik=internal_key: self._filter_paste_popup(ik),
                       color=SUCCESS).pack(side="left", padx=(0, 6))
        self._make_btn(toolbar, "\U0001f5d1  Svuota righe",
                       lambda ik=internal_key: self._filter_clear_all(ik),
                       color=ERROR).pack(side="left")

        table_frame = Frame(parent, bg=BG_CARD,
                            highlightthickness=1, highlightbackground=BORDER)
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 4))

        tree = ttk.Treeview(table_frame, columns=("id",), show="headings",
                            style="PPFilter.Treeview", selectmode="browse")
        tree.heading("id", text="ID Filtro")
        tree.column("id", width=500, minwidth=200, anchor="w")
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview,
                            style="Dark.Vertical.TScrollbar")
        vsb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(fill="both", expand=True)
        self._filter_trees[internal_key] = tree

        count_var = tkinter.StringVar(value="")
        self._filter_counts[internal_key] = count_var
        Label(parent, textvariable=count_var, bg=BG, fg=TEXT_SEC,
              font=("Consolas", 9), anchor="w",
              pady=4).pack(fill="x", padx=16)

    # ── Tab Impostazioni ──────────────────────────────────────────────────

    # ── Filtro helpers ────────────────────────────────────────────────────

    def _load_all_filters(self):
        for key in _PP_FILTER_FILES:
            self._load_filter(key)

    def _load_filter(self, internal_key):
        tree      = self._filter_trees.get(internal_key)
        count_var = self._filter_counts.get(internal_key)
        if not tree:
            return
        for row in tree.get_children():
            tree.delete(row)
        filter_file = _PP_FILTER_FILES[internal_key]
        if not filter_file.exists():
            if count_var:
                count_var.set("File non trovato.")
            return
        lines = filter_file.read_text(encoding="utf-8").strip().splitlines()
        count = 0
        for line in lines:
            line = line.strip()
            if line:
                tree.insert("", "end", values=(line,))
                count += 1
        if count_var:
            count_var.set(f"{count} ID caricati.")

    def _filter_paste_popup(self, internal_key):
        import re as _re
        tree      = self._filter_trees[internal_key]
        count_var = self._filter_counts[internal_key]
        label     = _PP_FILTER_LABELS[internal_key]
        W, H = 500, 420
        popup = tkinter.Toplevel(self)
        popup.title(f"Modifica / Aggiungi \u2014 {label}")
        popup.configure(bg=BG)
        popup.resizable(False, False)
        popup.grab_set()
        popup.update_idletasks()
        x = (popup.winfo_screenwidth()  - W) // 2
        y = (popup.winfo_screenheight() - H) // 2
        popup.geometry(f"{W}x{H}+{x}+{y}")

        Label(popup, text=f"Modifica / Aggiungi \u2014 {label}",
              bg=BG, fg=TEXT_PRI, font=("Consolas", 11, "bold"), pady=12).pack()
        Label(popup, text="Un ID per riga. Righe vuote verranno ignorate.",
              bg=BG, fg=TEXT_SEC, font=("Consolas", 9), justify="center").pack()
        Frame(popup, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(8, 0))

        btn_row = Frame(popup, bg=BG)
        btn_row.pack(side="bottom", fill="x", padx=16, pady=12)
        tkinter.Button(btn_row, text="Annulla", bg=BG_CARD, fg=TEXT_SEC,
                       activebackground=BG_HOVER, activeforeground=TEXT_PRI,
                       font=("Consolas", 10, "bold"), relief="flat",
                       cursor="hand2", pady=6, padx=14, bd=0,
                       command=popup.destroy).pack(side="right", padx=(6, 0))
        btn_conferma = tkinter.Button(btn_row, text="\u2713  Conferma",
                                      bg=ACCENT, fg="#ffffff",
                                      activebackground="#3a7ee8",
                                      activeforeground="#ffffff",
                                      font=("Consolas", 10, "bold"),
                                      relief="flat", cursor="hand2",
                                      pady=6, padx=14, bd=0)
        btn_conferma.pack(side="right")

        feedback_var = tkinter.StringVar(value="")
        Label(popup, textvariable=feedback_var, bg=BG, fg=WARNING,
              font=("Consolas", 9), pady=4).pack(side="bottom", fill="x", padx=16)

        txt_frame = Frame(popup, bg=BG_CARD)
        txt_frame.pack(fill="both", expand=True, padx=16, pady=(8, 0))
        vsb = ttk.Scrollbar(txt_frame, style="Dark.Vertical.TScrollbar")
        vsb.pack(side="right", fill="y")
        txt = tkinter.Text(txt_frame, bg=BG_INPUT, fg=TEXT_PRI,
                           font=("Consolas", 10), relief="flat", bd=0,
                           insertbackground=TEXT_PRI, wrap="none",
                           padx=8, pady=6, yscrollcommand=vsb.set)
        txt.pack(fill="both", expand=True)
        vsb.config(command=txt.yview)
        txt.focus_set()

        existing = [tree.item(iid, "values")[0] for iid in tree.get_children()]
        if existing:
            txt.insert("1.0", "\n".join(existing))
        txt.tag_configure("invalid", foreground=WARNING, background="#2a1f00")

        def _is_valid_id(v):
            return bool(_re.fullmatch(r'\d+(\.\d+)*', v))

        def _on_conferma():
            raw = txt.get("1.0", "end").strip().splitlines()
            txt.tag_remove("invalid", "1.0", "end")
            valid, invalid = [], []
            for i, line in enumerate(raw):
                line = line.strip()
                if not line:
                    continue
                if internal_key == "supply_code_number":
                    parts = line.split(";")
                    ok = len(parts) == 2 and parts[1].startswith("A-")
                elif internal_key == "agreement_id":
                    ok = _is_valid_id(line)
                elif internal_key == "agreement_id_plan_type":
                    parts = line.split(";")
                    ok = (len(parts) == 2 and _is_valid_id(parts[0])
                          and parts[1] in ("M", "C", "R", "U"))
                else:
                    ok = True
                if ok:
                    valid.append(line)
                else:
                    invalid.append(i + 1)
                    txt.tag_add("invalid", f"{i+1}.0", f"{i+1}.end")

            if invalid:
                msgs = {
                    "supply_code_number":     "formato atteso: prm;A-xxxxxxxx",
                    "agreement_id":           "solo numeri (es. 12345 o 12345.6)",
                    "agreement_id_plan_type": "formato atteso: numero;M|C|R|U",
                }
                feedback_var.set(
                    f"\u26a0  {len(invalid)} riga/e non valida/e \u2014 "
                    f"{msgs.get(internal_key, '')}")
                return
            if not valid:
                feedback_var.set("\u26a0  Nessun ID trovato.")
                return
            tree.delete(*tree.get_children())
            for v in valid:
                tree.insert("", "end", values=(v,))
            count_var.set(f"{len(valid)} ID.")
            self._save_filter(internal_key)
            popup.destroy()

        btn_conferma.config(command=_on_conferma)

    def _filter_clear_all(self, internal_key):
        tree      = self._filter_trees[internal_key]
        count_var = self._filter_counts[internal_key]
        if not tree.get_children():
            return
        if messagebox.askyesno("Svuota filtro", "Rimuovere tutti gli ID?"):
            tree.delete(*tree.get_children())
            count_var.set("0 ID.")
            self._save_filter(internal_key)

    def _save_filter(self, internal_key):
        tree        = self._filter_trees[internal_key]
        filter_file = _PP_FILTER_FILES[internal_key]
        rows = [tree.item(iid, "values")[0] for iid in tree.get_children()
                if tree.item(iid, "values")]
        try:
            filter_file.parent.mkdir(parents=True, exist_ok=True)
            filter_file.write_text(("\n".join(rows) + "\n") if rows else "",
                                   encoding="utf-8")
            self._status_var.set(
                f"\u2713 {filter_file.name} salvato ({len(rows)} ID).")
        except Exception as e:
            messagebox.showerror("Errore salvataggio filtro", str(e))

    # ── Fields / config ───────────────────────────────────────────────────

    def _load_fields(self):
        fk = _pp_get("PP_FILTER_KEY") or "agreement_id"
        self._fk_var.set(_PP_FILTER_KEY_MAP_INV.get(fk, "Agreement ID"))
        self._update_input_label()

    def _update_input_label(self):
        val = _pp_get("PP_INPUT_FOLDER").strip()
        if val and len(val) > 55:
            display = "…" + val[-52:]
        else:
            display = val if val else "—"
        self._input_lbl.configure(text=display,
                                  fg=ACCENT if val else TEXT_SEC)

    # ── Pipeline ─────────────────────────────────────────────────────────

    def _on_done(self, success):
        self._running = False
        color = SUCCESS if success else ERROR
        self._status_var.set(
            "\u2713 Completato con successo." if success else "\u2717 Terminato con errori.")
        self._btn.configure(fg=color, cursor="hand2")
        self.after(3000, lambda: self._btn.configure(fg=ACCENT))

    def _start(self):
        if self._running:
            return
        env = _read_env_raw()
        input_folder = env.get("PP_INPUT_FOLDER", "").strip()
        if not input_folder:
            messagebox.showwarning(
                "Input mancante", "Seleziona la cartella di input prima di avviare.")
            return
        self._running = True
        self._btn.configure(fg=TEXT_SEC, cursor="arrow")
        self._status_var.set("In esecuzione...")
        cfg = {
            "input_folder":      input_folder,
            "output_subfolder":  env.get("PP_OUTPUT_SUBFOLDER", "output"),
            "zip_filename":      env.get("PP_ZIP_FILENAME", "plan.zip"),
            "magheggio_c_in_u":  env.get("PP_MAGHEGGIO", "false").lower() == "true",
            "progress_interval": int(env.get("PP_PROGRESS_INTERVAL", "100")),
            "agreement_id_col":  int(env.get("PP_AGREEMENT_ID_COL", "0")),
            "number_col":        int(env.get("PP_NUMBER_COL", "4")),
            "supply_code_col":   int(env.get("PP_SUPPLY_CODE_COL", "3")),
            "plan_type_id_col":  int(env.get("PP_PLAN_TYPE_ID_COL", "11")),
            "filter_key":        env.get("PP_FILTER_KEY", "agreement_id"),
        }
        threading.Thread(
            target=pp_run_pipeline,
            args=(cfg, self._enqueue_log, self._on_done),
            daemon=True,
        ).start()



# ════════════════════════════════════════════════════════════════════════════
# CSV BLANK HEADER REMOVER
# ════════════════════════════════════════════════════════════════════════════

_CBR_TXT    = _HERE / "input"  / "csv blank header remover" / "files.txt"
_CBR_OUTPUT = _HERE / "output" / "csv blank header remover"
_CBR_CHUNK  = 64 * 1024 * 1024  # 64 MB
_CBR_EXT    = {".csv", ".txt"}


def csv_blank_header_run_pipeline(file_paths, log, on_done):
    try:
        _CBR_OUTPUT.mkdir(parents=True, exist_ok=True)
        log(f"[INFO] Output: {_CBR_OUTPUT}", "info")

        if not file_paths:
            log("[ERRORE] Nessun file da processare.", "error")
            on_done(success=False); return

        log(f"[INFO] File da processare: {len(file_paths)}", "info")
        ok = skip = err = 0

        for file_path in file_paths:
            src = Path(file_path)
            if src.suffix.lower() not in _CBR_EXT:
                log(f"[SKIP] {src.name} — estensione non supportata", "warn")
                skip += 1; continue
            if not src.exists():
                log(f"[SKIP] {src.name} — file non trovato", "warn")
                skip += 1; continue
            dst = _CBR_OUTPUT / f"{src.stem}_no_head{src.suffix}"
            try:
                with open(src, "rb") as f_in:
                    first = f_in.readline()
                    if first.strip(b"\r\n") != b"":
                        log(f"[SKIP] {src.name} — prima riga non vuota", "warn")
                        skip += 1; continue
                    with open(dst, "wb") as f_out:
                        while True:
                            chunk = f_in.read(_CBR_CHUNK)
                            if not chunk: break
                            f_out.write(chunk)
                log(f"[OK] {src.name}  \u2192  {dst.name}", "ok")
                ok += 1
            except Exception as e:
                log(f"[ERRORE] {src.name} \u2014 {e}", "error")
                err += 1

        log("\n\u2500\u2500 Riepilogo \u2500\u2500", "section")
        log(f"[INFO] Completati: {ok}  |  Saltati: {skip}  |  Errori: {err}", "info")
        log("\n[INFO] Fatto!", "ok")
        on_done(success=err == 0)
    except Exception as e:
        log(f"\n[ERRORE CRITICO] {e}", "error")
        on_done(success=False)



# ════════════════════════════════════════════════════════════════════════════
# INVOICE WRITER — logica integrata (ex invoice_writer.py, ora inline)
# Replica il flusso Java InvoiceService. Codice di business invariato.
# ════════════════════════════════════════════════════════════════════════════

"""
Invoice Flow Script
===================
Replica il flusso Java InvoiceService per ambiente di test.
Integrato in HUB Tool - All-in-one come app "Invoice Writer".

Step eseguiti:
  1. Lettura invoice direttamente da Kraken, filtrate per una lista di
     document identifier fornita dall'utente (stesso meccanismo di
     Kraken Data Extractor in modalità "by identifier": query
     query_invoice_elec.sql / query_invoice_gas.sql recuperate da
     hub_config_query_kraken con placeholder LISTA_IDENTIFIER)
  2. Mapping righe -> InputInvoice
  3. Mapping InputInvoice -> Invoice (con addVarsJsonValues)
  4. Validazione invoice (evaluateInvoice):
     - controllo soglia rounding
     - risoluzione SAP Plan ID / Agreement ID da CSV (opzionale)
  5. Invoice KO salvate in stg_invoice_waiting_check o kraken_scraps su DB HUB
  6. Generazione CSV SAP in ./output/invoice writer/

Le credenziali HUB e Kraken sono quelle già configurate nel tool
(config/.env, chiavi HUB_* e KRAKEN_*) — nessuna configurazione separata.

Lista identifier (input):
  input/invoice writer/data_input.csv
  Colonne: IDENTIFIER;IMPORT_SUPPLIER_BILL_ID;AGREEMENT_ID
"""

import os
import sys
import csv
import json
import uuid
import logging
from contextlib import contextmanager
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from pathlib import Path

from dotenv import load_dotenv

# =============================================================================
# SETUP LOGGING
# =============================================================================
_script_dir_early = Path(__file__).parent
_error_dir_early  = _script_dir_early / "error" / "invoice writer"
_error_dir_early.mkdir(parents=True, exist_ok=True)
_log_file = _error_dir_early / f"errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


class _LazyFileHandler(logging.Handler):
    """Crea il file di log solo al primo record WARNING o superiore."""
    def __init__(self, path, encoding="utf-8"):
        super().__init__(logging.WARNING)
        self._path = path
        self._encoding = encoding
        self._handler = None
        self.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

    def emit(self, record):
        if self._handler is None:
            self._handler = logging.FileHandler(self._path, encoding=self._encoding)
            self._handler.setFormatter(self.formatter)
        self._handler.emit(record)

    def close(self):
        if self._handler:
            self._handler.close()
        super().close()


_file_handler = _LazyFileHandler(_log_file)

log = logging.getLogger("invoice_writer")
log.setLevel(logging.INFO)
log.propagate = False
if not log.handlers:
    _stream_handler = logging.StreamHandler(sys.stdout)
    _stream_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    log.addHandler(_stream_handler)
    log.addHandler(_file_handler)

# =============================================================================
# CARICO .ENV
# =============================================================================
script_dir = Path(__file__).parent
load_dotenv(script_dir / "config" / ".env")

COMMODITY = "ELEC"  # impostato dinamicamente in run_for_commodity()

# Nota: le connessioni HUB e Kraken riusano get_hub_connection() e
# get_kraken_connection() già definite più in alto nel file (stesse
# credenziali di HUB Prod Sync e Kraken Data Extractor).

B2C_ABS_ROUNDING = Decimal(os.getenv("B2C_ABS_ROUNDING", "0.05"))

_IW_INPUT_DIR  = script_dir / "input"  / "invoice writer"
_IW_OUTPUT_DIR = script_dir / "output" / "invoice writer"
_IW_ERROR_DIR  = script_dir / "error"  / "invoice writer"

OUTPUT_DIR = _IW_OUTPUT_DIR
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ERROR_DIR = _IW_ERROR_DIR
ERROR_DIR.mkdir(parents=True, exist_ok=True)
_IW_INPUT_DIR.mkdir(parents=True, exist_ok=True)

BATCH_UUID = str(uuid.uuid4())

# =============================================================================
# COSTANTI
# =============================================================================

def COMMODITY_SAP_CODE() -> str:
    return "01" if COMMODITY == "ELEC" else "02"

def COMMODITY_SHORT() -> str:
    return "E" if COMMODITY == "ELEC" else "G"

# InvoiceSapVatCode mapping (replica Java enum)
VAT_CODE_MAP = {
    "TG":           "VAT_TG",
    "CC":           "VAT_TN",
    "CG":           "VAT_TN",
    "ENI":          "VAT_TN",
    "PFCS":         "VAT_TN",
    "CONSUMPTION":  "VAT_B9",
    "CTA":          "VAT_TA",
    "ENEDIS":       "VAT_DD",
    "TICFE":        "VAT_DD",
    "PVCS":         "VAT_DS",
    "SUBSCRIPTION": "VAT_B2",
    "ABONNEMENT":   "VAT_B2",
    "PCK_HOME_P":   "VAT_CF",
    "SAXA_G3ANS":   "VAT_CF",
    "TICGN":        "VAT_TE",
    "TSCA":         "VAT_CF",
    "VAT_20":       "VAT_20",
    "VAT_5_5":      "VAT_5.5",
    "VAT_0":        "VAT_0",
}

# Componenti che forzano codice VAT_B9
PCK_B9_COMPONENTS = {
    "PCK_PRO3_+", "PCK_PRO5_+", "PCK_PRO2_+", "PCK_PRO4_+",
    "PCK_PROTEC", "PCK_PROT_+", "VPPCKPROT+",
}

# Campi da escludere nella serializzazione CSV (replica Java getObjectAttributeValues)
CSV_SKIP_FIELDS = {"fileName", "createdBy", "paymentScheduleId", "firstTransactionId", "creditId"}

# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class InputInvoice:
    template_vars_json: str = ""
    number: str = ""
    account_type: str = ""
    ledger_type: str = ""
    prm: str = ""          # contiene sia PRM (ELEC) che PCE (GAS)
    identifier: str = ""
    finalized_at: str = ""
    document_type: str = ""
    issued_by_id: str = ""
    original_statement_identifier: str = ""
    payment_at: str = ""
    is_monthly_billing: bool = False
    template_code: str = ""
    last_payment_schedule_id: str = ""
    comodity: str = ""
    uuid: str = ""
    kraken_version: str = "V1"


@dataclass
class Invoice:
    vars_json: str = ""
    number: str = ""
    account_type: str = ""
    ledger_type: str = ""
    prm: str = ""
    identifier: str = ""
    finalized_at: str = ""
    document_type: str = ""
    issued_by_id: str = ""
    original_statement_identifier: str = ""
    payment_at: str = ""
    is_monthly_billing: bool = False
    template_code: str = ""
    last_payment_schedule_id: str = ""
    comodity: str = ""
    reconciliation_status: str = "NR"
    hub_updated_at: str = ""
    kraken_version: str = "V1"
    # Campi aggiunti da addVarsJsonValues
    invoice_amount: str = ""
    to_be_paid_amount: str = ""
    payment_amount_rb: str = ""
    vat_json_components: str = ""
    turpe_json_components: str = ""
    template_split_json: str = ""
    is_negative: bool = False
    # Campi settati da evaluateInvoice
    sap_plan_id: str = ""
    agreement_id: str = ""


@dataclass
class AccountDetailRow:
    """Riga generica CSV SAP (PCLI/PRIC/PTAX/ACC)"""
    reference: str = ""
    value_date: str = ""
    record_type: str = ""
    counter: int = 0
    document_type: str = ""
    template_code: str = ""
    component_detail: str = ""
    movement_type: str = ""
    expiration_date: str = ""
    point_of_delivery: str = ""
    kraken_account: str = ""
    commodity: str = ""
    characteristic_of_accounts: str = ""
    amount: str = ""
    original_statement_identifier: str = ""
    contract_end_date: str = ""
    sap_plan_id: str = ""
    agreement_id: str = ""
    segment: str = "RESIDENT"


@dataclass
class InvoiceTemplate:
    pcli: List[AccountDetailRow] = field(default_factory=list)
    pric: List[AccountDetailRow] = field(default_factory=list)
    ptax: List[AccountDetailRow] = field(default_factory=list)
    acc: List[AccountDetailRow] = field(default_factory=list)


# =============================================================================
# DB HELPERS
# =============================================================================
# Nota: Invoice Writer riusa get_hub_connection() e get_kraken_connection()
# già definite più in alto nel file (stesse credenziali di HUB Prod Sync e
# Kraken Data Extractor — nessuna configurazione separata).



# =============================================================================
# STEP 1: LETTURA INVOICE DA KRAKEN VIA LISTA IDENTIFIER
# (stesso meccanismo di Kraken Data Extractor — modalità "by identifier":
#  query_invoice_elec.sql / query_invoice_gas.sql recuperate da
#  hub_config_query_kraken ed eseguite su Kraken con placeholder LISTA_IDENTIFIER)
# =============================================================================

_IW_INPUT_FILE = _IW_INPUT_DIR / "data_input.csv"

_IW_FLOW_BY_COMMODITY = {
    "ELEC": "query_invoice_elec.sql",
    "GAS":  "query_invoice_gas.sql",
}


def iw_load_identifier_data() -> tuple:
    """
    Legge data_input.csv (IDENTIFIER;IMPORT_SUPPLIER_BILL_ID;AGREEMENT_ID).
    Ritorna (lista_identifier_sql, plan_map) dove:
      - lista_identifier_sql: stringa SQL IN (...) con tutti gli identifier
      - plan_map: dict {identifier: (sap_plan_id, agreement_id)}
    """
    if not _IW_INPUT_FILE.exists():
        raise FileNotFoundError(
            f"File input non trovato: {_IW_INPUT_FILE}")

    plan_map: Dict[str, tuple] = {}
    with open(_IW_INPUT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            identifier = row.get("IDENTIFIER", "").strip()
            if not identifier:
                continue
            if not identifier.upper().startswith(("EB", "GB")):
                log.warning("Identifier ignorato (prefisso non valido): %s", identifier)
                continue
            sap_plan_id = row.get("IMPORT_SUPPLIER_BILL_ID", "").strip()
            agreement_id = row.get("AGREEMENT_ID", "").strip()
            plan_map[identifier] = (sap_plan_id, agreement_id)

    if not plan_map:
        raise ValueError("Nessun identifier valido trovato nel file di input.")

    lista = ", ".join(f"'{i}'" for i in plan_map)
    return lista, plan_map


def _iw_jsonify(value):
    """Converte un eventuale dict/list (jsonb auto-deserializzato da psycopg2) in stringa JSON."""
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return value


def fetch_invoices_from_kraken(commodity: str, lista_identifier: str,
                               hub_conn, kraken_conn) -> List[Dict]:
    """
    Legge le invoice direttamente da Kraken usando la stessa query
    (query_invoice_elec.sql / query_invoice_gas.sql) e lo stesso meccanismo
    a placeholder LISTA_IDENTIFIER già usato da Kraken Data Extractor in
    modalità "by identifier" — qui eseguita ed usata direttamente senza
    passare per la tabella di staging Integration/Recette.
    """
    flow = _IW_FLOW_BY_COMMODITY[commodity]
    query = load_query_from_hub_identifier(hub_conn, flow, lista_identifier)
    if query is None:
        raise RuntimeError(
            f"Query '{flow}' non trovata in hub_config_query_kraken.")

    cur = kraken_conn.cursor()
    try:
        cur.execute(query)
    except Exception:
        cur.close()
        kraken_conn.rollback()
        raise
    columns = [d[0] for d in cur.description]
    raw_rows = cur.fetchall()
    cur.close()

    rows: List[Dict] = []
    for raw in raw_rows:
        row = {}
        for col, val in zip(columns, raw):
            if val is None:
                row[col] = ""
            elif col == "template_vars_json":
                row[col] = _iw_jsonify(val)
            else:
                row[col] = val
        rows.append(row)
    return rows


# =============================================================================
# STEP 2: riga CSV -> InputInvoice
# =============================================================================

def get_string(row: Dict, col: str) -> str:
    """Restituisce il valore stringa di una colonna, oppure stringa vuota."""
    val = row.get(col)
    return str(val).strip() if val is not None else ""


def get_boolean(row: Dict, col: str) -> bool:
    val = row.get(col)
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    return str(val).lower() in ("true", "t", "1", "yes")


def get_kraken_version(template_vars_json: str, finalized_at: str, identifier: str,
                       version_map: Dict[str, str]) -> str:
    """
    Replica la logica Java getKrakenVersion():
    - Se identifier è nella mappa -> usa versione mappata
    - Se finalized_at >= 2025-08-01 -> V3
    - Se JSON ha details.vat con chiavi numeriche -> V2
    - Altrimenti -> V1
    """
    if identifier in version_map:
        return version_map[identifier]

    if is_v3_triggered(finalized_at):
        return "V3"

    try:
        obj = json.loads(template_vars_json)
        details = obj.get("details", {})
        vat = details.get("vat", {})
        if isinstance(vat, dict):
            for key in vat:
                # chiave numerica tipo "20.00000" o "5" -> V2
                try:
                    float(key)
                    return "V2"
                except ValueError:
                    pass
    except Exception:
        pass

    return "V1"


def is_v3_triggered(finalized_at: str) -> bool:
    """Restituisce True se finalized_at >= 2025-08-01."""
    try:
        date_part = finalized_at.split(" ")[0].split("+")[0].strip()
        dt = datetime.strptime(date_part, "%Y-%m-%d")
        return dt >= datetime(2025, 8, 1)
    except Exception:
        return False


def result_set_to_input_invoice(row: Dict, batch_uuid: str, version_map: Dict[str, str]) -> Optional[InputInvoice]:
    """
    Replica Java getInputRecordToLog().
    `row` ora proviene da una riga del CSV di input (stesse colonne che prima
    arrivavano dal ResultSet della query Kraken).
    Restituisce None se prm/pce mancante (va in scraps).
    """
    inv = InputInvoice()

    # PRM per ELEC, PCE per GAS
    pod_col = "prm" if COMMODITY == "ELEC" else "pce"
    pod = get_string(row, pod_col)
    if not pod:
        log.warning("PRM/PCE mancante per number=%s - record scartato", get_string(row, "number"))
        return None

    inv.template_vars_json = get_string(row, "template_vars_json")
    inv.number = get_string(row, "number")
    inv.account_type = get_string(row, "account_type")
    inv.ledger_type = get_string(row, "ledger_type")
    inv.prm = pod
    inv.identifier = get_string(row, "identifier")
    inv.finalized_at = get_string(row, "finalized_at")
    inv.document_type = get_string(row, "document_type")
    inv.issued_by_id = get_string(row, "issued_by_id")
    inv.original_statement_identifier = get_string(row, "original_statement_identifier")
    inv.payment_at = get_string(row, "payment_at")
    inv.is_monthly_billing = get_boolean(row, "is_monthly_billing")
    inv.template_code = get_string(row, "template_code")
    inv.last_payment_schedule_id = get_string(row, "last_payment_schedule_id")
    inv.comodity = COMMODITY
    inv.uuid = batch_uuid
    inv.kraken_version = get_kraken_version(
        inv.template_vars_json, inv.finalized_at, inv.identifier, version_map
    )
    return inv


# =============================================================================
# STEP 3: InputInvoice -> Invoice + addVarsJsonValues
# =============================================================================

def input_invoice_to_invoice(inp: InputInvoice) -> Invoice:
    """Replica Java getInvoice()."""
    inv = Invoice()
    inv.vars_json = inp.template_vars_json
    inv.number = inp.number
    inv.account_type = inp.account_type
    inv.ledger_type = inp.ledger_type
    inv.prm = inp.prm
    inv.identifier = inp.identifier
    inv.finalized_at = inp.finalized_at
    inv.document_type = inp.document_type
    inv.issued_by_id = inp.issued_by_id
    inv.original_statement_identifier = inp.original_statement_identifier
    inv.payment_at = inp.payment_at
    inv.is_monthly_billing = inp.is_monthly_billing
    inv.template_code = inp.template_code
    inv.last_payment_schedule_id = inp.last_payment_schedule_id
    inv.comodity = COMMODITY
    inv.reconciliation_status = "NR"
    inv.hub_updated_at = datetime.now().isoformat()
    inv.kraken_version = inp.kraken_version
    return inv


PACK_MAP = {
    "Pack Protection + (3,99€/mois) - 6 mois":             "PCK_PRO3_+",
    "Pack Home P + (4,58€/mois)":                           "PCK_HOME_P",
    "Pack Protection + (3,99€/mois) - 3 mois offerts":     "PCK_PRO5_+",
    "Pack Protection + (3,99€/mois)":                       "PCK_PRO2_+",
    "Pack Protection + (1€ /mois)":                         "PCK_PRO4_+",
    "Pack Protection (2,99€/mois)":                         "PCK_PROTEC",
    "Pack Protection (3,99€/mois)":                         "PCK_PROT_+",
    "Assurance AXA avec période de gratuité de 3 ans":      "SAXA_G3ANS",
    "Pack protection + 10€ TTC/mois OFFERT":                "VPPCKPROT+",
}

TURPE_COMPONENT_MAP = {
    "turpe_counting":    "CC",
    "turpe_cs":          None,   # PVCS (variable) o PFCS (fixed)
    "turpe_management":  "CG",
}


def _comp(name: str, amount: str, vat_rate: str = "") -> dict:
    return {"componentName": name, "amount": amount, "vatRate": vat_rate}


def _apply_sign(amount: Decimal, gross: Decimal) -> Decimal:
    """Replica Java switch(signum): PRIC e PTAX cambiano segno in base al segno del PCLI."""
    if gross > 0:
        return -amount
    if gross < 0:
        return abs(amount)
    return amount


def _get_display_name(details: dict) -> Optional[str]:
    addons = details.get("addons", [])
    if addons:
        return addons[0].get("band", None)
    return None


def _extract_turpe_v1(sumup: dict) -> Dict[str, dict]:
    """
    Replica Java SapInvoiceMapperUtils.extractAndSaveTurpeComponents().
    Restituisce {component_name: {gross_amount, net_amount, vat_amount, vat_rate}}.
    """
    turpe_map = {}
    for section, is_variable in [("turpe_fixed_components", False), ("turpe_variable_components", True)]:
        components = sumup.get(section, {})
        for key, values in components.items():
            if key == "turpe_cs":
                sap_name = "PVCS" if is_variable else "PFCS"
            elif key == "turpe_counting":
                sap_name = "CC"
            elif key == "turpe_management":
                sap_name = "CG"
            else:
                sap_name = key.upper()
            turpe_map[sap_name] = {
                "gross_amount": str(values.get("gross_amount", "0")),
                "net_amount":   str(values.get("net_amount", "0")),
                "vat_amount":   str(values.get("vat_amount", "0")),
                "vat_rate":     str(values.get("vat_rate", "")),
            }
    return turpe_map


def build_template_split_json_v1(vars_json: str, template_code: str) -> str:
    """
    Replica Java InvoiceJsonManager.getInvoiceAccountDetailFromJson() (V1).
    Costruisce il template_split_json con PCLI, PRIC, PTAX, ACC, ROUND.
    """
    obj       = json.loads(vars_json)
    sumup     = obj["sumup"]
    details   = obj.get("details", {})

    is_intermediate = "INTERMEDIATE" in template_code.upper()
    is_final        = "FINAL" in template_code.upper()

    sumup_gross = Decimal(str(sumup["gross_amount"]))
    acc_amount  = str(sumup["paid_amount"]) if (is_final or is_intermediate) else ""

    has_addon    = bool(obj.get("has_addons")) and not obj.get("has_addons") is None
    display_name = _get_display_name(details) if has_addon else ""
    if display_name is None:
        display_name = ""
    # mappa display_name -> pack code se necessario
    display_name = PACK_MAP.get(display_name, display_name)

    turpe_map = _extract_turpe_v1(sumup)

    # ---- VAT map (details.vat) ----
    vat_obj = details.get("vat", {})
    # {vat_key: [{period_start_at, rate, value_taxed, amount, value_vat_included, taxed_item, ...}]}
    vat_map: Dict[str, list] = {}
    for prop_name, vat_array in vat_obj.items():
        entries = []
        for el in vat_array:
            entry = {k: el.get(k, "") for k in
                     ("period_start_at", "period_end_at", "tax_type", "rate",
                      "value_taxed", "amount", "value_vat_included", "vat_rate", "taxed_item", "reversed_charge")}
            taxed_item = entry["taxed_item"]
            if taxed_item.lower() == "addon":
                entry["taxed_item"] = display_name
            entries.append(entry)
        new_key = entries[0]["taxed_item"] if prop_name.lower() == "addon" and entries else prop_name
        vat_map[new_key] = entries

    pcli_list: list = []
    pric_list: list = []
    ptax_list: list = []
    total_gross_pcli = Decimal("0")
    total_gross_pric = Decimal("0")
    total_gross_ptax = Decimal("0")

    for comp_name, entries in vat_map.items():
        dto = entries[0]
        comp_upper = comp_name.upper()
        vat_rate = dto.get("rate", "")

        # Turpe amounts to subtract
        turpe_pcli = Decimal("0")
        turpe_pric = Decimal("0")
        turpe_ptax = Decimal("0")

        if comp_upper == "SUBSCRIPTION":
            for t_name, t_val in turpe_map.items():
                if str(t_val["vat_rate"]).startswith("5.5"):
                    turpe_pcli += Decimal(t_val["gross_amount"])
                    turpe_pric += Decimal(t_val["net_amount"])
                    turpe_ptax += Decimal(t_val["vat_amount"])
        elif comp_upper == "CONSUMPTION":
            for t_name, t_val in turpe_map.items():
                if str(t_val["vat_rate"]).startswith("20"):
                    turpe_pcli += Decimal(t_val["gross_amount"])
                    turpe_pric += Decimal(t_val["net_amount"])
                    turpe_ptax += Decimal(t_val["vat_amount"])

        amount_pcli = Decimal(str(dto["value_vat_included"])) - turpe_pcli
        amount_pric = Decimal(str(dto["value_taxed"]))         - turpe_pric
        amount_ptax = Decimal(str(dto["amount"]))              - turpe_ptax

        # Signum check
        amount_pric = _apply_sign(amount_pric, amount_pcli)
        amount_ptax = _apply_sign(amount_ptax, amount_pcli)

        total_gross_pcli += amount_pcli
        total_gross_pric += amount_pric
        total_gross_ptax += amount_ptax

        pcli_list.append(_comp(comp_upper, str(amount_pcli), vat_rate))
        pric_list.append(_comp(comp_upper, str(amount_pric), vat_rate))
        ptax_list.append(_comp(comp_upper, str(amount_ptax), vat_rate))

    # Turpe components (CC, CG, PFCS, PVCS, ...)
    for t_name, t_val in turpe_map.items():
        t_pcli = Decimal(t_val["gross_amount"])
        t_pric = Decimal(t_val["net_amount"])
        t_ptax = Decimal(t_val["vat_amount"])
        vat_rate = t_val["vat_rate"]

        t_pric = _apply_sign(t_pric, t_pcli)
        t_ptax = _apply_sign(t_ptax, t_pcli)

        total_gross_pcli += t_pcli
        total_gross_pric += t_pric
        total_gross_ptax += t_ptax

        pcli_list.append(_comp(t_name, str(t_pcli), vat_rate))
        pric_list.append(_comp(t_name, str(t_pric), vat_rate))
        ptax_list.append(_comp(t_name, str(t_ptax), vat_rate))

    # ROUND
    round_pcli = sumup_gross - total_gross_pcli
    gross_with_round = total_gross_pcli + round_pcli
    round_pric = (gross_with_round + total_gross_pric + total_gross_ptax) * Decimal("-1")

    round_list = [
        _comp("ROUND", str(round_pcli), ""),
        _comp("ROUND", str(round_pric), ""),
    ]

    # VAT_TG se ROUND != 0
    if round_pcli != 0:
        ptax_list.append(_comp("TG", "-0.00", "0.00"))

    result = {
        "PCLI":  pcli_list,
        "PRIC":  pric_list,
        "PTAX":  ptax_list,
        "ACC":   {"componentName": "ACC", "amount": acc_amount, "vatRate": ""},
        "ROUND": round_list,
    }
    return json.dumps(result)


def _extract_turpe_v2(sumup: dict) -> Dict[str, dict]:
    """
    Replica SapInvoiceMapperUtils.extractAndSaveTurpeComponentsV2().
    Nomi componenti: CC_N, CG_N, PFCS_N, PVCS_N.
    Struttura values identica a V1 (oggetto con net_amount, vat_rate, ...).
    """
    turpe_map = {}
    for section, is_variable in [("turpe_fixed_components", False), ("turpe_variable_components", True)]:
        components = sumup.get(section, {})
        for key, values in components.items():
            if key == "turpe_cs":
                sap_name = "PVCS_N" if is_variable else "PFCS_N"
            elif key == "turpe_counting":
                sap_name = "CC_N"
            elif key == "turpe_management":
                sap_name = "CG_N"
            else:
                sap_name = key.upper() + "_N"
            turpe_map[sap_name] = {
                "net_amount": str(values.get("net_amount", "0")),
                "vat_rate":   str(values.get("vat_rate", "")),
            }
    return turpe_map


def _extract_turpe_v3(sumup: dict) -> Dict[str, dict]:
    """
    Replica SapInvoiceMapperUtils.extractAndSaveTurpeComponentsV3().
    Struttura diversa: turpe_fixed/variable_components ha {key: {vat_20: value, vat_5.5: value}}.
    Nomi: fixed vat_20 -> CC_V3/CG_V3/PFCS_V3; fixed vat_5.5 -> CC_N/CG_N/PFCS_N;
          variable vat_5.5 -> PVCS_V3 (nota: nel Java è _V3 per vat_5.5 variable).
    """
    turpe_map = {}
    for section, is_variable in [("turpe_fixed_components", False), ("turpe_variable_components", True)]:
        components = sumup.get(section, {})
        for key, vat_dict in components.items():
            if not isinstance(vat_dict, dict):
                continue
            if key == "turpe_cs":
                base_name = "PVCS_N" if is_variable else "PFCS_N"
            elif key == "turpe_counting":
                base_name = "CC_N"
            elif key == "turpe_management":
                base_name = "CG_N"
            else:
                base_name = key.upper() + "_N"

            for vat_key, value in vat_dict.items():
                if value is None:
                    continue
                vat_rate = vat_key[4:] if vat_key.startswith("vat_") else vat_key  # "vat_20" -> "20"
                # fixed: vat_20 -> _V3 suffix; variable: vat_5.5 -> _V3 suffix
                if (not is_variable and vat_key == "vat_20") or (is_variable and vat_key == "vat_5.5"):
                    comp_name = base_name.replace("_N", "_V3")
                else:
                    comp_name = base_name
                turpe_map[comp_name] = {
                    "net_amount": str(value),
                    "vat_rate":   vat_rate,
                }
    return turpe_map


def _apply_sign_v2(amount: Decimal, gross_ref: Decimal) -> Decimal:
    """Stesso signum di V1 ma basato su gross_ref (grossAmount20 o grossAmount5_5)."""
    if gross_ref > 0:
        return -amount
    if gross_ref < 0:
        return abs(amount)
    return amount


def _add_vat0_to_round(round_list: list, amount: Decimal):
    """Replica Java addVat0ToPCLI(): ROUND[0] accumula VAT_0."""
    if not round_list:
        round_list.append(_comp("VAT_0", str(amount), ""))
    else:
        existing = Decimal(str(round_list[0]["amount"]))
        round_list[0]["amount"] = str(existing + amount)


def build_template_split_json_v2(vars_json: str, template_code: str) -> str:
    """
    Replica Java InvoiceJsonManager.getInvoiceAccountDetailFromJsonV2().
    PCLI: VAT_20 e VAT_5.5 (amount + value_taxed).
    PTAX: VAT_20 e VAT_5_5 (amount negato secondo signum).
    PRIC: CONSUMPTION_N, SUBSCRIPTION_N, CTA_N, TICFE_N o TICGN_N, turpe, addon.
    ROUND: VAT_0 (PCLI) + ROUND_N (PRIC).
    """
    obj      = json.loads(vars_json)
    sumup    = obj["sumup"]
    details  = obj.get("details", {})
    is_gas   = COMMODITY == "GAS"

    is_intermediate = "INTERMEDIATE" in template_code.upper()
    is_final        = "FINAL" in template_code.upper()
    acc_amount      = str(sumup["paid_amount"]) if (is_final or is_intermediate) else ""

    turpe_map = _extract_turpe_v2(sumup)

    has_addon    = bool(obj.get("has_addons"))
    display_name = _get_display_name(details) if has_addon else None
    if display_name:
        display_name = PACK_MAP.get(display_name, display_name)

    # ---- PCLI: VAT_20 e VAT_5.5 ----
    vat_obj = details.get("vat", {})
    vat20_data  = vat_obj.get("20", {})
    vat55_data  = vat_obj.get("5.5", {})

    gross20  = Decimal(str(vat20_data.get("amount", "0"))) + Decimal(str(vat20_data.get("value_taxed", "0")))
    gross5_5 = Decimal(str(vat55_data.get("amount", "0"))) + Decimal(str(vat55_data.get("value_taxed", "0")))

    pcli_list = []
    if vat20_data:
        pcli_list.append(_comp("VAT_20",  str(gross20),  str(vat20_data.get("rate", ""))))
    if vat55_data:
        pcli_list.append(_comp("VAT_5.5", str(gross5_5), str(vat55_data.get("rate", ""))))

    # ---- PTAX ----
    ptax_list = []
    if vat20_data:
        ptax20 = Decimal(str(vat20_data.get("amount", "0")))
        ptax20 = _apply_sign_v2(ptax20, gross20)
        ptax_list.append(_comp("VAT_20", str(ptax20), str(vat20_data.get("rate", ""))))
    if vat55_data:
        ptax55 = Decimal(str(vat55_data.get("amount", "0")))
        ptax55 = _apply_sign_v2(ptax55, gross5_5)
        ptax_list.append(_comp("VAT_5_5", str(ptax55), str(vat55_data.get("rate", ""))))

    # ---- PRIC ----
    pric_list = []

    def _add_pric(name: str, amount: Decimal, vat_rate: str):
        # signum basato su vat_rate: se 20 usa gross20, altrimenti gross5_5
        ref = gross20 if vat_rate == "20" else gross5_5
        signed = _apply_sign_v2(amount, ref)
        pric_list.append(_comp(name, str(signed), vat_rate))

    # Turpe sum per sottrazione
    turpe20_sum = sum(
        Decimal(v["net_amount"]) for v in turpe_map.values() if v["vat_rate"] == "20"
    )
    turpe55_sum = sum(
        Decimal(v["net_amount"]) for v in turpe_map.values() if v["vat_rate"] == "5.5"
    )

    consumption_vat_rate  = str(sumup.get("consumption_vat_rate", "20"))
    subscription_vat_rate = str(sumup.get("subscription_vat_rate", "5.5"))

    consumption_amount  = Decimal(str(sumup.get("consumption_amount", "0")))
    subscription_amount = Decimal(str(sumup.get("subscription_amount", "0")))

    _add_pric("CONSUMPTION_N", consumption_amount - turpe20_sum, consumption_vat_rate)
    _add_pric("SUBSCRIPTION_N", subscription_amount - turpe55_sum, subscription_vat_rate)

    # CTA
    taxes = details.get("taxes", {})
    cta_array = taxes.get("CTA", [])
    cta_amount = sum(Decimal(str(e.get("amount", "0"))) for e in cta_array)
    cta_vat_rate = str(cta_array[0].get("vat_rate", "5.5")) if cta_array else "5.5"
    _add_pric("CTA_N", cta_amount, cta_vat_rate)

    # TICFE (ELEC) o TICGN (GAS)
    tax_key  = "TICGN" if is_gas else "TICFE"
    tax_comp = ("TICGN_N" if is_gas else "TICFE_N")
    tax_array = taxes.get(tax_key, [])
    if tax_array:
        tax_amount   = sum(Decimal(str(e.get("amount", "0"))) for e in tax_array)
        tax_vat_rate = str(tax_array[0].get("vat_rate", "5.5"))
        _add_pric(tax_comp, tax_amount, tax_vat_rate)

    # Turpe PRIC
    for comp_name, t_val in turpe_map.items():
        t_net = Decimal(t_val["net_amount"])
        vat_r = t_val["vat_rate"]
        ref   = gross20 if vat_r == "20" else gross5_5
        signed = _apply_sign_v2(t_net, ref)
        pric_list.append(_comp(comp_name, str(signed), vat_r))

    # Addon
    has_addon_vat0 = False
    round_list: list = []
    if has_addon and display_name:
        PCK_TSCA = {"PCK_HOME_P", "SAXA_G3ANS"}
        if display_name.upper() in PCK_TSCA:
            tsca_amount = Decimal(str(sumup.get("tsca_amount", "0")))
            pric_list.append(_comp("TSCA_N", str(-tsca_amount), "0"))
            _add_vat0_to_round(round_list, -tsca_amount)
            has_addon_vat0 = True

        addon_amount   = Decimal(str(sumup.get("addons_amount", "0")))
        addon_vat_rate = str(sumup.get("addons_vat_rate", ""))
        ref = gross20 if addon_vat_rate == "20" else gross5_5
        pric_list.append(_comp(display_name + "_N", str(-addon_amount), addon_vat_rate))

        if addon_vat_rate == "0":
            _add_vat0_to_round(round_list, addon_amount)
            has_addon_vat0 = True

    # ---- ROUND ----
    total_pcli = sum(Decimal(c["amount"]) for c in pcli_list)
    if round_list:
        total_pcli += Decimal(str(round_list[0]["amount"]))

    sumup_gross = Decimal(str(sumup["gross_amount"]))
    round_pcli_val = sumup_gross - total_pcli
    gross_with_round = total_pcli + round_pcli_val

    total_pric = sum(Decimal(c["amount"]) for c in pric_list)
    total_ptax = sum(Decimal(c["amount"]) for c in ptax_list)
    round_pric_val = (gross_with_round + total_pric + total_ptax) * Decimal("-1")

    _add_vat0_to_round(round_list, round_pcli_val)
    round_list.append(_comp("ROUND_N", str(round_pric_val), ""))

    if round_pcli_val != 0 or has_addon_vat0:
        ptax_list.append(_comp("VAT_0", "-0.00", "0.00"))

    result = {
        "PCLI":  pcli_list,
        "PRIC":  pric_list,
        "PTAX":  ptax_list,
        "ACC":   {"componentName": "ACC", "amount": acc_amount, "vatRate": ""},
        "ROUND": round_list,
    }
    return json.dumps(result)


def build_template_split_json_v3(vars_json: str, template_code: str) -> str:
    """
    Replica Java ElectricityInvoiceCalculator / GasInvoiceCalculator (V3).
    Stessa struttura di V2 ma:
    - turpe estratto con logica V3 (struttura {vat_20: val, vat_5.5: val})
    - subscription da details.subscription[] (array per vat_rate)
    - ELEC: TICFE_N; GAS: TICGN_N + ATRD components (PFATRD_V3, PFATRD_N, PVATRD_N)
    - turpe PRIC sempre negato (non signum)
    """
    obj      = json.loads(vars_json)
    sumup    = obj["sumup"]
    details  = obj.get("details", {})
    is_gas   = COMMODITY == "GAS"

    is_intermediate = "INTERMEDIATE" in template_code.upper()
    is_final        = "FINAL" in template_code.upper()
    acc_amount      = str(sumup["paid_amount"]) if (is_final or is_intermediate) else ""

    turpe_map = _extract_turpe_v3(sumup)

    has_addon    = bool(obj.get("has_addons"))
    display_name = _get_display_name(details) if has_addon else None
    if display_name:
        display_name = PACK_MAP.get(display_name, display_name)

    # ---- PCLI ----
    vat_obj  = details.get("vat", {})
    vat20_d  = vat_obj.get("20", {})
    vat55_d  = vat_obj.get("5.5", {})

    gross20  = Decimal(str(vat20_d.get("amount", "0"))) + Decimal(str(vat20_d.get("value_taxed", "0")))
    gross5_5 = Decimal(str(vat55_d.get("amount", "0"))) + Decimal(str(vat55_d.get("value_taxed", "0")))

    pcli_list = []
    if vat20_d:
        pcli_list.append(_comp("VAT_20",  str(gross20),  str(vat20_d.get("rate", ""))))
    if vat55_d:
        pcli_list.append(_comp("VAT_5.5", str(gross5_5), str(vat55_d.get("rate", ""))))

    # ---- PTAX ----
    ptax_list = []
    if vat20_d:
        ptax_list.append(_comp("VAT_20",  str(-Decimal(str(vat20_d.get("amount", "0")))), str(vat20_d.get("rate", ""))))
    if vat55_d:
        ptax_list.append(_comp("VAT_5_5", str(-Decimal(str(vat55_d.get("amount", "0")))), str(vat55_d.get("rate", ""))))

    pric_list = []
    round_list: list = []

    # ---- GAS: ATRD components ----
    if is_gas:
        atrd_var_20   = Decimal("0")
        atrd_fixed_20 = Decimal("0")
        atrd_fixed_55 = Decimal("0")

        atrd_var = sumup.get("atrd_variable_components", {}).get("consumption", {})
        if atrd_var.get("vat_20") is not None:
            atrd_var_20 = Decimal(str(atrd_var["vat_20"]))

        atrd_fix = sumup.get("atrd_fixed_components", {}).get("subscription", {})
        if atrd_fix.get("vat_20") is not None:
            atrd_fixed_20 = Decimal(str(atrd_fix["vat_20"]))
        if atrd_fix.get("vat_5.5") is not None:
            atrd_fixed_55 = Decimal(str(atrd_fix["vat_5.5"]))

        if atrd_fixed_20 != 0:
            pric_list.append(_comp("PFATRD_V3", str(-atrd_fixed_20), "20"))
        if atrd_fixed_55 != 0:
            pric_list.append(_comp("PFATRD_N",  str(-atrd_fixed_55), "5.5"))
        if atrd_var_20 != 0:
            pric_list.append(_comp("PVATRD_N",  str(-atrd_var_20),   "20"))

        # CONSUMPTION (GAS): sottrae ATRD variable
        consumption_vat_rate = str(sumup.get("consumption_vat_rate", "20"))
        consumption_amount   = Decimal(str(sumup.get("consumption_amount", "0")))
        pric_list.append(_comp("CONSUMPTION_N", str(-(consumption_amount - atrd_var_20)), consumption_vat_rate))

        # SUBSCRIPTION (GAS): da details.subscription[]
        sub_array   = details.get("subscription", [])
        sub_amounts: Dict[str, Decimal] = {}
        for sub in sub_array:
            vr  = str(sub.get("vat_rate", ""))
            net = Decimal(str(sub.get("net_amount", "0")))
            sub_amounts[vr] = sub_amounts.get(vr, Decimal("0")) + net

        for vr, net in sub_amounts.items():
            if vr == "5.5":
                pric_list.append(_comp("SUBSCRIPTION_N",  str(-(net - atrd_fixed_55)), vr))
            elif vr == "20":
                pric_list.append(_comp("SUBSCRIPTION_V3", str(-(net - atrd_fixed_20)), vr))

    else:
        # ---- ELEC ----
        # Turpe sum per sottrazione (V3 usa PVCS_N separato per consumption)
        pvcs_sum = sum(
            Decimal(v["net_amount"])
            for k, v in turpe_map.items() if k.upper() == "PVCS_N"
        )
        turpe20_no_pvcs = sum(
            Decimal(v["net_amount"])
            for k, v in turpe_map.items()
            if v["vat_rate"] == "20" and k.upper() != "PVCS_N"
        )
        turpe55_no_pvcs = sum(
            Decimal(v["net_amount"])
            for k, v in turpe_map.items()
            if v["vat_rate"] == "5.5" and k.upper() != "PVCS_N"
        )

        consumption_vat_rate = str(sumup.get("consumption_vat_rate", "20"))
        consumption_amount   = Decimal(str(sumup.get("consumption_amount", "0")))
        pric_list.append(_comp("CONSUMPTION_N", str(-(consumption_amount - pvcs_sum)), consumption_vat_rate))

        sub_array   = details.get("subscription", [])
        sub_amounts: Dict[str, Decimal] = {}
        for sub in sub_array:
            vr  = str(sub.get("vat_rate", ""))
            net = Decimal(str(sub.get("net_amount", "0")))
            sub_amounts[vr] = sub_amounts.get(vr, Decimal("0")) + net

        for vr, net in sub_amounts.items():
            if vr == "5.5":
                pric_list.append(_comp("SUBSCRIPTION_N",  str(-(net - turpe55_no_pvcs)), vr))
            elif vr == "20":
                pric_list.append(_comp("SUBSCRIPTION_V3", str(-(net - turpe20_no_pvcs)), vr))

    # ---- CTA (comune ELEC e GAS) ----
    taxes = details.get("taxes", {})
    cta_amounts: Dict[str, Decimal] = {}
    for e in taxes.get("CTA", []):
        vr = str(e.get("vat_rate", ""))
        cta_amounts[vr] = cta_amounts.get(vr, Decimal("0")) + Decimal(str(e.get("amount", "0")))
    for vr, amt in cta_amounts.items():
        comp_name = "CTA_V3" if vr == "20" else "CTA_N"
        pric_list.append(_comp(comp_name, str(-amt), vr))

    # ---- TICFE (ELEC) o TICGN (GAS) ----
    tax_key  = "TICGN" if is_gas else "TICFE"
    tax_name = "TICGN_N" if is_gas else "TICFE_N"
    tax_arr  = taxes.get(tax_key, [])
    if tax_arr:
        tax_total    = sum(Decimal(str(e.get("amount", "0"))) for e in tax_arr)
        tax_vat_rate = str(tax_arr[0].get("vat_rate", ""))
        pric_list.append(_comp(tax_name, str(-tax_total), tax_vat_rate))

    # ---- Turpe PRIC (V3: sempre negate) ----
    for comp_name, t_val in turpe_map.items():
        t_net = Decimal(t_val["net_amount"])
        pric_list.append(_comp(comp_name, str(-t_net), t_val["vat_rate"]))

    # ---- Addon ----
    has_addon_vat0 = False
    if has_addon and display_name:
        PCK_TSCA = {"PCK_HOME_P", "SAXA_G3ANS"}
        if display_name.upper() in PCK_TSCA:
            tsca_amount = Decimal(str(sumup.get("tsca_amount", "0")))
            pric_list.append(_comp("TSCA_N", str(-tsca_amount), "0"))
            _add_vat0_to_round(round_list, -tsca_amount)
            has_addon_vat0 = True

        addon_amount   = Decimal(str(sumup.get("addons_amount", "0")))
        addon_vat_rate = str(sumup.get("addons_vat_rate", ""))
        pric_list.append(_comp(display_name + "_N", str(-addon_amount), addon_vat_rate))

        if addon_vat_rate == "0":
            _add_vat0_to_round(round_list, addon_amount)
            has_addon_vat0 = True

    # ---- ROUND ----
    total_pcli = sum(Decimal(c["amount"]) for c in pcli_list)
    if round_list:
        total_pcli += Decimal(str(round_list[0]["amount"]))

    sumup_gross    = Decimal(str(sumup["gross_amount"]))
    round_pcli_val = sumup_gross - total_pcli
    gross_with_round = total_pcli + round_pcli_val

    total_pric = sum(Decimal(c["amount"]) for c in pric_list)
    total_ptax = sum(Decimal(c["amount"]) for c in ptax_list)
    round_pric_val = (gross_with_round + total_pric + total_ptax) * Decimal("-1")

    _add_vat0_to_round(round_list, round_pcli_val)
    round_list.append(_comp("ROUND_N", str(round_pric_val), ""))

    if round_pcli_val != 0 or has_addon_vat0:
        ptax_list.append(_comp("VAT_0", "-0.00", "0.00"))

    result = {
        "PCLI":  pcli_list,
        "PRIC":  pric_list,
        "PTAX":  ptax_list,
        "ACC":   {"componentName": "ACC", "amount": acc_amount, "vatRate": ""},
        "ROUND": round_list,
    }
    return json.dumps(result)


def add_vars_json_values(invoice: Invoice):
    """
    Replica Java addVarsJsonValues() / addVarsJsonValuesV1/V2/V3.
    Popola:
      - to_be_paid_amount / invoice_amount
      - payment_at
      - payment_amount_rb
      - template_split_json (V1 only, le altre versioni usano logica interna Java più complessa)
      - is_negative
    """
    try:
        obj = json.loads(invoice.vars_json)
        sumup = obj.get("sumup", {})

        # Scelta campo amount
        is_monthly_intermediate = (
            invoice.is_monthly_billing and
            "INTERMEDIATE" in invoice.template_code.upper()
        )
        amount_field = "gross_amount" if is_monthly_intermediate else "payment_amount"

        raw_amount = str(sumup.get(amount_field, "0")).replace(".", "")
        invoice.to_be_paid_amount = raw_amount
        invoice.invoice_amount = raw_amount
        invoice.payment_at = str(sumup.get("payment_at", ""))
        invoice.payment_amount_rb = str(sumup.get("payment_amount", "0")).replace(".", "")
        invoice.is_negative = bool(sumup.get("is_negative", False))

        # Costruisce template_split_json replicando InvoiceJsonManager
        if invoice.kraken_version in ("V1", "", None):
            invoice.template_split_json = build_template_split_json_v1(
                invoice.vars_json, invoice.template_code
            )
        elif invoice.kraken_version == "V2":
            invoice.template_split_json = build_template_split_json_v2(
                invoice.vars_json, invoice.template_code
            )
        elif invoice.kraken_version == "V3":
            invoice.template_split_json = build_template_split_json_v3(
                invoice.vars_json, invoice.template_code
            )
        else:
            log.warning("Versione Kraken non gestita: %s (invoice %s)",
                        invoice.kraken_version, invoice.identifier)

    except Exception as e:
        log.error("Errore addVarsJsonValues per invoice %s: %s", invoice.identifier, e)
        raise


# =============================================================================
# STEP 4: VALIDAZIONE
# =============================================================================

def get_round_amount(template_split_json: str) -> Decimal:
    """
    Replica Java getRoundAmount().
    Cerca ROUND[*].componentName in (ROUND_N, ROUND, ROUND_V3) e restituisce l'amount.
    """
    if not template_split_json:
        return Decimal("0")
    try:
        obj = json.loads(template_split_json)
        round_array = obj.get("ROUND", [])
        for node in round_array:
            name = node.get("componentName", "").upper()
            if name in ("ROUND_N", "ROUND", "ROUND_V3"):
                return Decimal(str(node.get("amount", "0")))
    except Exception as e:
        log.warning("Errore nel parsing ROUND amount: %s", e)
    return Decimal("0")


def set_sap_plan_id_or_agreement_id(invoice: Invoice, plan_map: Dict[str, tuple]) -> tuple:
    """
    Imposta sap_plan_id e agreement_id dall'input map.
    Regole:
    - Monthly o ANNULMENT → blank, OK
    - Trovato nel plan_map → setta i valori, OK
    - Non trovato → KO (MISSING_PAYMENT_PLAN)
    Validazione: almeno uno tra sap_plan_id e agreement_id deve essere presente.
    """
    if invoice.is_monthly_billing or "ANNULMENT" in invoice.template_code.upper():
        invoice.sap_plan_id = ""
        invoice.agreement_id = ""
        return True, None

    entry = plan_map.get(invoice.identifier)
    if entry is None:
        return False, "MISSING_PAYMENT_PLAN"

    sap_plan_id, agreement_id = entry
    invoice.sap_plan_id  = sap_plan_id
    invoice.agreement_id = agreement_id
    return True, None


# =============================================================================
# STEP 5: KO
# =============================================================================


def evaluate_invoices(invoices: List[Invoice],
                      plan_map: Dict[str, tuple]) -> Tuple[List[Invoice], List[dict]]:
    """
    Replica Java evaluateInvoice() per ogni invoice della lista.
    Restituisce (invoices_ok, ko_records).
    ko_records è una lista di dict con 'invoice', 'table', 'reason'.
    """
    ok_list = []
    ko_list = []

    for invoice in invoices:
        # --- Check rounding ---
        round_amount = get_round_amount(invoice.template_split_json)
        if abs(round_amount) > B2C_ABS_ROUNDING:
            log.warning(
                "Invoice %s -> KO (ROUND_THRESHOLD_EXCEEDED) round=%s soglia=%s",
                invoice.identifier, round_amount, B2C_ABS_ROUNDING
            )
            ko_list.append({
                "invoice": invoice,
                "table": "kraken_scraps",
                "reason": "ROUND_THRESHOLD_EXCEEDED",
            })
            continue

        # --- Check SAP Plan / Agreement ID ---
        ok, reason = set_sap_plan_id_or_agreement_id(invoice, plan_map)
        if not ok:
            log.warning("Invoice %s -> KO (%s)", invoice.identifier, reason)
            ko_list.append({
                "invoice": invoice,
                "table": "stg_invoice_waiting_check",
                "reason": reason,
            })
            continue

        ok_list.append(invoice)

    return ok_list, ko_list


def save_ko_invoices(ko_list: List[dict]) -> int:
    """Logga le invoice KO nel file di errore (nessuna scrittura su DB)."""
    for item in ko_list:
        log.warning("KO | identifier=%s | reason=%s", item["invoice"].identifier, item["reason"])
    return 0


# =============================================================================
# STEP 6: GENERAZIONE CSV SAP
# =============================================================================

def is_zero_amount(amount: str) -> bool:
    try:
        return Decimal(amount) == 0
    except Exception:
        return False


def convert_to_american_format(date_str: str) -> str:
    """
    Replica esatta di Java DateParser.convertToAmericanFormat():
    prende i primi 10 caratteri e rimuove i '-'.
    Il Java ha un bug: chiama date.format() ma non usa il risultato,
    quindi ritorna sempre substring(0,10).replace("-","").
    """
    if not date_str or len(date_str) < 10:
        return ""
    return date_str[:10].replace("-", "")


def get_vat_code(component_name: str) -> str:
    """Replica Java InvoiceSapVatCode.fromComponentName()."""
    upper = component_name.upper()
    if upper in PCK_B9_COMPONENTS:
        return "VAT_B9"
    return VAT_CODE_MAP.get(upper, "VAT_ERROR")


def build_account_detail(
    record_type: str,
    bill_number: str,
    value_date: str,
    doc_type: str,
    template_code: str,
    component_name: str,
    movement_type: str,
    expiration_date: str,
    pod: str,
    kraken_account: str,
    amount: str,
    original_statement_identifier: str,
    contract_end_date: str,
    sap_plan_id: str,
    agreement_id: str,
    counter: int,
) -> AccountDetailRow:
    row = AccountDetailRow()
    row.reference = bill_number
    row.value_date = value_date.replace("/", "")
    row.record_type = record_type
    row.counter = counter
    row.document_type = doc_type
    row.template_code = template_code
    row.component_detail = component_name
    row.movement_type = movement_type
    row.expiration_date = expiration_date.replace("/", "")
    row.point_of_delivery = pod
    row.kraken_account = kraken_account
    row.commodity = COMMODITY_SAP_CODE()
    row.characteristic_of_accounts = "03"
    row.amount = amount
    row.original_statement_identifier = original_statement_identifier
    row.contract_end_date = contract_end_date.replace("/", "")
    row.sap_plan_id = sap_plan_id
    row.agreement_id = agreement_id
    row.segment = "RESIDENT"
    return row


def create_invoice_template_map(invoices: List[Invoice]) -> Dict[str, Dict[str, InvoiceTemplate]]:
    """
    Replica Java createInvoiceTemplateMapFromInvoiceList().
    Raggruppa le invoice per data (American format) e per doc_type (KM/KR/KK/KF).
    Restituisce: { date_str: { doc_type: InvoiceTemplate } }
    """
    invoice_map: Dict[str, List[Invoice]] = {}
    for inv in invoices:
        key_date = convert_to_american_format(inv.finalized_at)
        invoice_map.setdefault(key_date, []).append(inv)

    result: Dict[str, Dict[str, InvoiceTemplate]] = {}

    for date_key, date_invoices in invoice_map.items():
        pcli_list: List[AccountDetailRow] = []
        pric_list: List[AccountDetailRow] = []
        ptax_list: List[AccountDetailRow] = []
        acc_list: List[AccountDetailRow] = []

        for invoice in date_invoices:
            try:
                obj = json.loads(invoice.vars_json)
            except Exception:
                log.error("Errore parsing vars_json per invoice %s", invoice.identifier)
                continue

            sumup = obj.get("sumup", {})
            bill_number = invoice.identifier
            doc_type = ""
            value_date = convert_to_american_format(invoice.finalized_at)
            template_code = invoice.template_code
            pod = invoice.prm
            original_statement_identifier = ""
            contract_end_date = ""

            expiration_date = convert_to_american_format(
                str(sumup.get("payment_at", invoice.payment_at))
            )
            sap_plan_id = invoice.sap_plan_id
            agreement_id = invoice.agreement_id
            kraken_account = invoice.number

            is_monthly = obj.get("is_monthly_billing", invoice.is_monthly_billing)
            is_annulment = "annulment_statement_identifier" in obj
            is_intermediate = "INTERMEDIATE" in template_code.upper()
            is_final = "FINAL" in template_code.upper()

            movement_type = "K200" if is_final else "K100"

            # --- Doc Type ---
            if is_monthly and is_intermediate:
                doc_type = "KM"

            if not is_monthly and is_intermediate:
                doc_type = "KR"
                # ACC per KR
                try:
                    split_obj = json.loads(invoice.template_split_json) if invoice.template_split_json else {}
                    acc_data = split_obj.get("ACC", {})
                    acc_amount = str(acc_data.get("amount", "0"))
                    if acc_amount and acc_amount != "0":
                        acc_row = build_account_detail(
                            "ACC", bill_number, value_date, doc_type, template_code,
                            "", movement_type, expiration_date, pod, kraken_account,
                            acc_amount, original_statement_identifier, contract_end_date,
                            sap_plan_id, agreement_id, 1,
                        )
                        acc_list.append(acc_row)
                except Exception as e:
                    log.warning("Errore ACC per invoice KR %s: %s", invoice.identifier, e)

            if is_annulment:
                doc_type = "KK"
                original_statement_identifier = str(
                    obj.get("original_statement_identifier", "")
                )

            if is_final:
                doc_type = "KF"
                agreement_info = obj.get("agreement_info", {})
                date_valid_to = str(agreement_info.get("valid_to", ""))
                contract_end_date = convert_to_american_format(date_valid_to)

                # ACC per KF non-monthly
                if not is_monthly:
                    try:
                        split_obj = json.loads(invoice.template_split_json) if invoice.template_split_json else {}
                        acc_data = split_obj.get("ACC", {})
                        acc_amount = str(acc_data.get("amount", "0"))
                        if acc_amount and acc_amount != "0":
                            acc_row = build_account_detail(
                                "ACC", bill_number, value_date, doc_type, template_code,
                                "", movement_type, expiration_date, pod, kraken_account,
                                acc_amount, original_statement_identifier, contract_end_date,
                                sap_plan_id, agreement_id, 1,
                            )
                            acc_list.append(acc_row)
                    except Exception as e:
                        log.warning("Errore ACC per invoice KF %s: %s", invoice.identifier, e)

            # --- template_split_json parsing ---
            try:
                split_obj = json.loads(invoice.template_split_json) if invoice.template_split_json else {}
            except Exception:
                split_obj = {}

            pcli_components = split_obj.get("PCLI", [])
            pric_components = split_obj.get("PRIC", [])
            ptax_components = split_obj.get("PTAX", [])
            round_components = split_obj.get("ROUND", [])

            # --- PCLI ---
            counter_pcli = 0
            for comp in pcli_components:
                amount = str(comp.get("amount", "0"))
                if is_zero_amount(amount):
                    continue
                counter_pcli += 1
                row = build_account_detail(
                    "PCLI", bill_number, value_date, doc_type, template_code,
                    comp.get("componentName", ""), movement_type, expiration_date,
                    pod, kraken_account, amount, original_statement_identifier,
                    contract_end_date, sap_plan_id, agreement_id, counter_pcli,
                )
                pcli_list.append(row)

            # ROUND PCLI (ROUND[0])
            if round_components:
                r0 = round_components[0]
                r0_amount = str(r0.get("amount", "0"))
                if not is_zero_amount(r0_amount):
                    counter_pcli += 1
                    row = build_account_detail(
                        "PCLI", bill_number, value_date, doc_type, template_code,
                        r0.get("componentName", ""), movement_type, expiration_date,
                        pod, kraken_account, r0_amount, original_statement_identifier,
                        contract_end_date, sap_plan_id, agreement_id, counter_pcli,
                    )
                    pcli_list.append(row)

            # --- PRIC ---
            counter_pric = 0
            for comp in pric_components:
                amount = str(comp.get("amount", "0"))
                if is_zero_amount(amount):
                    continue
                counter_pric += 1
                row = build_account_detail(
                    "PRIC", bill_number, value_date, doc_type, template_code,
                    comp.get("componentName", ""), movement_type, expiration_date,
                    pod, kraken_account, amount, original_statement_identifier,
                    contract_end_date, sap_plan_id, agreement_id, counter_pric,
                )
                pric_list.append(row)

            # ROUND PRIC (ROUND[1])
            if len(round_components) > 1:
                r1 = round_components[1]
                r1_amount = str(r1.get("amount", "0"))
                if not is_zero_amount(r1_amount):
                    counter_pric += 1
                    row = build_account_detail(
                        "PRIC", bill_number, value_date, doc_type, template_code,
                        r1.get("componentName", ""), movement_type, expiration_date,
                        pod, kraken_account, r1_amount, original_statement_identifier,
                        contract_end_date, sap_plan_id, agreement_id, counter_pric,
                    )
                    pric_list.append(row)

            # --- PTAX ---
            ptax_map: Dict[str, AccountDetailRow] = {}
            counter_ptax = 0
            for comp in ptax_components:
                comp_name = comp.get("componentName", "")
                comp_amount = Decimal(str(comp.get("amount", "0")))
                comp_name_upper = comp_name.upper()

                if comp_name_upper in PCK_B9_COMPONENTS:
                    code = "VAT_B9"
                else:
                    code = get_vat_code(comp_name_upper)

                if code in ptax_map:
                    # Aggrega amount sullo stesso codice
                    existing = ptax_map[code]
                    current = Decimal(existing.amount)
                    ptax_map[code].amount = str(current + comp_amount)
                else:
                    # Nuova entry
                    # Filtro: includi se SAXA_G3ANS o amount != 0.00 AND comp_name != VAT_0
                    include = (
                        comp_name_upper == "SAXA_G3ANS" or
                        str(comp_amount) != "0.00"
                    ) and comp_name_upper != "VAT_0"

                    # VAT_TG e VAT_0 vengono aggiunti con segno negativo
                    negate = comp_name_upper in ("VAT_TG", "VAT_0")

                    if include or negate:
                        counter_ptax += 1
                        amount_str = str(-comp_amount) if negate else str(comp_amount)
                        row = build_account_detail(
                            "PTAX", bill_number, value_date, doc_type, template_code,
                            code, movement_type, expiration_date,
                            pod, kraken_account, amount_str, original_statement_identifier,
                            contract_end_date, sap_plan_id, agreement_id, counter_ptax,
                        )
                        ptax_map[code] = row

            # Filtra PTAX: includi solo se amount != 0.00 oppure è VAT_TG/VAT_0/VAT_CF
            for code, ptax_row in ptax_map.items():
                if (
                    ptax_row.amount != "0.00" or
                    ptax_row.component_detail in ("VAT_TG", "VAT_0", "VAT_CF")
                ):
                    ptax_list.append(ptax_row)

            # Ordina PTAX per reference poi counter
            ptax_list.sort(key=lambda r: (r.reference, r.counter))

        # Raggruppa per doc_type e costruisce InvoiceTemplate
        date_result: Dict[str, InvoiceTemplate] = {}
        for row in pric_list + pcli_list + ptax_list + acc_list:
            dt = row.document_type
            if dt not in date_result:
                date_result[dt] = InvoiceTemplate()
        for row in pric_list:
            date_result[row.document_type].pric.append(row)
        for row in pcli_list:
            date_result[row.document_type].pcli.append(row)
        for row in ptax_list:
            date_result[row.document_type].ptax.append(row)
        for row in acc_list:
            date_result[row.document_type].acc.append(row)

        result[date_key] = date_result

    return result


def row_to_csv_fields(row: AccountDetailRow) -> List[str]:
    """
    Serializza una AccountDetailRow in lista di campi per CSV.
    Replica Java getObjectAttributeValues(): skip dei campi in CSV_SKIP_FIELDS,
    sostituisce '/' con '' nei valori stringa.
    """
    fields_order = [
        "reference", "value_date", "record_type", "counter",
        "document_type", "template_code", "component_detail",
        "movement_type", "expiration_date", "point_of_delivery",
        "kraken_account", "commodity", "characteristic_of_accounts",
        "amount", "original_statement_identifier", "contract_end_date",
        "sap_plan_id", "agreement_id", "segment",
    ]
    result = []
    for f in fields_order:
        if f in CSV_SKIP_FIELDS:
            continue
        val = getattr(row, f, "")
        if val is None:
            val = ""
        val = str(val).replace("/", "")
        result.append(val)
    return result


def generate_csv_files(template_map: Dict[str, Dict[str, InvoiceTemplate]]):
    """
    Genera i file CSV SAP in OUTPUT_DIR.
    Replica Java CSVSapObjectService.createMultipleCSVFileFromSapInvoiceList()

    Nome file: {DOCTYPE}_{COMMODITY}_{TIMESTAMP}_{INVOICEDATE}.csv
    """
    if not template_map:
        return

    execution_date = datetime.now().strftime("%Y%m%d%H%M%S")
    files_per_dir: Dict[str, int] = {}
    identifiers_per_dir: Dict[str, set] = {}

    for invoice_date, doc_type_map in template_map.items():
        # invoice_date è già in formato yyyyMMdd (da convert_to_american_format)
        invoice_date_clean = invoice_date

        for doc_type, template in doc_type_map.items():
            doc_type_dir = OUTPUT_DIR / doc_type.upper()
            doc_type_dir.mkdir(exist_ok=True)
            file_name = f"{doc_type}_{COMMODITY_SHORT()}_{execution_date}_{invoice_date_clean}.csv"
            file_path = doc_type_dir / file_name

            # Calcola header stats
            # totalBillNumber = numero di reference uniche
            all_references = set()
            for row in template.pcli + template.pric + template.ptax + template.acc:
                all_references.add(row.reference)
            total_bill_number = len(all_references)

            # totalAmount = somma amount PCLI
            total_amount = Decimal("0")
            for row in template.pcli:
                try:
                    total_amount += Decimal(row.amount)
                except Exception:
                    pass

            # HEADER row: PA;{totalBillNumber};{registrationDate};{totalAmount};EUR
            registration_date = date.today().strftime("%Y%m%d")

            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";", quoting=csv.QUOTE_NONE, escapechar="\\", lineterminator="\n")

                # HEADER
                writer.writerow(["PA", total_bill_number, registration_date, float(total_amount), "EUR"])

                # PCLI
                for row in template.pcli:
                    writer.writerow(row_to_csv_fields(row))

                # PRIC
                for row in template.pric:
                    writer.writerow(row_to_csv_fields(row))

                # PTAX (con negazione per VAT_TG / VAT_TG_N - replica Java)
                for row in template.ptax:
                    if row.component_detail.upper() in ("VAT_TG", "VAT_TG_N"):
                        if not row.amount.startswith("-"):
                            row.amount = "-" + row.amount
                    writer.writerow(row_to_csv_fields(row))

                # ACC (solo per KR e KF)
                if doc_type.upper() in ("KR", "KF"):
                    for row in template.acc:
                        writer.writerow(row_to_csv_fields(row))

                # FOOTER
                writer.writerow(["PA", "END"])

            dt_key = doc_type.upper()
            files_per_dir[dt_key] = files_per_dir.get(dt_key, 0) + 1
            identifiers_per_dir.setdefault(dt_key, set()).update(all_references)

    summary = ", ".join(
        f"{dt}: {files_per_dir[dt]} file ({len(identifiers_per_dir[dt])} identifier)"
        for dt in sorted(files_per_dir)
    )
    log.info("File CSV scritti -> %s", summary)

    # Crea uno ZIP per ogni doc_type con i CSV della sottocartella
    import zipfile
    for dt_key in files_per_dir:
        dt_dir = OUTPUT_DIR / dt_key
        zip_path = OUTPUT_DIR / f"{dt_key}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for csv_file in dt_dir.glob("*.csv"):
                zf.write(csv_file, csv_file.name)
    log.info("ZIP creati: %s", ", ".join(f"{dt}.zip" for dt in sorted(files_per_dir)))


# =============================================================================
# MAIN
# =============================================================================

def clean_output_dir():
    """Svuota il contenuto di output/ ed error/ prima di ogni esecuzione,
    senza rimuovere le cartelle stesse (evita lock OneDrive/Explorer su rmtree)."""
    import shutil

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for item in OUTPUT_DIR.iterdir():
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink(missing_ok=True)
        except PermissionError as e:
            log.warning("Impossibile rimuovere %s (file in uso/OneDrive): %s", item, e)

    # Pulisce error/ ma non cancella il file di log corrente già aperto
    if ERROR_DIR.exists():
        for f in ERROR_DIR.iterdir():
            if f != _log_file:
                try:
                    f.unlink(missing_ok=True)
                except PermissionError:
                    pass


def run_for_commodity(commodity: str, hub_conn, kraken_conn, lista_identifier: str,
                      plan_map: Dict[str, tuple], version_map: Dict[str, str]):
    global COMMODITY
    COMMODITY = commodity

    log.info("=" * 60)
    log.info("COMMODITY: %s", COMMODITY)
    log.info("=" * 60)

    # STEP 1: lettura invoice da Kraken via lista identifier
    # (stesse query query_invoice_elec.sql / query_invoice_gas.sql usate da
    #  Kraken Data Extractor in modalità "by identifier")
    try:
        rows = fetch_invoices_from_kraken(COMMODITY, lista_identifier, hub_conn, kraken_conn)
    except Exception as e:
        log.error("Impossibile leggere le invoice da Kraken: %s", e)
        return

    log.info("Record letti da Kraken: %d", len(rows))

    if not rows:
        log.info("Nessuna invoice trovata.")
        return

    # STEP 2: ResultSet -> InputInvoice
    input_invoices: List[InputInvoice] = []
    malformed_count = 0
    for row in rows:
        try:
            inp = result_set_to_input_invoice(row, BATCH_UUID, version_map)
            if inp is not None:
                input_invoices.append(inp)
            else:
                malformed_count += 1
        except Exception as e:
            malformed_count += 1
            log.error("Errore mapping row %s: %s", row.get("identifier", "?"), e)

    if malformed_count:
        log.warning("Record malformati (PRM/PCE mancante): %d", malformed_count)

    # STEP 3: InputInvoice -> Invoice
    invoices: List[Invoice] = []
    mapping_errors = 0
    for inp in input_invoices:
        try:
            inv = input_invoice_to_invoice(inp)
            add_vars_json_values(inv)
            invoices.append(inv)
        except Exception as e:
            mapping_errors += 1
            log.error("Errore mapping invoice %s: %s", inp.identifier, e)

    log.info("Invoice mappate: %d (errori mapping: %d)", len(invoices), mapping_errors)

    # STEP 4: Validazione
    ok_invoices, ko_list = evaluate_invoices(invoices, plan_map)

    # STEP 5: Salvataggio KO
    save_errors = save_ko_invoices(ko_list)

    ko_by_reason: Dict[str, int] = {}
    for item in ko_list:
        r = item["reason"]
        ko_by_reason[r] = ko_by_reason.get(r, 0) + 1

    # STEP 6: Generazione CSV SAP
    if ok_invoices:
        template_map = create_invoice_template_map(ok_invoices)
        generate_csv_files(template_map)

    log.info("RIEPILOGO %s", COMMODITY)
    log.info("  Lavorati         : %d", len(rows))
    log.info("  OK (CSV)         : %d", len(ok_invoices))
    log.info("  KO totali        : %d", len(ko_list))
    for reason, count in sorted(ko_by_reason.items()):
        log.info("    %-35s: %d", reason, count)
    if malformed_count:
        log.info("  Malformati       : %d", malformed_count)
    if mapping_errors:
        log.info("  Errori mapping   : %d", mapping_errors)
    if save_errors:
        log.info("  Errori salvataggio KO: %d", save_errors)


def main():
    clean_output_dir()

    try:
        lista_identifier, plan_map = iw_load_identifier_data()
    except (FileNotFoundError, ValueError) as e:
        log.error("%s", e)
        return

    log.info("Caricati %d identifier dal file di input.", len(plan_map))

    log.info("Connessione HUB: %s ...", os.getenv("HUB_HOST"))
    try:
        hub_conn = get_hub_connection()
        log.info("Connessione HUB attiva.")
    except Exception as e:
        log.error("Connessione HUB fallita: %s", e)
        return

    log.info("Connessione Kraken: %s / %s ...", os.getenv("KRAKEN_HOST"), os.getenv("KRAKEN_NAME"))
    try:
        kraken_conn = get_kraken_connection()
        log.info("Connessione Kraken attiva.")
    except Exception as e:
        log.error("Connessione Kraken fallita: %s", e)
        hub_conn.close()
        return

    try:
        # Version map (opzionale) — letta una sola volta
        version_map: Dict[str, str] = {}
        try:
            with hub_conn.cursor() as cur:
                cur.execute("SELECT identifier, version FROM identifier_version_map")
                for r in cur.fetchall():
                    version_map[r[0]] = r[1]
        except Exception:
            hub_conn.rollback()

        run_for_commodity("ELEC", hub_conn, kraken_conn, lista_identifier, plan_map, version_map)
        run_for_commodity("GAS",  hub_conn, kraken_conn, lista_identifier, plan_map, version_map)
    finally:
        try:
            kraken_conn.close()
        except Exception:
            pass
        try:
            hub_conn.close()
        except Exception:
            pass

    log.info("=" * 60)
    log.info("COMPLETATO")
    log.info("=" * 60)

# ── Fine Invoice Writer (logica) ──────────────────────────────────────────────


class InvoiceWriter(_AppBase):
    """Wrapper GUI per Invoice Writer — lista identifier (come Kraken Data
    Extractor) + bottone Avvia + log."""

    def __init__(self, master):
        super().__init__(master, bg=BG)
        self._log_queue = queue.Queue()
        self._running   = False
        self._build_ui()
        self._load_identifier_into_table()
        self._poll_log()

    def _build_ui(self):
        self._status_var = tkinter.StringVar(value="Pronto.")
        Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, side="bottom")
        self._status_lbl = Label(self, textvariable=self._status_var, bg=BG, fg=TEXT_SEC,
                                  font=("Consolas", 9), anchor="w", pady=5)
        self._status_lbl.pack(fill="x", padx=24, side="bottom")
        self._build_notebook([
            ("  ▶  Pipeline  ",    self._build_pipeline_tab),
            ("  📋  Data Input  ", self._build_data_input_tab),
        ])

    # ── Tab Pipeline ──────────────────────────────────────────────────────

    def _build_pipeline_tab(self, parent):
        left, right = self._build_panel_layout(parent, left_width=220)

        Label(left, text="Lettura invoice da Kraken (ELEC + GAS) in base agli "
                         "identifier configurati nella tab Data Input.",
              bg=BG_CARD, fg=TEXT_SEC, font=("Consolas", 9),
              anchor="w", justify="left", wraplength=190, padx=14, pady=14
              ).pack(fill="x")

        Frame(left, bg=BORDER, height=1).pack(fill="x", padx=14)

        btn_frame = Frame(left, bg=BG_CARD)
        btn_frame.pack(side="bottom", fill="x", padx=14, pady=12)
        self._btn = self._make_btn(btn_frame, "▶  Avvia", self._start)
        self._btn.pack(fill="x")

        self._build_log_panel(right, on_clear=self._clear_log)

    # ── Tab Data Input ───────────────────────────────────────────────────

    def _build_data_input_tab(self, parent):
        hdr = Frame(parent, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(12, 0))
        Label(hdr, text="Data Input  —  Invoice", bg=BG, fg=TEXT_PRI,
              font=("Consolas", 11, "bold")).pack(side="left")
        Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(8, 0))
        Label(parent,
              text="Ogni riga: IDENTIFIER obbligatorio, almeno uno tra IMPORT_SUPPLIER_BILL_ID e AGREEMENT_ID.",
              bg=BG, fg=TEXT_SEC, font=("Consolas", 9), anchor="w", pady=6).pack(fill="x", padx=16)

        toolbar = Frame(parent, bg=BG)
        toolbar.pack(fill="x", padx=16, pady=(0, 6))
        self._make_btn(toolbar, "✏️  Modifica / Aggiungi", self._identifier_paste_popup,
                       color=SUCCESS).pack(side="left", padx=(0, 6))
        self._make_btn(toolbar, "🗑  Svuota righe", self._identifier_clear_all,
                       color=ERROR).pack(side="left")

        cols = ("identifier", "sap_plan_id", "agreement_id")
        table_frame = Frame(parent, bg=BG_CARD,
                            highlightthickness=1, highlightbackground=BORDER)
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        style = ttk.Style()
        style.configure("Input.Treeview",
                        background=BG_CARD, foreground=TEXT_PRI,
                        fieldbackground=BG_CARD, rowheight=26,
                        font=("Consolas", 10), borderwidth=0)
        style.configure("Input.Treeview.Heading",
                        background=BG_CARD2, foreground=ACCENT,
                        font=("Consolas", 9, "bold"), relief="flat")
        style.map("Input.Treeview",
                  background=[("selected", ACCENT2)],
                  foreground=[("selected", TEXT_PRI)])

        self._id_tree = ttk.Treeview(table_frame, columns=cols,
                                     show="headings", style="Input.Treeview",
                                     selectmode="browse")
        self._id_tree.heading("identifier",   text="Identifier")
        self._id_tree.heading("sap_plan_id",  text="Import Supplier Bill ID")
        self._id_tree.heading("agreement_id", text="Agreement ID")
        self._id_tree.column("identifier",   width=260, minwidth=120, anchor="w")
        self._id_tree.column("sap_plan_id",  width=220, minwidth=100, anchor="w")
        self._id_tree.column("agreement_id", width=180, minwidth=80,  anchor="w")

        vsb = ttk.Scrollbar(table_frame, orient="vertical",
                            command=self._id_tree.yview,
                            style="Dark.Vertical.TScrollbar")
        def _id_scroll(f, l):
            if float(f) <= 0.0 and float(l) >= 1.0:
                if vsb.winfo_ismapped():
                    vsb.after(1, vsb.pack_forget)
            else:
                if not vsb.winfo_ismapped():
                    vsb.after(1, lambda: vsb.pack(side="right", fill="y", before=self._id_tree))
            vsb.set(f, l)
        vsb.pack(side="right", fill="y")
        self._id_tree.configure(yscrollcommand=_id_scroll)
        self._id_tree.pack(fill="both", expand=True)

        footer = Frame(parent, bg=BG)
        footer.pack(fill="x", padx=16, pady=(0, 4))
        self._id_count_var = tkinter.StringVar(value="")
        Label(footer, textvariable=self._id_count_var,
              bg=BG, fg=TEXT_SEC, font=("Consolas", 9)).pack(side="left")

    # ── Identifier ────────────────────────────────────────────────────────

    def _identifier_paste_popup(self):
        """Popup per modificare la lista invoice: IDENTIFIER;IMPORT_SUPPLIER_BILL_ID;AGREEMENT_ID."""
        popup = tkinter.Toplevel(self)
        popup.title("Modifica / Aggiungi righe")
        popup.configure(bg=BG)
        popup.grab_set()
        popup.update_idletasks()
        W, H = 700, 520
        x = (popup.winfo_screenwidth()  - W) // 2
        y = (popup.winfo_screenheight() - H) // 2
        popup.geometry(f"{W}x{H}+{x}+{y}")

        Label(popup,
              text="Formato: IDENTIFIER ; IMPORT_SUPPLIER_BILL_ID ; AGREEMENT_ID\n"
                   "IDENTIFIER obbligatorio (EB.../GB...) — esattamente uno tra IMPORT_SUPPLIER_BILL_ID e AGREEMENT_ID.",
              bg=BG, fg=TEXT_SEC, font=("Consolas", 9), justify="left",
              anchor="w", pady=8).pack(fill="x", padx=16)
        Frame(popup, bg=BORDER, height=1).pack(fill="x", padx=16)

        txt = tkinter.Text(popup, bg=BG_INPUT, fg=TEXT_PRI, insertbackground=TEXT_PRI,
                           relief="flat", font=("Consolas", 10), wrap="none",
                           padx=8, pady=8, undo=True)
        txt.pack(fill="both", expand=True, padx=16, pady=10)
        txt.tag_configure("invalid", foreground=WARNING, background="#2a1f00")

        for iid in self._id_tree.get_children():
            vals = self._id_tree.item(iid, "values")
            if vals:
                txt.insert("end", ";".join(vals) + "\n")
        txt.focus_set()

        feedback_var = tkinter.StringVar(value="")
        feedback_lbl = Label(popup, textvariable=feedback_var, bg=BG, fg=TEXT_SEC,
                             font=("Consolas", 9), anchor="w")
        feedback_lbl.pack(fill="x", padx=16)

        btn_row = Frame(popup, bg=BG)
        btn_row.pack(fill="x", padx=16, pady=(0, 12))

        def _save():
            raw = txt.get("1.0", tkinter.END).strip().splitlines()
            txt.tag_remove("invalid", "1.0", "end")
            valid_rows = []
            invalid_lines = []
            seen_identifiers: dict = {}  # identifier -> prima riga (1-based)

            for i, line in enumerate(raw):
                line_s = line.strip()
                if not line_s:
                    continue
                parts = [p.strip() for p in line_s.split(";")]
                identifier = parts[0] if len(parts) >= 1 else ""
                sap_plan   = parts[1] if len(parts) >= 2 else ""
                agreement  = parts[2] if len(parts) >= 3 else ""
                line_no = i + 1

                ok = True
                if not identifier:
                    ok = False
                elif not identifier.upper().startswith(("EB", "GB")):
                    ok = False
                elif not sap_plan and not agreement:
                    ok = False  # nessuno dei due
                elif sap_plan and agreement:
                    ok = False  # entrambi presenti: solo uno è ammesso

                if not ok:
                    invalid_lines.append(line_no)
                    txt.tag_add("invalid", f"{line_no}.0", f"{line_no}.end")
                    continue

                # Controlla duplicato
                if identifier in seen_identifiers:
                    # Evidenzia la riga corrente e la prima occorrenza
                    txt.tag_add("invalid", f"{line_no}.0", f"{line_no}.end")
                    if line_no not in invalid_lines:
                        invalid_lines.append(line_no)
                    first = seen_identifiers[identifier]
                    txt.tag_add("invalid", f"{first}.0", f"{first}.end")
                    if first not in invalid_lines:
                        invalid_lines.append(first)
                    # Rimuovi dalla valid_rows la prima occorrenza
                    valid_rows = [(id_, s, a) for id_, s, a in valid_rows if id_ != identifier]
                else:
                    seen_identifiers[identifier] = line_no
                    valid_rows.append((identifier, sap_plan, agreement))

            if not valid_rows and not invalid_lines:
                feedback_var.set("⚠  Nessuna riga trovata.")
                feedback_lbl.config(fg=WARNING)
                return
            if invalid_lines:
                feedback_var.set(
                    f"⚠  {len(invalid_lines)} riga/e non valida/e evidenziate in giallo — "
                    "correggi e riprova.  "
                    "(IDENTIFIER: prefisso EB/GB, nessun duplicato, "
                    "esattamente uno tra IMPORT_SUPPLIER_BILL_ID e AGREEMENT_ID)")
                feedback_lbl.config(fg=WARNING)
                return

            self._id_tree.delete(*self._id_tree.get_children())
            for r in valid_rows:
                self._id_tree.insert("", "end", values=r)
            self._id_count_var.set(f"{len(valid_rows)} righe.")
            self._save_identifier_input()
            popup.destroy()

        tkinter.Button(btn_row, text="✔  Salva", command=_save,
                       bg=BG_CARD, fg=ACCENT, font=("Consolas", 10, "bold"),
                       relief="flat", cursor="hand2", padx=10, pady=4,
                       activebackground=BG_HOVER, activeforeground=TEXT_PRI,
                       bd=0).pack(side="left", padx=(0, 8))
        tkinter.Button(btn_row, text="✕  Annulla", command=popup.destroy,
                       bg=BG_CARD, fg=TEXT_SEC, font=("Consolas", 10, "bold"),
                       relief="flat", cursor="hand2", padx=10, pady=4,
                       activebackground=BG_HOVER, activeforeground=TEXT_PRI,
                       bd=0).pack(side="left")

    def _identifier_clear_all(self):
        if not self._id_tree.get_children():
            return
        if messagebox.askyesno("Svuota righe", "Sei sicuro di voler rimuovere tutte le righe?"):
            self._id_tree.delete(*self._id_tree.get_children())
            self._id_count_var.set("0 righe.")
            self._save_identifier_input()

    def _save_identifier_input(self):
        rows = []
        for iid in self._id_tree.get_children():
            vals = self._id_tree.item(iid, "values")
            if vals:
                rows.append(";".join(vals))
        try:
            _IW_INPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
            header = "IDENTIFIER;IMPORT_SUPPLIER_BILL_ID;AGREEMENT_ID\n"
            content = header + ("\n".join(rows) + "\n" if rows else "")
            _IW_INPUT_FILE.write_text(content, encoding="utf-8")
            self._status_var.set(f"✓ data_input.csv salvato ({len(rows)} righe).")
        except Exception as e:
            messagebox.showerror("Errore salvataggio", str(e))

    def _load_identifier_into_table(self):
        for row in self._id_tree.get_children():
            self._id_tree.delete(row)
        if not _IW_INPUT_FILE.exists():
            self._id_count_var.set("File non trovato — verrà creato al salvataggio.")
            return
        try:
            with open(_IW_INPUT_FILE, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                count = 0
                for row in reader:
                    identifier = row.get("IDENTIFIER", "").strip()
                    if not identifier:
                        continue
                    sap_plan  = row.get("IMPORT_SUPPLIER_BILL_ID", "").strip()
                    agreement = row.get("AGREEMENT_ID", "").strip()
                    self._id_tree.insert("", "end", values=(identifier, sap_plan, agreement))
                    count += 1
            self._id_count_var.set(f"{count} righe caricate.")
        except Exception as e:
            self._id_count_var.set(f"Errore lettura: {e}")

    def _start(self):
        if self._running:
            return
        if not self._id_tree.get_children():
            messagebox.showwarning("Nessun identifier",
                                   "Aggiungi almeno un document identifier prima di avviare.")
            return
        self._running = True
        self._btn.configure(fg=TEXT_SEC, cursor="arrow")
        self._status_var.set("Esecuzione in corso...")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        import logging as _logging

        class _QueueHandler(_logging.Handler):
            def __init__(self, q):
                super().__init__()
                self._q = q
            def emit(self, record):
                msg = self.format(record)
                tag = "error" if record.levelno >= _logging.ERROR else (
                      "warn" if record.levelno >= _logging.WARNING else "info")
                self._q.put((msg, tag))

        try:
            handler = _QueueHandler(self._log_queue)
            handler.setFormatter(_logging.Formatter("%(message)s"))
            log.addHandler(handler)
            try:
                main()
            finally:
                log.removeHandler(handler)
            self.after(0, self._done, True)
        except Exception as e:
            self._enqueue_log(f"[ERRORE] {e}", "error")
            self.after(0, self._done, False)

    def _done(self, ok):
        self._running = False
        self._btn.configure(fg=ACCENT, cursor="hand2")
        self._status_var.set("✓ Completato." if ok else "✗ Errore durante l'esecuzione.")


class CsvBlankHeaderRemover(_AppBase):

    def __init__(self, master):
        super().__init__(master, bg=BG)
        self._log_queue   = queue.Queue()
        self._running     = False
        self._files_data  = []
        self._build_ui()
        self._load_into_list()
        self._update_btn_state()
        self._poll_log()

    def _build_ui(self):
        self._status_var = tkinter.StringVar(value="Pronto.")
        Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, side="bottom")
        self._status_lbl = Label(self, textvariable=self._status_var, bg=BG, fg=TEXT_SEC,
                                  font=("Consolas", 9), anchor="w", pady=5)
        self._status_lbl.pack(fill="x", padx=24, side="bottom")

        body = Frame(self, bg=BG, highlightthickness=1, highlightbackground=BORDER)
        body.pack(fill="both", expand=True, padx=24, pady=(12, 0))

        paned = tkinter.PanedWindow(body, orient="vertical", bg=BORDER,
                                    sashwidth=5, sashrelief="flat", bd=0)
        paned.pack(fill="both", expand=True)

        # ── Pannello superiore: lista file ────────────────────────────────
        top = Frame(paned, bg=BG_CARD, bd=0, highlightthickness=1,
                    highlightbackground=BORDER)

        hdr = Frame(top, bg=BG_CARD)
        hdr.pack(fill="x")
        Label(hdr, text="FILE", bg=BG_CARD, fg=TEXT_SEC,
              font=("Consolas", 9, "bold"), pady=10, padx=14).pack(side="left")

        def _icon_btn(symbol, command, color=ACCENT, tip=""):
            lbl = Label(hdr, text=symbol, bg=BG_CARD, fg=color,
                        font=("Consolas", 14), cursor="hand2", padx=10, pady=6)
            lbl.bind("<Button-1>", lambda e: command())
            lbl.bind("<Enter>",    lambda e: (lbl.configure(bg=BG_HOVER),
                                              self._status_var.set(tip) if tip else None))
            lbl.bind("<Leave>",    lambda e: (lbl.configure(bg=BG_CARD),
                                              self._status_var.set("Pronto.")))
            return lbl

        _icon_btn("🗑", self._remove_all,    ERROR,   "Rimuovi tutto").pack(side="right", padx=(0, 4))
        _icon_btn("+",  self._browse_files,  SUCCESS, "Aggiungi file").pack(side="right", padx=(0, 4))
        self._btn = _icon_btn("▶", self._start, ACCENT, "Avvia rimozione header")
        self._btn.pack(side="right", padx=(0, 8))
        Frame(top, bg=BORDER, height=1).pack(fill="x", padx=14)

        # Canvas scrollabile
        canvas_frame = Frame(top, bg=BG_CARD)
        canvas_frame.pack(fill="both", expand=True, padx=6, pady=6)
        self._cbr_vsb = ttk.Scrollbar(canvas_frame, style="Dark.Vertical.TScrollbar")
        self._cbr_vsb.pack(side="right", fill="y")
        self._cbr_canvas = tkinter.Canvas(canvas_frame, bg=BG_CARD,
                                          highlightthickness=0,
                                          yscrollcommand=self._cbr_vsb.set)
        self._cbr_canvas.pack(side="left", fill="both", expand=True)
        self._cbr_vsb.config(command=self._cbr_canvas.yview)
        self._cbr_inner = Frame(self._cbr_canvas, bg=BG_CARD)
        self._cbr_win = self._cbr_canvas.create_window(
            (0, 0), window=self._cbr_inner, anchor="nw")
        self._cbr_inner.bind("<Configure>", self._cbr_update_scroll)
        self._cbr_canvas.bind("<Configure>", lambda e: (
            self._cbr_canvas.itemconfig(self._cbr_win, width=e.width),
            self._cbr_update_scroll()
        ))
        self._cbr_canvas.bind("<Enter>", lambda e: self._cbr_canvas.bind_all(
            "<MouseWheel>", lambda e: self._cbr_canvas.yview_scroll(
                -1*(e.delta//120), "units")))
        self._cbr_canvas.bind("<Leave>", lambda e: self._cbr_canvas.unbind_all("<MouseWheel>"))

        paned.add(top, minsize=80, height=180, stretch="never")

        # ── Pannello inferiore: log ───────────────────────────────────────
        bottom = Frame(paned, bg=BG_CARD, bd=0, highlightthickness=1,
                       highlightbackground=BORDER)
        self._build_log_panel(bottom, on_clear=self._clear_log)
        paned.add(bottom, minsize=100, stretch="always")

    def _cbr_update_scroll(self, _e=None):
        self._cbr_canvas.update_idletasks()
        content_h = self._cbr_inner.winfo_reqheight()
        canvas_h  = self._cbr_canvas.winfo_height()
        if content_h > canvas_h:
            if not self._cbr_vsb.winfo_ismapped():
                self._cbr_vsb.pack(side="right", fill="y")
            self._cbr_canvas.configure(scrollregion=(0, 0, 0, content_h))
        else:
            if self._cbr_vsb.winfo_ismapped():
                self._cbr_vsb.pack_forget()
            self._cbr_canvas.configure(scrollregion=(0, 0, 0, canvas_h))
            self._cbr_canvas.yview_moveto(0)

    # ── Lista file ────────────────────────────────────────────────────────

    def _load_into_list(self):
        raw = _CBR_TXT.read_text(encoding="utf-8") if _CBR_TXT.exists() else ""
        self._files_data = [l.strip() for l in raw.splitlines() if l.strip()]
        self._redraw_files()

    def _redraw_files(self):
        for w in self._cbr_inner.winfo_children():
            w.destroy()
        for path in self._files_data:
            row = Frame(self._cbr_inner, bg=BG_CARD)
            row.pack(fill="x", padx=6, pady=1)
            x_lbl = Label(row, text="✕", bg=BG_CARD, fg=ERROR,
                          font=("Consolas", 10, "bold"), cursor="hand2",
                          padx=8, pady=4)
            x_lbl.pack(side="left")
            x_lbl.bind("<Button-1>", lambda e, p=path: self._remove_by_path(p))
            x_lbl.bind("<Enter>",    lambda e, l=x_lbl: l.configure(bg=BG_HOVER))
            x_lbl.bind("<Leave>",    lambda e, l=x_lbl: l.configure(bg=BG_CARD))
            Label(row, text=path, bg=BG_CARD, fg=TEXT_PRI,
                  font=("Consolas", 10), anchor="w", pady=4).pack(
                  side="left", fill="x", expand=True)
            Frame(self._cbr_inner, bg=BORDER, height=1).pack(fill="x", padx=6)
        self._update_btn_state()
        self._cbr_update_scroll()

    def _remove_by_path(self, path):
        if path in self._files_data:
            self._files_data.remove(path)
            self._save_and_reload()

    def _remove_all(self):
        if not self._files_data:
            return
        if not messagebox.askyesno("Rimuovi tutto", "Rimuovere tutti i file dalla lista?"):
            return
        self._files_data.clear()
        self._save_and_reload()

    def _save_and_reload(self):
        try:
            _CBR_TXT.parent.mkdir(parents=True, exist_ok=True)
            _CBR_TXT.write_text("\n".join(self._files_data), encoding="utf-8")
            self._status_var.set("✓ files.txt salvato.")
        except Exception as e:
            messagebox.showerror("Errore salvataggio", str(e))
        self._redraw_files()

    def _browse_files(self):
        paths = filedialog.askopenfilenames(
            title="Seleziona file CSV o TXT",
            filetypes=[("CSV e TXT", "*.csv *.txt"), ("Tutti i file", "*.*")]
        )
        if not paths:
            return
        existing = set(self._files_data)
        added = [p for p in paths if p not in existing]
        skipped = len(paths) - len(added)
        if added:
            self._files_data.extend(added)
            self._save_and_reload()
        if skipped:
            self._warn_status(f"⚠ {skipped} file già presenti ignorati.")

    def _update_btn_state(self):
        has = bool(self._files_data)
        self._btn.configure(fg=ACCENT if has else TEXT_SEC,
                            cursor="hand2" if has else "arrow")

    # ── Pipeline ──────────────────────────────────────────────────────────

    def _on_done(self, success: bool):
        self._running = False
        self._status_var.set("✓ Completato." if success else "✗ Terminato con errori.")
        self._btn.configure(fg=SUCCESS if success else ERROR, cursor="hand2")
        self.after(3000, self._update_btn_state)

    def _start(self):
        if self._running or not self._files_data:
            return
        self._running = True
        self._btn.configure(fg=TEXT_SEC, cursor="arrow")
        self._status_var.set("In esecuzione...")
        threading.Thread(
            target=csv_blank_header_run_pipeline,
            args=(list(self._files_data), self._enqueue_log, self._on_done),
            daemon=True,
        ).start()


# ════════════════════════════════════════════════════════════════════════════
# JIRA TICKET CREATOR
# ════════════════════════════════════════════════════════════════════════════

import json as _json_mod

_JIRA_DIR           = _HERE / "input" / "jira ticket"
_JIRA_TEMPLATE_FILE = _JIRA_DIR / "jira_templates.json"
_JIRA_VERIFY_SSL    = False



def _jira_load_templates() -> dict:
    if not _JIRA_TEMPLATE_FILE.exists():
        return {}
    try:
        return _json_mod.loads(_JIRA_TEMPLATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _jira_save_templates(templates: dict):
    _JIRA_DIR.mkdir(parents=True, exist_ok=True)
    _JIRA_TEMPLATE_FILE.write_text(
        _json_mod.dumps(templates, indent=2, ensure_ascii=False), encoding="utf-8")



_JIRA_TARGET_DIRS = {
    "KCC":       "/interface/PE1/500/FICA/KR_CUSTOMERS/entr\u00e9e/",
    "Piani":     "/interface/PE1/500/FICA/PIANI_AFB_KRAKEN/entr\u00e9e/",
    "KR":        "/interface/PE1/500/FICA/INVOICE_KRAKEN/entr\u00e8e/KR",
    "KF":        "/interface/PE1/500/FICA/INVOICE_KRAKEN/entr\u00e8e/KF",
    "KM":        "/interface/PE1/500/FICA/INVOICE_KRAKEN/entr\u00e8e/KM",
    "KK":        "/interface/PE1/500/FICA/INVOICE_KRAKEN/entr\u00e8e/KK",
    "Pagamenti": "/interface/PE1/500/FICA/ACCOUNTING_KRAKEN/entr\u00e9e/",
}


def _jira_detect_file_type(filename):
    n = filename.upper()
    if n.startswith("K_C_C_") or n.startswith("K_C_U_"):
        return "KCC"
    if n.startswith("KF_"):
        return "KF"
    if n.startswith("KR_"):
        return "KR"
    if n.startswith("KM_"):
        return "KM"
    if n.startswith("KK_"):
        return "KK"
    if n.startswith("KE_PP_") or n.startswith("KG_PP_"):
        return "Piani"
    if n.startswith("KE_") or n.startswith("KG_"):
        return "Pagamenti"
    return None


def _jira_validate_zip_structure(all_entries):
    """
    Valida che lo ZIP segua una catena lineare.
    - Nessuna cartella vuota
    - Ad ogni livello: solo file OPPURE solo una sottocartella, mai entrambi, mai più di una
    Ritorna (leaf_files, errore). leaf_files = lista di nomi file (basename).
    """
    import os as _os
    from collections import defaultdict

    files = [n for n in all_entries if not n.endswith("/")]
    dirs  = [n.rstrip("/") for n in all_entries if n.endswith("/")]

    if not files and not dirs:
        return None, "archivio vuoto."

    # Costruisci l'albero includendo sia file che directory esplicite
    dir_children = defaultdict(lambda: {"files": [], "subdirs": set()})

    # Aggiungi directory esplicite all'albero
    for d in dirs:
        parts = d.split("/")
        for i in range(len(parts)):
            parent = "/".join(parts[:i]) if i > 0 else ""
            dir_children[parent]["subdirs"].add(parts[i])

    # Aggiungi file all'albero
    for f in files:
        parts = f.split("/")
        for i in range(len(parts)):
            parent = "/".join(parts[:i]) if i > 0 else ""
            if i == len(parts) - 1:
                dir_children[parent]["files"].append(parts[i])
            else:
                dir_children[parent]["subdirs"].add(parts[i])

    # Valida ogni nodo
    for dir_path, ch in dir_children.items():
        label = f"'{dir_path.split('/')[-1]}'" if dir_path else "root"

        if ch["files"] and ch["subdirs"]:
            return None, (f"cartella {label} contiene sia file che "
                          f"sottocartelle — struttura non valida.")

        if len(ch["subdirs"]) > 1:
            return None, (f"cartella {label} contiene più sottocartelle "
                          f"({', '.join(sorted(ch['subdirs']))}) — "
                          f"ammessa una sola per livello.")

        if ch["subdirs"] and not ch["files"]:
            # Ha una sottocartella — ok, è un nodo intermedio
            pass

        if not ch["files"] and not ch["subdirs"]:
            # Cartella vuota esplicita
            return None, f"cartella vuota trovata: {label}"

    # Controlla cartelle esplicite senza figli nell'albero
    for d in dirs:
        d_clean = d.rstrip("/")
        ch = dir_children.get(d_clean, {"files": [], "subdirs": set()})
        if not ch["files"] and not ch["subdirs"]:
            label = d_clean.split("/")[-1]
            return None, f"cartella vuota trovata: '{label}'"

    if not files:
        return None, "nessun file trovato nell'archivio."

    # Verifica struttura root
    root_files  = [n for n in files if "/" not in n]
    nested_files = [n for n in files if "/" in n]

    if root_files and nested_files:
        return None, "struttura mista — file sia a root che in cartelle."

    leaf_names = [_os.path.basename(f) for f in files]
    return leaf_names, None


def _jira_build_cfg(key, zip_paths, jira_env="PROD"):
    """Ritorna (cfg_content, errore). errore è None se tutto ok."""
    import zipfile as _zf, os as _os
    env_code = "CE1" if jira_env == "CHOPIN" else "PE1"
    lines = ["TICKET_JIRA;ZIP_FILE;TARGET_DIR"]

    for zip_path in zip_paths:
        zip_name = _os.path.basename(zip_path)
        try:
            with _zf.ZipFile(zip_path, "r") as z:
                all_entries = z.namelist()
        except Exception as e:
            return None, f"Impossibile leggere {zip_name}: {e}"

        leaf_files, err = _jira_validate_zip_structure(all_entries)
        if err:
            return None, f"{zip_name}: {err}"

        # Tutti devono essere .csv
        non_csv = [n for n in leaf_files if not n.lower().endswith(".csv")]
        if non_csv:
            return None, (f"{zip_name}: file non .csv trovati: "
                          f"{', '.join(non_csv[:3])}"
                          f"{'...' if len(non_csv) > 3 else ''}")

        # Rileva tipo
        types = {_jira_detect_file_type(n) for n in leaf_files}
        types.discard(None)
        if not types:
            return None, f"{zip_name}: nessun file riconosciuto all'interno."
        if len(types) > 1:
            return None, (f"{zip_name}: tipi misti trovati ({', '.join(sorted(types))}) — "
                          f"ogni ZIP deve contenere una sola tipologia.")

        tipo   = next(iter(types))
        target = _JIRA_TARGET_DIRS[tipo].replace("PE1", env_code)
        lines.append(f"{key};{zip_name};{target}")

    return "\n".join(lines), None


class JiraTicketCreator(_AppBase):

    def __init__(self, master):
        super().__init__(master, bg=BG)
        self._log_queue = queue.Queue()
        self._running   = False
        self._allegati  = []
        self._build_ui()
        self._load_saved()
        self._poll_log()

    # ── Costruzione UI ───────────────────────────────────────────────────

    def _build_ui(self):
        self._status_var = tkinter.StringVar(value="Pronto.")
        Frame(self, bg=BORDER, height=1).pack(fill="x", padx=12, side="bottom")
        self._status_lbl = Label(self, textvariable=self._status_var,
                                 bg=BG, fg=TEXT_SEC, font=("Consolas", 9),
                                 anchor="w", pady=5)
        self._status_lbl.pack(fill="x", padx=12, side="bottom")

        body = tkinter.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=(10, 19), pady=(4, 4))

        paned = tkinter.PanedWindow(body, orient="horizontal", bg=BORDER,
                                    sashwidth=5, sashrelief="flat", bd=0)
        paned.pack(fill="both", expand=True)

        # ── Form (sinistra, scrollabile) ──────────────────────────────────
        left = tkinter.Frame(paned, bg=BG)
        canvas, inner = self._jira_scrollable(left)
        self._build_auth_content(inner)
        self._build_ticket_content(inner)
        paned.add(left, stretch="always", minsize=400)

        # ── Log (destra, ridimensionabile) ───────────────────────────────
        right = tkinter.Frame(paned, bg=BG_CARD, bd=0,
                              highlightthickness=1, highlightbackground=BORDER)
        self._build_log_panel(right, on_clear=self._clear_log)
        paned.add(right, stretch="never", minsize=160)

        self.after(100, lambda: paned.sash_place(0, int(paned.winfo_width() * 0.68), 0))

    def _build_single_view(self):
        pass  # non usato

    # ── Autenticazione ────────────────────────────────────────────────────

    def _build_auth_tab(self, parent):
        canvas, inner = self._jira_scrollable(parent)
        self._build_auth_content(inner)

    def _build_auth_content(self, inner):
        """Inizializza le variabili di autenticazione dal .env — UI gestita da Impostazioni."""
        self._url_var         = tkinter.StringVar()
        self._username_var    = tkinter.StringVar()
        self._password_var    = tkinter.StringVar()
        self._test_result_var = tkinter.StringVar(value="")
        self._load_saved()

    # ── Tab Crea Ticket ───────────────────────────────────────────────────

    def _build_ticket_tab(self, parent):
        canvas, inner = self._jira_scrollable(parent)
        self._build_ticket_content(inner)

    def _make_dropdown(self, parent, var, get_vals):
        """Dropdown filtrabile: campo di testo + lista filtrata dinamicamente."""
        frame = Frame(parent, bg=BG_INPUT, highlightthickness=1,
                      highlightbackground=BORDER, cursor="hand2")
        lbl = Label(frame, textvariable=var, bg=BG_INPUT, fg=TEXT_PRI,
                    font=("Consolas", 10), anchor="w", padx=8, pady=4)
        lbl.pack(side="left", fill="x", expand=True)
        arr = Label(frame, text="▾", bg=BG_INPUT, fg=TEXT_SEC,
                    font=("Consolas", 10), padx=6)
        arr.pack(side="right")

        def _open(e=None):
            vals = get_vals()
            if not vals:
                return

            popup = tkinter.Toplevel(frame)
            popup.wm_overrideredirect(True)
            popup.configure(bg=BORDER)

            # Posiziona sotto il frame
            fx = frame.winfo_rootx()
            fy = frame.winfo_rooty() + frame.winfo_height()
            fw = max(frame.winfo_width(), 200)
            popup.geometry(f"{fw}x220+{fx}+{fy}")

            # Campo di ricerca
            search_var = tkinter.StringVar()
            search = tkinter.Entry(popup, textvariable=search_var,
                                   bg=BG_INPUT, fg=TEXT_PRI,
                                   insertbackground=TEXT_PRI,
                                   relief="flat", font=("Consolas", 10),
                                   highlightthickness=0)
            search.pack(fill="x", padx=1, pady=1, ipady=5)
            search.focus_set()

            Frame(popup, bg=BORDER, height=1).pack(fill="x")

            # Listbox
            lb_frame = Frame(popup, bg=BG_CARD)
            lb_frame.pack(fill="both", expand=True, padx=1, pady=(0, 1))

            sb = tkinter.Scrollbar(lb_frame, orient="vertical")
            lb = tkinter.Listbox(lb_frame, bg=BG_CARD, fg=TEXT_PRI,
                                 selectbackground=ACCENT2,
                                 selectforeground=TEXT_PRI,
                                 font=("Consolas", 10), relief="flat",
                                 bd=0, highlightthickness=0,
                                 activestyle="none",
                                 yscrollcommand=sb.set)
            sb.configure(command=lb.yview)
            sb.pack(side="right", fill="y")
            lb.pack(side="left", fill="both", expand=True)

            def _populate(filter_txt=""):
                lb.delete(0, tkinter.END)
                for v in vals:
                    if filter_txt.lower() in v.lower():
                        lb.insert(tkinter.END, v)

            _populate()

            def _on_search(*_):
                _populate(search_var.get())

            def _select(e=None):
                sel = lb.curselection()
                if sel:
                    var.set(lb.get(sel[0]))
                popup.destroy()

            def _on_key(e):
                if e.keysym == "Down":
                    lb.focus_set()
                    if lb.size() > 0:
                        lb.selection_set(0)
                        lb.activate(0)
                elif e.keysym == "Return":
                    _select()
                elif e.keysym == "Escape":
                    popup.destroy()

            search_var.trace_add("write", _on_search)
            search.bind("<Key>", _on_key)
            lb.bind("<Return>", _select)
            lb.bind("<Double-Button-1>", _select)
            lb.bind("<Escape>", lambda e: popup.destroy())
            popup.bind("<FocusOut>", lambda e: popup.destroy() if popup.focus_get() not in (search, lb) else None)

        for w in (frame, lbl, arr):
            w.bind("<Button-1>", _open)
        return frame

    def _on_importa(self):
        """Apre il popup di importazione da ticket esistente."""
        popup = tkinter.Toplevel(self)
        popup.title("Importa da ticket")
        popup.configure(bg=BG)
        popup.grab_set()
        W, H = 420, 120
        x = (popup.winfo_screenwidth() - W) // 2
        y = (popup.winfo_screenheight() - H) // 2
        popup.geometry(f"{W}x{H}+{x}+{y}")
        Label(popup, text="Chiave ticket o URL:", bg=BG, fg=TEXT_SEC,
              font=("Consolas", 9), anchor="w").pack(fill="x", padx=16, pady=(14, 4))
        if not hasattr(self, "_import_var"):
            self._import_var = tkinter.StringVar()
        row = Frame(popup, bg=BG)
        row.pack(fill="x", padx=16)
        tkinter.Entry(row, textvariable=self._import_var, bg=BG_INPUT, fg=TEXT_PRI,
                      insertbackground=TEXT_PRI, relief="flat",
                      font=("Consolas", 10),
                      highlightthickness=1, highlightbackground=BORDER
                      ).pack(side="left", fill="x", expand=True, ipady=4)
        def _carica():
            popup.destroy()
            self._on_import()
        self._make_btn(row, "📋 Carica", _carica).pack(side="left", padx=(8, 0))

    def _open_template_menu(self):
        """Popup template: dropdown in alto, preview sotto, bottone Usa."""
        templates = _jira_load_templates()

        if not templates:
            messagebox.showinfo("Nessun template",
                                "Non ci sono template salvati.\n\n"
                                "Compila i campi e premi 💾 Salva Template per crearne uno.")
            return

        popup = tkinter.Toplevel(self)
        popup.title("Template")
        popup.configure(bg=BG)
        popup.grab_set()
        W, H = 500, 360
        x = (popup.winfo_screenwidth() - W) // 2
        y = (popup.winfo_screenheight() - H) // 2
        popup.geometry(f"{W}x{H}+{x}+{y}")
        popup.resizable(True, True)
        popup.minsize(400, 300)

        # Header
        hdr = Frame(popup, bg=BG_CARD2)
        hdr.pack(fill="x")
        Label(hdr, text="📄  Template", bg=BG_CARD2, fg=TEXT_PRI,
              font=("Consolas", 10, "bold"), pady=10, padx=16).pack(side="left")
        self._make_btn(hdr, "✔  Usa questo template",
                       lambda: _apply(), color=SUCCESS).pack(side="right", padx=12, pady=6)
        Frame(popup, bg=BORDER, height=1).pack(fill="x")

        body = Frame(popup, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # Dropdown selezione template
        sel_row = Frame(body, bg=BG)
        sel_row.pack(fill="x", pady=(0, 10))
        Label(sel_row, text="Template:", bg=BG, fg=TEXT_SEC,
              font=("Consolas", 9), width=10, anchor="w").pack(side="left")

        keys = list(templates.keys())
        sel_var = tkinter.StringVar(value=keys[0] if keys else "")

        import tkinter.ttk as _ttk
        combo = _ttk.Combobox(sel_row, textvariable=sel_var, values=keys,
                               state="readonly", font=("Consolas", 10))
        combo.pack(side="left", fill="x", expand=True, padx=(0, 8))

        del_btn = self._make_btn(sel_row, "🗑", lambda: _delete(), color=ERROR)
        del_btn.pack(side="left")

        Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(0, 10))

        # Area preview
        preview_frame = Frame(body, bg=BG)
        preview_frame.pack(fill="both", expand=True)

        fields_info = [
            ("Project Key",  "project_key"),
            ("Tipo Issue",   "tipo_issue"),
            ("Priorità",     "priorita"),
            ("Assegnatario", "assegnatario"),
        ]
        field_vars = {}
        for label, key in fields_info:
            row = Frame(preview_frame, bg=BG)
            row.pack(fill="x", pady=2)
            Label(row, text=f"{label}:", bg=BG, fg=TEXT_SEC,
                  font=("Consolas", 9), width=14, anchor="w").pack(side="left")
            v = tkinter.StringVar()
            field_vars[key] = v
            Label(row, textvariable=v, bg=BG, fg=TEXT_PRI,
                  font=("Consolas", 9), anchor="w").pack(side="left")

        Frame(preview_frame, bg=BORDER, height=1).pack(fill="x", pady=(8, 4))
        Label(preview_frame, text="Descrizione:", bg=BG, fg=TEXT_SEC,
              font=("Consolas", 9), anchor="w").pack(fill="x")
        desc_text = tkinter.Text(preview_frame, height=6, bg=BG_INPUT, fg=TEXT_SEC,
                                 font=("Consolas", 9), relief="flat", bd=0,
                                 wrap="word", padx=6, pady=4,
                                 highlightthickness=1, highlightbackground=BORDER,
                                 state="disabled")
        desc_text.pack(fill="both", expand=True, pady=(4, 0))

        def _refresh_preview(*_):
            chiave = sel_var.get()
            t = templates.get(chiave, {})
            for key, var in field_vars.items():
                var.set(t.get(key, "—") or "—")
            desc = t.get("descrizione", "").strip()
            desc_text.configure(state="normal")
            desc_text.delete("1.0", tkinter.END)
            desc_text.insert("1.0", desc)
            desc_text.configure(state="disabled")

        combo.bind("<<ComboboxSelected>>", _refresh_preview)
        if keys:
            _refresh_preview()

        def _delete():
            chiave = sel_var.get()
            if not chiave:
                return
            if not messagebox.askyesno("Elimina", f"Eliminare «{chiave}»?", parent=popup):
                return
            t = _jira_load_templates()
            t.pop(chiave, None)
            _jira_save_templates(t)
            popup.destroy()
            self._open_template_menu()

        def _apply():
            chiave = sel_var.get()
            t = templates.get(chiave, {})
            self._proj_var.set(t.get("project_key", ""))
            self._title_var.set(t.get("title", ""))
            self._tipo_var.set(t.get("tipo_issue", "—"))
            self._prio_var.set(t.get("priorita", "—"))
            self._assegn_var.set(t.get("assegnatario", ""))
            self._desc_text.configure(state="normal")
            self._desc_text.delete("1.0", tkinter.END)
            self._desc_text.insert("1.0", t.get("descrizione", ""))
            if hasattr(self, "_tmpl_var"):
                self._tmpl_var.set(chiave)
            popup.destroy()

        if not keys:
            combo.configure(state="disabled")

    def _load_templates_dict(self) -> dict:
        import json as _json
        if not _JIRA_TMPL.exists():
            return {}
        try:
            return _json.loads(_JIRA_TMPL.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _apply_template_by_name(self, nome: str):
        t = self._load_templates_dict().get(nome, {})
        if not t:
            return
        self._proj_var.set(t.get("project_key", ""))
        self._title_var.set(t.get("title", ""))
        self._tipo_var.set(t.get("tipo", "—"))
        self._prio_var.set(t.get("priorita", "—"))
        self._assegn_var.set(t.get("assegnatario", ""))
        self._desc_text.configure(state="normal")
        self._desc_text.delete("1.0", tkinter.END)
        self._desc_text.insert("1.0", t.get("descrizione", ""))
        if hasattr(self, "_tmpl_var"):
            self._tmpl_var.set(nome)

    def _build_ticket_content(self, inner):

        def _card(parent, icon, title, extra_widgets=None):
            """Crea una card con header stile dark."""
            c = Frame(parent, bg=BG_CARD, highlightthickness=1,
                      highlightbackground=BORDER)
            c.pack(fill="x", padx=10, pady=(0, 0))
            hdr = Frame(c, bg=BG_CARD2)
            hdr.pack(fill="x")
            Label(hdr, text=f"{icon}  {title}", bg=BG_CARD2, fg=TEXT_SEC,
                  font=("Consolas", 9, "bold"), pady=7, padx=12).pack(side="left")
            if extra_widgets:
                extra_widgets(hdr)
            Frame(c, bg=BORDER, height=1).pack(fill="x")
            body = Frame(c, bg=BG_CARD)
            body.pack(fill="x", padx=12, pady=10)
            return body

        # ── Card Dettagli ticket ──────────────────────────────────────────
        def _det_extra(hdr):
            btn_frame = Frame(hdr, bg=BG_CARD2)
            btn_frame.pack(side="right", padx=8)
            self._make_btn(btn_frame, "⬇  Importa", self._on_importa,
                           color=TEXT_SEC).pack(side="left", padx=(0, 4))
            self._make_btn(btn_frame, "📄  Template", self._open_template_menu,
                           color=TEXT_SEC).pack(side="left")

        det_body = _card(inner, "📋", "Dettagli ticket", _det_extra)

        # Project Key + Title
        row1 = Frame(det_body, bg=BG_CARD)
        row1.pack(fill="x", pady=(0, 8))
        row1.columnconfigure(1, weight=1)

        proj_col = Frame(row1, bg=BG_CARD)
        proj_col.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        Label(proj_col, text="Project Key *", bg=BG_CARD, fg=TEXT_SEC,
              font=("Consolas", 9), anchor="w").pack(anchor="w", pady=(0, 3))
        self._proj_var = tkinter.StringVar()
        self._entry_proj = tkinter.Entry(proj_col, textvariable=self._proj_var,
                      bg=BG_INPUT, fg=TEXT_PRI, insertbackground=TEXT_PRI,
                      relief="flat", font=("Consolas", 10), width=10,
                      highlightthickness=1, highlightbackground=BORDER)
        self._entry_proj.pack(fill="x", ipady=4)

        title_col = Frame(row1, bg=BG_CARD)
        title_col.grid(row=0, column=1, sticky="ew")
        Label(title_col, text="Title *", bg=BG_CARD, fg=TEXT_SEC,
              font=("Consolas", 9), anchor="w").pack(anchor="w", pady=(0, 3))
        self._title_var = tkinter.StringVar()
        self._entry_title = tkinter.Entry(title_col, textvariable=self._title_var,
                      bg=BG_INPUT, fg=TEXT_PRI, insertbackground=TEXT_PRI,
                      relief="flat", font=("Consolas", 10),
                      highlightthickness=1, highlightbackground=BORDER)
        self._entry_title.pack(fill="x", ipady=4)

        # Tipo + Priorità + Assegnatario sulla stessa riga
        row2 = Frame(det_body, bg=BG_CARD)
        row2.pack(fill="x")
        row2.columnconfigure(0, weight=1)
        row2.columnconfigure(1, weight=1)
        row2.columnconfigure(2, weight=2)

        # Tipo Issue
        tipo_col = Frame(row2, bg=BG_CARD)
        tipo_col.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        Label(tipo_col, text="Tipo Issue", bg=BG_CARD, fg=TEXT_SEC,
              font=("Consolas", 9), anchor="w").pack(anchor="w", pady=(0, 3))
        self._tipo_var = tkinter.StringVar(value="—")
        self._cb_tipo = self._make_dropdown(tipo_col, self._tipo_var,
                                            lambda: self._cb_tipo_values)
        self._cb_tipo.pack(fill="x")

        # Priorità
        prio_col = Frame(row2, bg=BG_CARD)
        prio_col.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        Label(prio_col, text="Priorità", bg=BG_CARD, fg=TEXT_SEC,
              font=("Consolas", 9), anchor="w").pack(anchor="w", pady=(0, 3))
        self._prio_var = tkinter.StringVar(value="—")
        self._cb_prio = self._make_dropdown(prio_col, self._prio_var,
                                            lambda: self._cb_prio_values)
        self._cb_prio.pack(fill="x")

        # Assegnatario
        assegn_col = Frame(row2, bg=BG_CARD)
        assegn_col.grid(row=0, column=2, sticky="ew")
        assegn_hdr = Frame(assegn_col, bg=BG_CARD)
        assegn_hdr.pack(fill="x", pady=(0, 3))
        Label(assegn_hdr, text="Assegnatario", bg=BG_CARD, fg=TEXT_SEC,
              font=("Consolas", 9), anchor="w").pack(side="left")
        self._assegn_result_var = tkinter.StringVar(value="")
        self._assegn_result_lbl = Label(assegn_hdr, textvariable=self._assegn_result_var,
              bg=BG_CARD, font=("Consolas", 8), anchor="w")
        self._assegn_result_lbl.pack(side="left", padx=(8, 0))

        assegn_row = Frame(assegn_col, bg=BG_CARD)
        assegn_row.pack(fill="x")
        self._assegn_var = tkinter.StringVar()
        self._entry_assegn = tkinter.Entry(assegn_row, textvariable=self._assegn_var,
                      bg=BG_INPUT, fg=TEXT_PRI, insertbackground=TEXT_PRI,
                      relief="flat", font=("Consolas", 10),
                      highlightthickness=1, highlightbackground=BORDER)
        self._entry_assegn.pack(side="left", fill="x", expand=True, ipady=4)
        self._btn_valida_assegn = self._make_btn(assegn_row, "Valida",
                                                  self._on_valida_assegnatario,
                                                  color=TEXT_SEC)
        self._btn_valida_assegn.pack(side="left", padx=(4, 0))
        self._btn_valida_assegn.configure(fg=TEXT_SEC, cursor="arrow")

        def _toggle_valida(*_):
            if self._assegn_var.get().strip():
                self._btn_valida_assegn.configure(fg=ACCENT, cursor="hand2")
            else:
                self._btn_valida_assegn.configure(fg=TEXT_SEC, cursor="arrow")

        self._assegn_var.trace_add("write", _toggle_valida)

        # ── Card Descrizione ──────────────────────────────────────────────
        desc_card = Frame(inner, bg=BG_CARD, highlightthickness=1,
                          highlightbackground=BORDER)
        desc_card.pack(fill="x", padx=10, pady=(10, 0))
        desc_hdr = Frame(desc_card, bg=BG_CARD2)
        desc_hdr.pack(fill="x")
        Label(desc_hdr, text="📝  Descrizione", bg=BG_CARD2, fg=TEXT_SEC,
              font=("Consolas", 9, "bold"), pady=7, padx=12).pack(side="left")
        Frame(desc_card, bg=BORDER, height=1).pack(fill="x")

        self._desc_toolbar = Frame(desc_card, bg=BG_CARD2)
        self._desc_toolbar.pack(fill="x")

        def _tb(text, cmd):
            b = Label(self._desc_toolbar, text=text, bg=BG_CARD2, fg=TEXT_SEC,
                      font=("Consolas", 9, "bold"), cursor="hand2", padx=8, pady=4)
            b.bind("<Button-1>", lambda e: cmd())
            b.bind("<Enter>", lambda e: b.configure(bg=BG_HOVER, fg=TEXT_PRI))
            b.bind("<Leave>", lambda e: b.configure(bg=BG_CARD2, fg=TEXT_SEC))
            b.pack(side="left")

        _tb("\U0001f517 Link", self._fmt_link)
        _tb("B",       lambda: self._fmt_wrap("*", "*"))
        _tb("I",       lambda: self._fmt_wrap("_", "_"))
        _tb("S",       lambda: self._fmt_wrap("-", "-"))
        _tb("{}",      lambda: self._fmt_wrap("{{", "}}"))
        _tb("\u2022 Lista", lambda: self._fmt_prefix("* "))
        _tb("# Lista", lambda: self._fmt_prefix("# "))
        Frame(desc_card, bg=BORDER, height=1).pack(fill="x")

        self._desc_text = tkinter.Text(
            desc_card, height=10, bg=BG_INPUT, fg=TEXT_PRI,
            insertbackground=TEXT_PRI, relief="flat", bd=0,
            font=("Consolas", 10), wrap="word", padx=10, pady=8,
            undo=True, maxundo=-1, selectbackground=ACCENT2)
        self._desc_text.pack(fill="x")
        self._desc_text.bind("<Control-z>",
            lambda e: self._desc_text.edit_undo() or "break")
        self._desc_text.bind("<Control-y>",
            lambda e: self._desc_text.edit_redo() or "break")

        # ── Card Allegati ─────────────────────────────────────────────────
        att_card = Frame(inner, bg=BG_CARD, highlightthickness=1,
                         highlightbackground=BORDER)
        att_card.pack(fill="x", padx=10, pady=(10, 0))
        att_hdr = Frame(att_card, bg=BG_CARD2)
        att_hdr.pack(fill="x")
        Label(att_hdr, text="📎  Allegati", bg=BG_CARD2, fg=TEXT_SEC,
              font=("Consolas", 9, "bold"), pady=7, padx=12).pack(side="left")
        self._att_count_var = tkinter.StringVar(value="")
        Label(att_hdr, textvariable=self._att_count_var, bg=BG_CARD2,
              fg=TEXT_SEC, font=("Consolas", 8)).pack(side="left")
        btn_rm_all = Label(att_hdr, text="✕  Rimuovi tutti", bg=BG_CARD2,
                           fg=ERROR, font=("Consolas", 9), cursor="hand2",
                           padx=10)
        btn_rm_all.pack(side="right")
        btn_rm_all.bind("<Button-1>", lambda e: self._remove_attachments())
        Frame(att_card, bg=BORDER, height=1).pack(fill="x")

        att_body = Frame(att_card, bg=BG)
        att_body.pack(fill="x", padx=12, pady=10)

        drop_zone = Label(att_body,
                          text="\U0001f4c2  Trascina qui i file o clicca per selezionare",
                          bg=BG_INPUT, fg=TEXT_SEC, font=("Consolas", 9),
                          pady=12, cursor="hand2",
                          highlightthickness=1, highlightbackground=BORDER)
        drop_zone.pack(fill="x")
        drop_zone.bind("<Button-1>", lambda e: self._add_attachments())
        if _HAS_DND:
            try:
                drop_zone.drop_target_register(_DND_FILES)
                drop_zone.dnd_bind("<<Drop>>", self._on_dnd_drop)
            except Exception:
                pass

        self._files_frame = Frame(att_body, bg=BG_CARD)
        self._files_frame.pack(fill="x")

        # ── Riga 1: checkbox .cfg + Preview ──────────────────────────────
        cfg_row = Frame(inner, bg=BG)
        cfg_row.pack(fill="x", padx=10, pady=(10, 0))

        cfg_left = Frame(cfg_row, bg=BG)
        cfg_left.pack(side="left")
        self._cfg_var = tkinter.BooleanVar(value=False)
        self._cfg_box = Label(cfg_left, text="\u2610", bg=BG, fg=TEXT_SEC,
                              font=("Consolas", 12), cursor="hand2", width=2)
        self._cfg_box.pack(side="left")
        cfg_lbl = Label(cfg_left, text="Crea file .cfg", bg=BG, fg=TEXT_PRI,
                        font=("Consolas", 9), cursor="hand2")
        cfg_lbl.pack(side="left", padx=(4, 0))

        cfg_right = Frame(cfg_row, bg=BG)
        cfg_right.pack(side="right")
        self._btn_preview_cfg = self._make_btn(cfg_right, "\U0001f441  Preview .cfg",
                                               self._on_debug, color=WARNING)

        # ── Riga 2: Crea Ticket + Salva Template + Pulisci ───────────────
        btn_row = Frame(inner, bg=BG)
        btn_row.pack(fill="x", padx=10, pady=(6, 16))

        btn_right = Frame(btn_row, bg=BG)
        btn_right.pack(side="right")
        self._btn_crea = self._make_btn(btn_right, "\u2714  Crea Ticket", self._on_crea)
        self._btn_crea.pack(side="left")
        self._make_btn(btn_right, "\U0001f4be  Salva Template", self._save_template,
                       color=TEXT_SEC).pack(side="left", padx=(6, 0))
        self._make_btn(btn_right, "\u21ba  Pulisci", self._pulisci,
                       color=TEXT_SEC).pack(side="left", padx=(6, 0))

        def _toggle_cfg(e=None):
            val = not self._cfg_var.get()
            self._cfg_var.set(val)
            self._cfg_box.configure(text="\u2611" if val else "\u2610",
                                    fg=ACCENT if val else TEXT_SEC)
            if val:
                self._btn_preview_cfg.pack(side="right", in_=cfg_right)
                self._cfg_lock_fields()
            else:
                self._btn_preview_cfg.pack_forget()
                self._cfg_unlock_fields()

        self._cfg_box.bind("<Button-1>", _toggle_cfg)
        cfg_lbl.bind("<Button-1>", _toggle_cfg)
        cfg_left.bind("<Button-1>", _toggle_cfg)

    def _cfg_lock_fields(self):
        """Prepopola i campi con valori fissi e li rende non modificabili."""
        from datetime import datetime as _dt
        now = _dt.now()
        data = f"{now.day:02d}/{now.month:02d}"
        desc = (
            "Hi,\n\n\n\n \n\nplease copy the contents of the attached ZIP files "
            "following the configuration defined in the attached "
            "{{<JIRA_TICKET>.cfg}} file.\n\n \n\n\nRegards"
        )
        # Prepopola
        self._proj_var.set("PRD")
        self._title_var.set(f"Accounting- Copy file to entr\u00e9e folder - {data}")
        self._tipo_var.set("T\u00e2che")
        self._prio_var.set("Major [2]")
        self._assegn_var.set("alain.bellon")
        self._desc_text.delete("1.0", tkinter.END)
        self._desc_text.insert("1.0", desc)

        # Blocca Entry
        _dis_bg = BG_CARD2
        for entry in (self._entry_proj, self._entry_title, self._entry_assegn):
            entry.configure(state="disabled", disabledbackground=_dis_bg,
                            disabledforeground=TEXT_SEC)

        # Blocca dropdown — sostituisce il binding con no-op (unbind non è affidabile)
        def _noop(e=None): return "break"
        for dd in (self._cb_tipo, self._cb_prio):
            dd.configure(cursor="arrow")
            dd.bind("<Button-1>", _noop)
            for child in dd.winfo_children():
                child.configure(cursor="arrow")
                child.bind("<Button-1>", _noop)

        # Blocca Text descrizione e nasconde toolbar
        self._desc_text.configure(state="disabled", cursor="arrow",
                                  bg=BG_CARD2)
        for w in self._desc_toolbar.winfo_children():
            w.configure(fg=TEXT_SEC, cursor="arrow")
            w.unbind("<Button-1>")
            w.unbind("<Enter>")
            w.unbind("<Leave>")

        # Blocca bottone Valida assegnatario
        self._btn_valida_assegn.configure(fg=TEXT_SEC, cursor="arrow")
        self._btn_valida_assegn.bind("<Button-1>", lambda e: "break")

    def _cfg_unlock_fields(self):
        """Svuota i campi e li rende nuovamente modificabili."""
        self._proj_var.set("")
        self._title_var.set("")
        self._tipo_var.set("\u2014")
        self._prio_var.set("\u2014")
        self._assegn_var.set("")
        self._assegn_result_var.set("")
        self._desc_text.configure(state="normal", cursor="xterm", bg=BG_INPUT)
        self._desc_text.delete("1.0", tkinter.END)
        for w in self._desc_toolbar.winfo_children():
            label = w.cget("text")
            w.configure(fg=TEXT_SEC, cursor="hand2")
            w.bind("<Enter>", lambda e, b=w: b.configure(bg=BG_HOVER, fg=TEXT_PRI))
            w.bind("<Leave>", lambda e, b=w: b.configure(bg=BG_CARD2, fg=TEXT_SEC))

        # Sblocca Entry
        for entry in (self._entry_proj, self._entry_title, self._entry_assegn):
            entry.configure(state="normal", bg=BG_INPUT, fg=TEXT_PRI)

        # Sblocca dropdown (ripristina binding)
        for dd, var, get_vals in [
            (self._cb_tipo, self._tipo_var, lambda: self._cb_tipo_values),
            (self._cb_prio, self._prio_var, lambda: self._cb_prio_values),
        ]:
            dd.configure(cursor="hand2")
            for child in dd.winfo_children():
                child.configure(cursor="hand2")
            def _make_open(btn, v, gv):
                def _open(e=None):
                    vals = gv()
                    if not vals:
                        return
                    menu = tkinter.Menu(self, tearoff=0, bg=BG_CARD2, fg=TEXT_PRI,
                                        activebackground=ACCENT2,
                                        activeforeground=TEXT_PRI,
                                        font=("Consolas", 10), bd=0, relief="flat")
                    for x in vals:
                        menu.add_command(label=x, command=lambda z=x: v.set(z))
                    menu.post(btn.winfo_rootx(),
                              btn.winfo_rooty() + btn.winfo_height())
                return _open
            _open_fn = _make_open(dd, var, get_vals)
            dd.bind("<Button-1>", _open_fn)
            for child in dd.winfo_children():
                child.bind("<Button-1>", _open_fn)

        # Sblocca bottone Valida assegnatario
        self._btn_valida_assegn.configure(fg=ACCENT, cursor="hand2")
        self._btn_valida_assegn.bind("<Button-1>",
            lambda e: self._on_valida_assegnatario())

    def _build_template_tab(self, parent):
        canvas, inner = self._jira_scrollable(parent)

        card = self._jira_card(inner, "\U0001f4cc  Template salvati")
        row = Frame(card, bg=BG_CARD)
        row.pack(fill="x", pady=(0, 8))
        self._tmpl_var = tkinter.StringVar()
        self._tmpl_cb  = ttk.Combobox(row, textvariable=self._tmpl_var,
                                      state="readonly", style="Jira.TCombobox",
                                      font=("Consolas", 10))
        self._tmpl_cb.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._make_btn(row, "\U0001f4c2  Carica",
                       self._load_template).pack(side="left", padx=(0, 4))
        self._make_btn(row, "\U0001f4be  Salva",
                       self._save_template, color=SUCCESS).pack(side="left", padx=(0, 4))
        self._make_btn(row, "\U0001f5d1  Elimina",
                       self._delete_template, color=ERROR).pack(side="left")

        self._tmpl_preview = Label(card, text="", bg=BG_CARD, fg=TEXT_SEC,
                                   font=("Consolas", 9), anchor="w",
                                   justify="left", wraplength=600)
        self._tmpl_preview.pack(fill="x", pady=(8, 0))
        self._tmpl_cb.bind("<<ComboboxSelected>>",
                           lambda e: self._preview_template())
        self._refresh_templates()
        Frame(inner, bg=BG).pack(pady=12)

    # ── Tab Importa ───────────────────────────────────────────────────────

    def _build_import_tab(self, parent):
        canvas, inner = self._jira_scrollable(parent)

        card = self._jira_card(inner, "\U0001f4e5  Importa da ticket esistente")
        Label(card, text="Chiave o URL ticket (es. PROJ-123)",
              bg=BG_CARD, fg=TEXT_SEC, font=("Consolas", 9),
              anchor="w").pack(fill="x", pady=(0, 4))

        imp_row = Frame(card, bg=BG_INPUT, highlightthickness=1,
                        highlightbackground=BORDER)
        imp_row.pack(fill="x")
        self._import_var = tkinter.StringVar()
        tkinter.Entry(imp_row, textvariable=self._import_var,
                      bg=BG_INPUT, fg=TEXT_PRI, insertbackground=TEXT_PRI,
                      relief="flat", font=("Consolas", 10), bd=0).pack(
                      side="left", fill="x", expand=True, ipady=5, padx=(6, 0))
        self._make_btn(imp_row, "\U0001f4cb  Carica",
                       self._on_import).pack(side="right", padx=2, pady=2)

        Label(card, text="I campi verranno copiati nella tab Crea Ticket.",
              bg=BG_CARD, fg=TEXT_SEC, font=("Consolas", 8),
              anchor="w").pack(fill="x", pady=(8, 0))
        Frame(inner, bg=BG).pack(pady=12)

    # ── Helper UI ─────────────────────────────────────────────────────────

    def _jira_card(self, parent, title):
        outer = Frame(parent, bg=BG)
        outer.pack(fill="x", padx=16, pady=(12, 0))
        Label(outer, text=title, bg=BG, fg=TEXT_SEC,
              font=("Consolas", 9, "bold"), anchor="w").pack(anchor="w", pady=(0, 4))
        card = Frame(outer, bg=BG_CARD, bd=0, highlightthickness=1,
                     highlightbackground=BORDER)
        card.pack(fill="x")
        inner = Frame(card, bg=BG_CARD, padx=16, pady=12)
        inner.pack(fill="x")
        return inner

    def _jira_scrollable(self, parent):
        canvas = tkinter.Canvas(parent, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview,
                            style="Dark.Vertical.TScrollbar")
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        def _scroll_set(first, last):
            if float(first) <= 0.0 and float(last) >= 1.0:
                if vsb.winfo_ismapped():
                    vsb.pack_forget()
            else:
                if not vsb.winfo_ismapped():
                    vsb.pack(side="right", fill="y", before=canvas)
            vsb.set(first, last)

        canvas.configure(yscrollcommand=_scroll_set)
        inner = Frame(canvas, bg=BG)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner(e=None):
            canvas.update_idletasks()
            ch = canvas.winfo_height()
            ih = inner.winfo_reqheight()
            if ih <= ch:
                canvas.configure(scrollregion=(0, 0, 0, ch))
                canvas.yview_moveto(0)
            else:
                canvas.configure(scrollregion=canvas.bbox("all"))

        inner.bind("<Configure>", _on_inner)
        canvas.bind("<Configure>",
            lambda e: (canvas.itemconfig(win_id, width=e.width), _on_inner()))
        canvas.bind("<Enter>", lambda e: canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(-1*(e.delta//120), "units")))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        return canvas, inner

    def _toggle_pw(self, eye_lbl):
        showing = self._pw_entry.cget("show") == ""
        self._pw_entry.config(show="\u2022" if showing else "")
        eye_lbl.configure(fg=TEXT_SEC if showing else ACCENT)

    # ── Formattazione descrizione ─────────────────────────────────────────

    def _fmt_wrap(self, apri, chiudi):
        try:
            sel = self._desc_text.get(tkinter.SEL_FIRST, tkinter.SEL_LAST)
            self._desc_text.delete(tkinter.SEL_FIRST, tkinter.SEL_LAST)
            self._desc_text.insert(tkinter.INSERT, f"{apri}{sel}{chiudi}")
        except tkinter.TclError:
            self._desc_text.insert(tkinter.INSERT, f"{apri}testo{chiudi}")

    def _fmt_prefix(self, pfx):
        idx  = self._desc_text.index(tkinter.INSERT)
        riga = int(idx.split(".")[0])
        self._desc_text.insert(f"{riga}.0", pfx)

    def _fmt_link(self):
        popup = tkinter.Toplevel(self)
        popup.title("Inserisci link")
        popup.configure(bg=BG)
        popup.resizable(False, False)
        popup.grab_set()
        popup.update_idletasks()
        W, H = 420, 160
        x = (popup.winfo_screenwidth()  - W) // 2
        y = (popup.winfo_screenheight() - H) // 2
        popup.geometry(f"{W}x{H}+{x}+{y}")
        grid = Frame(popup, bg=BG)
        grid.pack(fill="both", expand=True, padx=20, pady=12)
        grid.columnconfigure(1, weight=1)
        _link_testo = tkinter.StringVar()
        _link_url   = tkinter.StringVar()
        for i, (lbl, var) in enumerate([("Testo", _link_testo), ("URL", _link_url)]):
            Label(grid, text=lbl, bg=BG, fg=TEXT_SEC,
                  font=("Consolas", 10)).grid(row=i, column=0, sticky="w", pady=4)
            ttk.Entry(grid, textvariable=var, style="Env.TEntry",
                      font=("Consolas", 10)).grid(
                      row=i, column=1, sticky="ew", pady=4, padx=(12, 0))
        try:
            _link_testo.set(self._desc_text.get(tkinter.SEL_FIRST, tkinter.SEL_LAST))
        except tkinter.TclError:
            pass

        def _ins():
            testo = _link_testo.get().strip() or _link_url.get().strip()
            url   = _link_url.get().strip()
            if not url:
                return
            try:
                self._desc_text.delete(tkinter.SEL_FIRST, tkinter.SEL_LAST)
            except tkinter.TclError:
                pass
            self._desc_text.insert(tkinter.INSERT, f"[{testo}|{url}]")
            popup.destroy()

        self._make_btn(grid, "\u2713  Inserisci", _ins).grid(
            row=2, column=0, columnspan=2, pady=(12, 0))

    # ── Allegati ──────────────────────────────────────────────────────────

    def _refresh_files_list(self):
        for w in self._files_frame.winfo_children():
            w.destroy()
        if not self._allegati:
            self._files_frame.pack_forget()
            return
        self._files_frame.pack(fill="x")
        import os as _os
        for i, fp in enumerate(self._allegati):
            tag = Frame(self._files_frame, bg=BG_CARD2,
                        highlightthickness=1, highlightbackground=BORDER)
            tag.pack(fill="x", pady=(4, 0))
            x = Label(tag, text="✕", bg=BG_CARD2, fg=ERROR,
                      font=("Consolas", 9), cursor="hand2", padx=8, pady=4)
            x.pack(side="right")
            x.bind("<Enter>", lambda e, w=x: w.configure(fg="#ff8080"))
            x.bind("<Leave>", lambda e, w=x: w.configure(fg=ERROR))
            x.bind("<Button-1>", lambda e, idx=i: self._remove_file(idx))
            Label(tag, text=_os.path.basename(fp), bg=BG_CARD2, fg=TEXT_PRI,
                  font=("Consolas", 9), anchor="w", padx=8, pady=4
                  ).pack(side="left", fill="x", expand=True)

    def _on_dnd_drop(self, event):
        import re, os as _os
        # Percorsi con spazi arrivano tra {}, senza spazi arrivano nudi
        raw = event.data
        paths = [p[0] or p[1] for p in re.findall(r'\{([^}]+)\}|(\S+)', raw)]
        existing = {_os.path.normpath(f) for f in self._allegati}
        for f in paths:
            if _os.path.isfile(f) and _os.path.normpath(f) not in existing:
                self._allegati.append(f)
        self._refresh_files_list()

    def _remove_file(self, idx):
        if 0 <= idx < len(self._allegati):
            self._allegati.pop(idx)
            self._refresh_files_list()

    def _add_attachments(self):
        files = filedialog.askopenfilenames(title="Seleziona allegati")
        if not files:
            return
        import os as _os
        existing = {_os.path.normpath(f) for f in self._allegati}
        for f in files:
            if _os.path.normpath(f) not in existing:
                self._allegati.append(f)
        self._refresh_files_list()

    def _remove_attachments(self):
        self._allegati = []
        self._refresh_files_list()

    # ── Load / Save credentials ───────────────────────────────────────────

    def _load_saved(self):
        env = _read_env_raw()
        self._url_var.set(env.get("JIRA_URL", "https://jira.fr.eni.com"))
        self._username_var.set(env.get("JIRA_USERNAME", ""))
        self._password_var.set(env.get("JIRA_PASSWORD", ""))
        self._cb_tipo_values = []
        self._cb_prio_values = []
        # Recupera priorità e tipi issue aggiornati da Jira in background
        threading.Thread(target=self._fetch_priorities, daemon=True).start()
        threading.Thread(target=self._fetch_issue_types, daemon=True).start()

    def _fetch_priorities(self):
        """Chiama /rest/api/2/priority e aggiorna _cb_prio_values."""
        try:
            import requests as _req
            from requests.auth import HTTPBasicAuth
            url  = self._url_var.get().strip().rstrip("/")
            user = self._username_var.get().strip()
            pw   = self._password_var.get()
            if not url or not user:
                return
            r = _req.get(f"{url}/rest/api/2/priority",
                         auth=HTTPBasicAuth(user, pw),
                         verify=_JIRA_VERIFY_SSL, timeout=10)
            if not r.ok:
                return
            priorities = [p["name"] for p in r.json() if p.get("name")]
            if priorities:
                self._cb_prio_values = priorities
        except Exception:
            pass

    def _fetch_issue_types(self):
        """Chiama /rest/api/2/issuetype e aggiorna _cb_tipo_values."""
        try:
            import requests as _req
            from requests.auth import HTTPBasicAuth
            url  = self._url_var.get().strip().rstrip("/")
            user = self._username_var.get().strip()
            pw   = self._password_var.get()
            if not url or not user:
                return
            r = _req.get(f"{url}/rest/api/2/issuetype",
                         auth=HTTPBasicAuth(user, pw),
                         verify=_JIRA_VERIFY_SSL, timeout=10)
            if not r.ok:
                return
            tipos = [t["name"] for t in r.json() if t.get("name")]
            if tipos:
                self._cb_tipo_values = tipos
        except Exception:
            pass

    def _save_credentials(self):
        _write_env({
            "JIRA_USERNAME": self._username_var.get().strip(),
            "JIRA_PASSWORD": self._password_var.get(),
        })
        _reload_env()
        self._warn_status("\u2713 Credenziali salvate.")

    # ── Test connessione ──────────────────────────────────────────────────

    def _on_test_and_save(self):
        if not self._username_var.get() or not self._password_var.get():
            messagebox.showwarning("Autenticazione", "Inserisci username e password.")
            return
        self._btn_test.configure(fg=TEXT_SEC, cursor="arrow")
        self._test_result_var.set("⏳ Verifica in corso...")
        threading.Thread(target=self._test_and_save_worker, daemon=True).start()

    def _test_and_save_worker(self):
        try:
            import requests as _req
            from requests.auth import HTTPBasicAuth
            url  = self._url_var.get().strip().rstrip("/")
            auth = HTTPBasicAuth(self._username_var.get().strip(),
                                 self._password_var.get())
            r = _req.get(f"{url}/rest/api/2/myself", auth=auth,
                         verify=_JIRA_VERIFY_SSL, timeout=10)
            if r.status_code == 401:
                self.after(0, self._test_save_fail,
                           "Credenziali non valide (401) — username o password errati.")
                return
            if r.status_code == 403:
                self.after(0, self._test_save_fail, "Accesso negato (403).")
                return
            r.raise_for_status()
            data = r.json()
            nome = data.get("displayName") or data.get("name") or "utente"
            # Fetch priorities
            r2 = _req.get(f"{url}/rest/api/2/priority", auth=auth,
                          verify=_JIRA_VERIFY_SSL, timeout=10)
            if r2.ok:
                prios = [p["name"] for p in r2.json()]
                self.after(0, lambda p=prios: (
                    setattr(self, "_cb_prio_values", p),
                    self._prio_var.set(p[0] if p else "")))
            self.after(0, self._test_save_ok, nome)
        except _req.exceptions.ConnectionError:
            self.after(0, self._test_save_fail,
                       "Impossibile raggiungere il server — controlla URL e rete.")
        except _req.exceptions.Timeout:
            self.after(0, self._test_save_fail, "Timeout — il server non risponde.")
        except Exception as e:
            self.after(0, self._test_save_fail, str(e))

    def _test_save_ok(self, nome):
        self._btn_test.configure(fg=ACCENT, cursor="hand2")
        self._test_result_var.set("")
        _write_env({
            "JIRA_USERNAME": self._username_var.get().strip(),
            "JIRA_PASSWORD": self._password_var.get(),
        })
        _reload_env()
        self._enqueue_log(f"[OK] Credenziali valide — connesso come: {nome}. Salvato.", "ok")

    def _test_save_fail(self, msg):
        self._btn_test.configure(fg=ACCENT, cursor="hand2")
        self._test_result_var.set("")
        self._enqueue_log(f"[ERRORE] Credenziali non salvate: {msg}", "error")

    def _jira_env_get(self) -> str:
        """Restituisce 'PROD' o 'CHOPIN' dal toggle del Launcher."""
        try:
            return self.winfo_toplevel()._jira_env
        except Exception:
            return "PROD"

    def _on_test(self):
        self._on_test_and_save()

    def _test_worker(self):
        try:
            import requests as _req
            from requests.auth import HTTPBasicAuth
            url  = self._url_var.get().strip().rstrip("/")
            auth = HTTPBasicAuth(self._username_var.get().strip(),
                                 self._password_var.get())
            r = _req.get(f"{url}/rest/api/2/myself", auth=auth,
                         verify=_JIRA_VERIFY_SSL, timeout=10)
            if r.status_code == 401:
                self.after(0, self._test_err, "Credenziali non valide (401) — verifica username e password.")
                return
            if r.status_code == 403:
                self.after(0, self._test_err, "Accesso negato (403) — account non autorizzato.")
                return
            r.raise_for_status()
            data = r.json()
            nome = data.get("displayName") or data.get("name") or "utente"
            # Fetch priorities
            r2 = _req.get(f"{url}/rest/api/2/priority", auth=auth,
                          verify=_JIRA_VERIFY_SSL, timeout=10)
            if r2.ok:
                prios = [p["name"] for p in r2.json()]
                self.after(0, lambda p=prios: (
                    setattr(self, "_cb_prio_values", p),
                    self._prio_var.set(p[0] if p else "")))
            self.after(0, self._test_ok, nome)
        except _req.exceptions.ConnectionError:
            self.after(0, self._test_err, f"Impossibile raggiungere il server — controlla URL e rete.")
        except _req.exceptions.Timeout:
            self.after(0, self._test_err, "Timeout — il server non risponde.")
        except Exception as e:
            self.after(0, self._test_err, str(e))

    def _test_ok(self, nome):
        self._btn_test.configure(fg=ACCENT, cursor="hand2")
        self._test_result_var.set(f"\u2705  Connesso come: {nome}")
        self._enqueue_log(f"[OK] Test riuscito — utente: {nome}", "ok")

    def _test_err(self, msg):
        self._btn_test.configure(fg=ACCENT, cursor="hand2")
        self._test_result_var.set(f"\u274c  {msg}")
        self._enqueue_log(f"[ERRORE] Test connessione: {msg}", "error")

    # ── Crea ticket ───────────────────────────────────────────────────────

    def _on_valida_assegnatario(self):
        username = self._assegn_var.get().strip()
        if not username:
            return  # bottone disabilitato, non dovrebbe arrivare qui
        if not self._username_var.get() or not self._password_var.get():
            self._assegn_result_var.set("⚠  Credenziali non configurate. Vai in Impostazioni → Jira.")
            self._assegn_result_lbl.configure(fg=WARNING)
            return
        self._assegn_result_var.set("⏳ Verifica...")
        self._assegn_result_lbl.configure(fg=TEXT_PRI)
        self._btn_valida_assegn.configure(fg=TEXT_SEC, cursor="arrow")
        threading.Thread(target=self._valida_assegn_worker, args=(username,), daemon=True).start()

    def _valida_assegn_worker(self, username):
        try:
            import requests as _req
            from requests.auth import HTTPBasicAuth
            url  = self._url_var.get().strip().rstrip("/")
            auth = HTTPBasicAuth(self._username_var.get().strip(),
                                 self._password_var.get())
            r = _req.get(f"{url}/rest/api/2/user/search",
                         params={"username": username, "maxResults": 5},
                         auth=auth, verify=_JIRA_VERIFY_SSL, timeout=10)
            if not r.ok:
                self.after(0, self._assegn_result, False,
                           f"Errore API ({r.status_code})")
                return
            results = r.json()
            match = next((u for u in results
                          if u.get("name", "").lower() == username.lower()), None)
            if match:
                display = match.get("displayName", username)
                self.after(0, self._assegn_result, True,
                           f"✓  {display}")
            elif results:
                names = ", ".join(u.get("name", "") for u in results[:3])
                self.after(0, self._assegn_result, False,
                           f"✗  Non trovato. Simili: {names}")
            else:
                self.after(0, self._assegn_result, False,
                           "✗  Nessun utente trovato.")
        except Exception as e:
            self.after(0, self._assegn_result, False, f"Errore: {e}")

    def _assegn_result(self, ok, msg):
        self._btn_valida_assegn.configure(fg=ACCENT, cursor="hand2")
        self._assegn_result_var.set(msg)
        self._assegn_result_lbl.configure(fg=SUCCESS if ok else WARNING)

    def _on_debug(self):
        """Simula creazione ticket senza chiamare Jira — mostra il .cfg nel log."""
        self._enqueue_log("\n── DEBUG MODE ──", "section")

        # Campi base
        proj  = self._proj_var.get().strip()
        title = self._title_var.get().strip()
        tipo  = self._tipo_var.get()
        prio  = self._prio_var.get()
        assegn = self._assegn_var.get().strip()
        desc  = self._desc_text.get("1.0", tkinter.END).strip()

        fake_key = f"{proj or 'PRJ'}-99999"

        self._enqueue_log(f"[DEBUG] Ticket simulato: {fake_key}", "info")

        if self._allegati:
            self._enqueue_log(f"[DEBUG] Allegati ({len(self._allegati)}):", "info")
            import os as _os
            for fp in self._allegati:
                self._enqueue_log(f"         • {_os.path.basename(fp)}", "info")
        else:
            self._enqueue_log("[DEBUG] Allegati: nessuno", "info")

        if self._cfg_var.get():
            import os as _os, zipfile as _zf
            zip_paths = [fp for fp in self._allegati if fp.lower().endswith(".zip")]
            if not zip_paths:
                self._enqueue_log("[DEBUG] .cfg: ✗ Nessun ZIP tra gli allegati", "error")
                return
            cfg_content, err = _jira_build_cfg(fake_key, zip_paths, self._jira_env_get())
            if err:
                self._enqueue_log(f"[DEBUG] .cfg: ✗ {err}", "error")
            else:
                self._enqueue_log("[DEBUG] .cfg generato:", "ok")
                for line in cfg_content.splitlines():
                    self._enqueue_log(f"         {line}", "ok")

                # Conteggio file per cartella destinazione
                dir_files: dict = {}  # target_dir -> [(zip_name, count)]
                for fp in zip_paths:
                    zip_name = _os.path.basename(fp)
                    try:
                        with _zf.ZipFile(fp, "r") as z:
                            csv_files = [n for n in z.namelist()
                                         if not n.endswith("/") and n.lower().endswith(".csv")]
                            count = len(csv_files)
                    except Exception:
                        count = 0
                    # Trova il target_dir per questo ZIP dal .cfg
                    for line in cfg_content.splitlines()[1:]:
                        parts = line.split(";")
                        if len(parts) == 3 and parts[1] == zip_name:
                            target = parts[2]
                            dir_files.setdefault(target, []).append((zip_name, count))
                            break

                if dir_files:
                    lines = ["[DEBUG] File per cartella destinazione:"]
                    for target, entries in dir_files.items():
                        total = sum(c for _, c in entries)
                        lines.append(f"         {target}  →  {total} file")
                    self._enqueue_log("\n".join(lines), "info")
        else:
            self._enqueue_log("[DEBUG] .cfg: disabilitato", "info")

        self._enqueue_log("── Fine DEBUG ──\n", "section")

    def _pulisci(self):
        for var in (self._proj_var, self._title_var, self._assegn_var):
            var.set("")
        self._tipo_var.set("\u2014")
        self._prio_var.set("\u2014")
        self._desc_text.delete("1.0", tkinter.END)
        self._remove_attachments()
        self._assegn_result_var.set("")

    def _on_crea(self):
        mancanti = [n for n, v in [
            ("Project Key",  self._proj_var.get().strip()),
            ("Title",        self._title_var.get().strip()),
            ("Tipo Issue",   self._tipo_var.get().strip()),
            ("Assegnatario", self._assegn_var.get().strip()),
            ("Descrizione",  self._desc_text.get("1.0", tkinter.END).strip()),
        ] if not v]
        if mancanti:
            messagebox.showwarning("Campi obbligatori",
                                   "Campi mancanti:\n\n  \u2022 " +
                                   "\n  \u2022 ".join(mancanti))
            return
        if not self._username_var.get() or not self._password_var.get():
            messagebox.showwarning("Autenticazione", "Inserisci username e password.")
            return

        # Conferma e avvio
        if not messagebox.askyesno("Conferma",
                                   f"Creare il ticket:\n\n"
                                   f"  Progetto: {self._proj_var.get()}\n"
                                   f"  Title:    {self._title_var.get()}\n"
                                   f"  Tipo:     {self._tipo_var.get()}"):
            return

        self._cfg_content = None
        self._btn_crea.configure(fg=TEXT_SEC, cursor="arrow")
        self._status_var.set("Invio in corso...")
        threading.Thread(target=self._crea_worker, daemon=True).start()

    def _crea_worker(self):
        try:
            import requests as _req, os as _os, tempfile as _tmp
            from requests.auth import HTTPBasicAuth
            url  = self._url_var.get().strip().rstrip("/")
            auth = HTTPBasicAuth(self._username_var.get().strip(),
                                 self._password_var.get())
            headers    = {"Content-Type": "application/json"}
            atl_h      = {"X-Atlassian-Token": "no-check"}
            assegnatario = self._assegn_var.get().strip()

            # ── Step 0: Valida assegnatario ───────────────────────────────
            self._enqueue_log("[INFO] Validazione assegnatario...", "info")
            r_u = _req.get(f"{url}/rest/api/2/user/search",
                           params={"username": assegnatario, "maxResults": 5},
                           auth=auth, verify=_JIRA_VERIFY_SSL, timeout=10)
            if not r_u.ok:
                self.after(0, self._crea_err,
                           f"Impossibile verificare l'assegnatario ({r_u.status_code}).")
                return
            results = r_u.json()
            match = next((u for u in results
                          if u.get("name", "").lower() == assegnatario.lower()), None)
            if not match:
                simili = ", ".join(u.get("name", "") for u in results[:3])
                msg = f"Assegnatario '{assegnatario}' non trovato su Jira."
                if simili:
                    msg += f" Utenti simili: {simili}"
                self.after(0, self._crea_err, msg)
                return
            self._enqueue_log(
                f"[OK] Assegnatario verificato: {match.get('displayName', assegnatario)}",
                "ok")

            # ── Step 1: Valida .cfg (se richiesto) ───────────────────────
            if self._cfg_var.get():
                zip_paths = [fp for fp in self._allegati if fp.lower().endswith(".zip")]
                if not zip_paths:
                    self.after(0, self._crea_err,
                               "Nessun file ZIP tra gli allegati — impossibile generare il .cfg.")
                    return
                self._enqueue_log("[INFO] Validazione ZIP in corso...", "info")
                cfg_content, err = _jira_build_cfg("__KEY__", zip_paths, self._jira_env_get())
                if err:
                    self._enqueue_log(f"[ERRORE] Validazione .cfg: {err}", "error")
                    self.after(0, self._crea_err, f"Errore validazione ZIP: {err}")
                    return
                self._cfg_content = cfg_content
                self._enqueue_log("[OK] Validazione ZIP superata.", "ok")

            # ── Step 2: Crea ticket (senza assegnatario) ──────────────────
            payload = {"fields": {
                "project":     {"key": self._proj_var.get().strip().upper()},
                "summary":     self._title_var.get().strip(),
                "issuetype":   {"name": self._tipo_var.get()},
                "priority":    {"name": self._prio_var.get()},
                "description": self._desc_text.get("1.0", tkinter.END).strip(),
            }}
            self._enqueue_log("[INFO] Creazione ticket...", "info")
            r = _req.post(f"{url}/rest/api/2/issue", headers=headers,
                          data=_json_mod.dumps(payload), auth=auth,
                          verify=_JIRA_VERIFY_SSL, timeout=15)
            r.raise_for_status()
            key = r.json().get("key", "?")
            self._enqueue_log(f"[OK] Ticket creato: {key}", "ok")
            ep    = f"{url}/rest/api/2/issue/{key}/attachments"
            atl_h = {"X-Atlassian-Token": "no-check"}

            # ── Prepara .cfg se richiesto ─────────────────────────
            cfg_path = None
            cfg_name = None
            if self._cfg_var.get() and self._cfg_content:
                cfg_name = f"{key}.cfg"
                cfg_dir  = _HERE / "output" / "jira ticket" / "cfg"
                cfg_dir.mkdir(parents=True, exist_ok=True)
                cfg_path = str(cfg_dir / cfg_name)
                final_content = self._cfg_content.replace("__KEY__", key)
                with open(cfg_path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(final_content)

                # Conteggio file per cartella destinazione
                import zipfile as _zf2
                dir_files: dict = {}
                for fp in zip_paths:
                    zip_name = _os.path.basename(fp)
                    try:
                        with _zf2.ZipFile(fp, "r") as z:
                            count = len([n for n in z.namelist()
                                         if not n.endswith("/") and n.lower().endswith(".csv")])
                    except Exception:
                        count = 0
                    for line in final_content.splitlines()[1:]:
                        parts = line.split(";")
                        if len(parts) == 3 and parts[1] == zip_name:
                            dir_files.setdefault(parts[2], 0)
                            dir_files[parts[2]] += count
                            break
                if dir_files:
                    lines = ["[INFO] File per cartella destinazione:"]
                    for target, total in dir_files.items():
                        lines.append(f"         {target}  →  {total} file")
                    self._enqueue_log("\n".join(lines), "info")

            # ── Step 3: Allega tutti i file in una sola chiamata ──────────
            try:
                tutti = list(self._allegati)
                if cfg_path:
                    tutti.append(cfg_path)
                if tutti:
                    files = []
                    handles = []
                    for fp in tutti:
                        name = _os.path.basename(fp)
                        fh = open(fp, "rb")
                        handles.append(fh)
                        files.append(("file", (name, fh)))
                    try:
                        ra = _req.post(ep, headers=atl_h, files=files,
                                       auth=auth, verify=_JIRA_VERIFY_SSL, timeout=60)
                    finally:
                        for fh in handles:
                            try: fh.close()
                            except Exception: pass
                    if ra.ok:
                        uploaded = [a.get("filename", "?") for a in ra.json()]
                        self._enqueue_log(
                            f"[OK] {len(uploaded)} allegato/i caricato/i: "
                            f"{', '.join(uploaded)}", "ok")
                    else:
                        self._enqueue_log(
                            f"[WARN] Upload allegati: {ra.status_code} — {ra.text[:200]}",
                            "warn")
            finally:
                if cfg_path:
                    try:
                        _os.remove(cfg_path)
                    except Exception:
                        pass

            # ── Step 4: Aggiorna assegnatario ─────────────────────────────
            if assegnatario:
                ra = _req.put(
                    f"{url}/rest/api/2/issue/{key}/assignee",
                    headers=headers,
                    data=_json_mod.dumps({"name": assegnatario}),
                    auth=auth, verify=_JIRA_VERIFY_SSL, timeout=10)
                self._enqueue_log(
                    f"[{'OK' if ra.ok else 'WARN'}] Assegnatario: {assegnatario}",
                    "ok" if ra.ok else "warn")

            self.after(0, self._crea_ok, key, f"{url}/browse/{key}")
        except Exception as e:
            self.after(0, self._crea_err, str(e))

    def _crea_ok(self, key, url):
        self._btn_crea.configure(fg=ACCENT, cursor="hand2")
        self._status_var.set(f"\u2713 Ticket {key} creato.")
        from datetime import datetime as _dt
        ts = _dt.now().strftime("%Y-%m-%d %H:%M:%S")
        tag_name = f"link_{key}"
        self._log_box.configure(state="normal")
        self._log_box.tag_configure(tag_name, foreground=ACCENT,
                                    font=("Consolas", 10, "underline"), cursor="hand2")
        self._log_box.tag_bind(tag_name, "<Button-1>",
                               lambda e, u=url: __import__("webbrowser").open(u))
        self._log_box.insert("end", f"[{ts}] [OK] Ticket creato: {key}  \u2192  ", "ok")
        self._log_box.insert("end", url + "\n", tag_name)
        self._log_box.see("end")
        self._log_box.configure(state="disabled")
        messagebox.showinfo("Ticket creato!", f"Ticket {key} creato con successo!\n\n{url}")
        self._remove_attachments()

    def _crea_err(self, msg):
        self._btn_crea.configure(fg=ACCENT, cursor="hand2")
        self._status_var.set("\u2717 Errore creazione.")
        self._enqueue_log(f"[ERRORE] Creazione ticket: {msg}", "error")
        messagebox.showerror("Errore", msg)

    # ── Importa ───────────────────────────────────────────────────────────

    def _on_import(self):
        chiave = self._import_var.get().strip()
        if not chiave:
            messagebox.showwarning("Campo vuoto", "Inserisci chiave o URL del ticket.")
            return
        if not self._username_var.get():
            messagebox.showwarning("Autenticazione", "Compila prima le credenziali.")
            return
        threading.Thread(target=self._import_worker, args=(chiave,), daemon=True).start()

    def _import_worker(self, chiave):
        try:
            import requests as _req, re as _re
            from requests.auth import HTTPBasicAuth
            m = _re.search(r'/browse/([A-Z]+-\d+)', chiave)
            if m:
                chiave = m.group(1)
            chiave = chiave.strip().upper()
            url  = self._url_var.get().strip().rstrip("/")
            auth = HTTPBasicAuth(self._username_var.get().strip(),
                                 self._password_var.get())
            r = _req.get(f"{url}/rest/api/2/issue/{chiave}", auth=auth,
                         verify=_JIRA_VERIFY_SSL, timeout=10)
            r.raise_for_status()
            self.after(0, self._import_ok, r.json(), chiave)
        except Exception as e:
            self.after(0, self._import_err, str(e))

    def _import_ok(self, data, chiave):
        f = data.get("fields", {})
        self._proj_var.set(f.get("project", {}).get("key", ""))
        self._title_var.set(f.get("summary", ""))
        tipo = (f.get("issuetype") or {}).get("name", "")
        prio = (f.get("priority")  or {}).get("name", "")
        if tipo and tipo not in self._cb_tipo_values:
            self._cb_tipo_values = self._cb_tipo_values + [tipo]
        if prio and prio not in self._cb_prio_values:
            self._cb_prio_values = self._cb_prio_values + [prio]
        self._tipo_var.set(tipo)
        self._prio_var.set(prio)
        self._assegn_var.set((f.get("assignee") or {}).get("name", ""))
        self._desc_text.delete("1.0", tkinter.END)
        self._desc_text.insert("1.0", f.get("description") or "")
        self._enqueue_log(f"[OK] Importato da: {chiave}", "ok")
        messagebox.showinfo("Importato", f"Campi copiati da {chiave}.")

    def _import_err(self, msg):
        self._enqueue_log(f"[ERRORE] Importazione: {msg}", "error")
        messagebox.showerror("Errore importazione", msg)

    # ── Template ──────────────────────────────────────────────────────────

    def _refresh_templates(self):
        templates = _jira_load_templates()
        keys = list(templates.keys())
        self._tmpl_var.set(keys[0] if keys else "")
        if keys:
            self._preview_template()

    def _preview_template(self):
        chiave = self._tmpl_var.get()
        t = _jira_load_templates().get(chiave, {})
        if t:
            self._tmpl_preview.configure(
                text=f"{t.get('project_key','')} \u2014 {t.get('title','')}\n"
                     f"Tipo: {t.get('tipo_issue','')}  |  "
                     f"Priorit\xe0: {t.get('priorita','')}  |  "
                     f"Assegnatario: {t.get('assegnatario','')}")

    def _load_template(self):
        chiave = self._tmpl_var.get()
        if not chiave:
            messagebox.showwarning("Nessun template", "Seleziona un template.")
            return
        t = _jira_load_templates().get(chiave, {})
        if not t:
            return
        self._proj_var.set(t.get("project_key", ""))
        self._title_var.set(t.get("title", ""))
        tipo = t.get("tipo_issue", "")
        prio = t.get("priorita", "")
        if tipo and tipo not in self._cb_tipo_values:
            self._cb_tipo_values = self._cb_tipo_values + [tipo]
        if prio and prio not in self._cb_prio_values:
            self._cb_prio_values = self._cb_prio_values + [prio]
        self._tipo_var.set(tipo)
        self._prio_var.set(prio)
        self._assegn_var.set(t.get("assegnatario", ""))
        self._desc_text.delete("1.0", tkinter.END)
        self._desc_text.insert("1.0", t.get("descrizione", ""))
        self._enqueue_log(f"[INFO] Template caricato: {chiave}", "info")

    def _save_template(self):
        pk    = self._proj_var.get().strip()
        title = self._title_var.get().strip()
        if not pk or not title:
            messagebox.showwarning("Campi mancanti", "Compila Project Key e Title.")
            return
        chiave = f"{pk.upper()}::{title}"
        templates = _jira_load_templates()
        templates[chiave] = {
            "project_key":  pk,
            "title":        title,
            "tipo_issue":   self._tipo_var.get(),
            "priorita":     self._prio_var.get(),
            "assegnatario": self._assegn_var.get(),
            "descrizione":  self._desc_text.get("1.0", tkinter.END).strip(),
        }
        _jira_save_templates(templates)
        self._enqueue_log(f"[OK] Template salvato: {chiave}", "ok")
        messagebox.showinfo("Template salvato", f"Template «{chiave}» salvato con successo.")

    def _delete_template(self):
        chiave = self._tmpl_var.get()
        if not chiave:
            return
        if not messagebox.askyesno("Elimina template", f"Eliminare \xabf{chiave}\xbb?"):
            return
        templates = _jira_load_templates()
        templates.pop(chiave, None)
        _jira_save_templates(templates)
        self._refresh_templates()
        self._enqueue_log(f"[INFO] Template eliminato: {chiave}", "info")


# ════════════════════════════════════════════════════════════════════════════
# UPDATE HUB FILTER
# ════════════════════════════════════════════════════════════════════════════

UHF_INPUT_FILE = _HERE / "input" / "hub filter updater" / "data_input.txt"


class HubFilterUpdater(_AppBase):

    def __init__(self, master):
        super().__init__(master, bg=BG)
        self._log_queue: queue.Queue = queue.Queue()
        self._running        = False
        self._stop_requested = False

        self._build_ui()
        self._load_input_into_table()
        self._poll_log()

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("UHF.TNotebook",
                        background=BG, borderwidth=0, tabmargins=[0, 0, 0, 0])
        style.configure("UHF.TNotebook.Tab",
                        background=BG_CARD, foreground=TEXT_SEC,
                        font=("Consolas", 10), padding=[16, 6],
                        borderwidth=0)
        style.map("UHF.TNotebook.Tab",
                  background=[("selected", BG_CARD2)],
                  foreground=[("selected", TEXT_PRI)],
                  padding=[("selected", [16, 8]), ("!selected", [16, 6])])

        nb = ttk.Notebook(self, style="UHF.TNotebook")
        nb.pack(fill="both", expand=True, padx=24, pady=(12, 0))

        tab_pipeline = Frame(nb, bg=BG)
        nb.add(tab_pipeline, text="  ▶  Pipeline  ")
        self._build_pipeline_tab(tab_pipeline)

        tab_input = Frame(nb, bg=BG)
        nb.add(tab_input, text="  📋  Data Input  ")
        self._build_input_tab(tab_input)

        self._status_var = tkinter.StringVar(value="Pronto.")
        Label(self, textvariable=self._status_var, bg=BG, fg=TEXT_SEC,
              font=("Consolas", 9), anchor="w", pady=5).pack(fill="x", padx=24, side="bottom")
        Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24, side="bottom")

    def _build_pipeline_tab(self, parent):
        body = Frame(parent, bg=BG)
        body.pack(fill="both", expand=True)

        top = Frame(body, bg=BG_CARD, bd=0, highlightthickness=1,
                    highlightbackground=BORDER)
        top.pack(fill="x", pady=(0, 10))

        row = Frame(top, bg=BG_CARD)
        row.pack(fill="x", padx=14, pady=10)

        Label(row, text="Cluster", bg=BG_CARD, fg=TEXT_SEC,
              font=("Consolas", 9), anchor="w").pack(side="left", padx=(0, 8))

        self._cluster_var = tkinter.StringVar()
        self._cluster_entry = tkinter.Entry(row, textvariable=self._cluster_var,
                                            bg=BG_INPUT, fg=TEXT_PRI, insertbackground=TEXT_PRI,
                                            disabledbackground=BG_CARD, disabledforeground=TEXT_SEC,
                                            font=("Consolas", 10), relief="flat", bd=0,
                                            highlightthickness=1, highlightbackground=BORDER)
        self._cluster_entry.pack(side="left", fill="x", expand=True, ipady=5)
        self._cluster_entry.bind("<FocusIn>",  lambda e: self._cluster_entry.configure(highlightbackground=ACCENT))
        self._cluster_entry.bind("<FocusOut>", lambda e: self._cluster_entry.configure(highlightbackground=BORDER))

        self._btn = self._make_btn(row, "▶  Avvia", self._start)
        self._btn.pack(side="right", padx=(12, 0))

        log_frame = Frame(body, bg=BG_CARD, bd=0, highlightthickness=1,
                          highlightbackground=BORDER)
        log_frame.pack(fill="both", expand=True)
        self._build_log_panel(log_frame, on_clear=self._clear_log)

    def _build_input_tab(self, parent):
        hdr = Frame(parent, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(12, 0))
        Label(hdr, text="Data Input  —  PRM / Kraken Account", bg=BG, fg=TEXT_PRI,
              font=("Consolas", 11, "bold")).pack(side="left")
        Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(8, 0))
        Label(parent, text="Ogni riga rappresenta una coppia PRM ; Kraken Account da processare.",
              bg=BG, fg=TEXT_SEC, font=("Consolas", 9), anchor="w", pady=6).pack(fill="x", padx=16)

        toolbar = Frame(parent, bg=BG)
        toolbar.pack(fill="x", padx=16, pady=(0, 6))
        self._make_btn(toolbar, "✏️  Modifica / Aggiungi", self._input_paste_popup,
                       color=SUCCESS).pack(side="left", padx=(0, 6))
        self._make_btn(toolbar, "🗑  Svuota righe", self._input_clear_all,
                       color=ERROR).pack(side="left")

        table_frame = Frame(parent, bg=BG_CARD,
                            highlightthickness=1, highlightbackground=BORDER)
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        style = ttk.Style()
        style.configure("UHF.Treeview",
                        background=BG_CARD, foreground=TEXT_PRI,
                        fieldbackground=BG_CARD, rowheight=26,
                        font=("Consolas", 10), borderwidth=0)
        style.configure("UHF.Treeview.Heading",
                        background=BG_CARD2, foreground=ACCENT,
                        font=("Consolas", 9, "bold"), relief="flat")
        style.map("UHF.Treeview",
                  background=[("selected", ACCENT2)],
                  foreground=[("selected", TEXT_PRI)])

        cols = ("prm", "kraken")
        self._input_tree = ttk.Treeview(table_frame, columns=cols,
                                        show="headings", style="UHF.Treeview",
                                        selectmode="browse")
        self._input_tree.heading("prm",    text="PRM")
        self._input_tree.heading("kraken", text="Kraken Account")
        self._input_tree.column("prm",    width=260, minwidth=120, anchor="w")
        self._input_tree.column("kraken", width=260, minwidth=120, anchor="w")

        vsb = ttk.Scrollbar(table_frame, orient="vertical",
                            command=self._input_tree.yview,
                            style="Dark.Vertical.TScrollbar")
        def _scroll(f, l):
            if float(f) <= 0.0 and float(l) >= 1.0:
                if vsb.winfo_ismapped():
                    vsb.after(1, vsb.pack_forget)
            else:
                if not vsb.winfo_ismapped():
                    vsb.after(1, lambda: vsb.pack(side="right", fill="y",
                                                   before=self._input_tree))
            vsb.set(f, l)
        vsb.pack(side="right", fill="y")
        self._input_tree.configure(yscrollcommand=_scroll)
        self._input_tree.pack(fill="both", expand=True)
        self._input_tree.bind("<Double-1>", self._input_edit_cell)

        footer = Frame(parent, bg=BG)
        footer.pack(fill="x", padx=16, pady=(0, 4))
        self._input_count_var = tkinter.StringVar(value="")
        Label(footer, textvariable=self._input_count_var,
              bg=BG, fg=TEXT_SEC, font=("Consolas", 9)).pack(side="left")

    # ── Input CRUD ────────────────────────────────────────────────────────

    def _load_input_into_table(self):
        if not hasattr(self, "_input_tree"):
            return
        for row in self._input_tree.get_children():
            self._input_tree.delete(row)
        if not UHF_INPUT_FILE.exists():
            self._input_count_var.set("File non trovato — verrà creato al salvataggio.")
            return
        lines = UHF_INPUT_FILE.read_text(encoding="utf-8").strip().splitlines()
        count = 0
        for line in lines:
            line = line.strip()
            if not line or line.lower().startswith("prm"):
                continue
            parts = line.split(";")
            if len(parts) == 2:
                self._input_tree.insert("", "end", values=(parts[0].strip(), parts[1].strip()))
                count += 1
            else:
                self._input_tree.insert("", "end", values=(line, ""))
        self._input_count_var.set(f"{count} righe caricate.")

    def _save_input(self):
        rows = []
        for iid in self._input_tree.get_children():
            vals = self._input_tree.item(iid, "values")
            prm    = vals[0].strip() if len(vals) > 0 else ""
            kraken = vals[1].strip() if len(vals) > 1 else ""
            if prm or kraken:
                rows.append(f"{prm};{kraken}")
        try:
            UHF_INPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
            UHF_INPUT_FILE.write_text("\n".join(rows) + "\n" if rows else "", encoding="utf-8")
            self._status_var.set(f"✓ data_input.txt salvato ({len(rows)} righe).")
            self._update_input_count()
        except Exception as e:
            messagebox.showerror("Errore salvataggio", str(e))

    def _update_input_count(self):
        n = len(self._input_tree.get_children())
        self._input_count_var.set(f"{n} righe.")

    def _input_paste_popup(self):
        self._paste_popup(
            title="Modifica / Aggiungi dati",
            subtitle=("Modifica, aggiungi o cancella righe. Formato: PRM;KrakenAccount\n"
                      "Le righe non valide verranno evidenziate in arancione."),
            tree=self._input_tree, count_var=self._input_count_var,
            empty_warning="⚠  Nessuna riga trovata.",
            count_label_fn=lambda n: f"{n} righe.",
            save_fn=self._save_input,
            two_column=True, W=560, H=460,
        )

    def _input_clear_all(self):
        if not self._input_tree.get_children():
            return
        if messagebox.askyesno("Svuota righe", "Sei sicuro di voler rimuovere tutte le righe?"):
            self._input_tree.delete(*self._input_tree.get_children())
            self._update_input_count()
            self._save_input()

    def _input_edit_cell(self, event):
        region = self._input_tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        col_id = self._input_tree.identify_column(event.x)
        col = "prm" if col_id == "#1" else "kraken"
        iid = self._input_tree.identify_row(event.y)
        if not iid:
            return
        col_index = 0 if col == "prm" else 1
        bbox = self._input_tree.bbox(iid, col)
        if not bbox:
            return
        x, y, w, h = bbox
        current_val = self._input_tree.item(iid, "values")
        val = current_val[col_index] if current_val else ""
        var = StringVar(value=val)
        entry = tkinter.Entry(self._input_tree, textvariable=var,
                              bg=BG_INPUT, fg=TEXT_PRI, insertbackground=TEXT_PRI,
                              font=("Consolas", 10), relief="flat", bd=2,
                              highlightthickness=1, highlightbackground=ACCENT)
        entry.place(x=x, y=y, width=w, height=h)
        entry.focus_set()
        entry.select_range(0, "end")

        def _commit(e=None):
            new_val = var.get()
            vals = list(self._input_tree.item(iid, "values"))
            while len(vals) < 2:
                vals.append("")
            vals[col_index] = new_val
            self._input_tree.item(iid, values=tuple(vals))
            entry.destroy()
            self._save_input()

        entry.bind("<Return>",  _commit)
        entry.bind("<FocusOut>", _commit)
        entry.bind("<Escape>",  lambda e: entry.destroy())

    def _on_done(self, success: bool):
        self._running = False
        self._stop_requested = False
        self._cluster_var.set("")
        self._cluster_entry.configure(state="normal")
        color = SUCCESS if success else ERROR
        self._status_var.set("✓ Completato." if success else "✗ Errore.")
        self._btn.configure(fg=color, cursor="hand2")
        self.after(3000, lambda: self._btn.configure(fg=ACCENT))

    def _clear_log(self):
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    # ── Pipeline ──────────────────────────────────────────────────────────

    def _start(self):
        if self._running:
            return
        if not self._cluster_var.get().strip():
            self._enqueue_log("[ERRORE] Campo 'Cluster' obbligatorio — inserisci un valore prima di avviare.", "error")
            return
        pairs = [
            (self._input_tree.item(iid, "values")[0].strip(),
             self._input_tree.item(iid, "values")[1].strip())
            for iid in self._input_tree.get_children()
            if self._input_tree.item(iid, "values")
        ]
        if not pairs:
            self._enqueue_log("[ERRORE] Nessuna coppia PRM / Kraken Account nel Data Input.", "error")
            return
        self._running = True
        self._stop_requested = False
        self._btn.configure(fg=TEXT_SEC, cursor="arrow")
        self._cluster_entry.configure(state="disabled", highlightbackground=BORDER)
        self._status_var.set("In esecuzione ...")
        cluster = self._cluster_var.get().strip()
        threading.Thread(target=self._run, args=(cluster, pairs), daemon=True).start()

    def _run(self, cluster: str, pairs: list):
        from datetime import datetime

        _reload_env()
        self._run_ts = datetime.now().astimezone()
        filename = f"{cluster} - {self._run_ts.strftime('%Y/%m/%d')}"

        try:
            self._enqueue_log("[INFO] Connessione HUB ...", "info")
            conn = get_hub_connection()
            self._enqueue_log("[OK] Connessione HUB attiva ✓", "ok")

            cur = conn.cursor()

            # 1. Recupero commodity da agreement
            self._enqueue_log(f"[INFO] Recupero commodity da agreement per {len(pairs)} coppie ...", "info")
            placeholders = ", ".join(["(%s, %s)"] * len(pairs))
            params = [v for pair in pairs for v in pair]
            cur.execute(
                f"""
                SELECT DISTINCT prm_pce, number,
                    CASE sparte WHEN '01' THEN 'ELEC' WHEN '02' THEN 'GAS' ELSE sparte END
                FROM public.agreement
                WHERE (prm_pce, number) IN ({placeholders})
                """,
                params,
            )
            rows = cur.fetchall()
            found_pairs = {(r[0], r[1]) for r in rows}
            not_found = [(p, k) for p, k in pairs if (p, k) not in found_pairs]
            self._enqueue_log(f"[OK] Commodity trovata per {len(found_pairs)}/{len(pairs)} coppie.", "ok")
            if not_found:
                self._enqueue_log(f"[WARN] {len(not_found)} coppia/e senza corrispondenza in agreement:", "warn")
                for p, k in not_found:
                    self._enqueue_log(f"[WARN]   • {p} / {k}", "warn")

            # 2. Truncate e populate z_dc_filter_import
            self._enqueue_log("[INFO] Popolamento z_dc_filter_import ...", "info")
            cur.execute("TRUNCATE TABLE public.z_dc_filter_import;")
            cur.executemany(
                """
                INSERT INTO public.z_dc_filter_import (supply_code, kraken_account, commodity)
                VALUES (%s, %s, %s)
                """,
                rows,
            )
            conn.commit()
            self._enqueue_log(f"[OK] {len(rows)} righe inserite in z_dc_filter_import.", "ok")

            # 3. Conteggio unico: mancanti in sap_filter_contract + presenti in on_hold
            self._enqueue_log("[INFO] Verifica record su sap_filter_contract e on_hold ...", "info")
            total_count = len(rows)
            cur.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE sfc.supply_code IS NULL AND oh.supply_code IS NULL) AS da_aggiungere,
                    COUNT(oh.supply_code)                                                       AS on_hold_count,
                    COUNT(sfc.supply_code)                                                      AS already_present
                FROM public.z_dc_filter_import fi
                LEFT JOIN public.sap_filter_contract sfc
                    ON fi.supply_code = sfc.supply_code AND fi.kraken_account = sfc.kraken_account
                LEFT JOIN public.sap_filter_contract_on_hold oh
                    ON fi.supply_code = oh.supply_code AND fi.kraken_account = oh.kraken_account
                """
            )
            missing_count, on_hold_count, already_present = cur.fetchone()
            for line in [
                "",
                f"  ┌─────────────────────┬───────┐",
                f"  │ Da aggiungere       │ {missing_count:>5} │",
                f"  │ In on hold          │ {on_hold_count:>5} │",
                f"  │ Già presenti        │ {already_present:>5} │",
                f"  ├─────────────────────┼───────┤",
                f"  │ Totale              │ {total_count:>5} │",
                f"  └─────────────────────┴───────┘",
                "",
            ]:
                self._log_queue.put((line, "info"))

            if missing_count == 0:
                self._enqueue_log("[WARN] Nessun record da aggiungere — flusso interrotto.", "warn")
                cur.close()
                conn.close()
                self.after(0, self._on_done, True)
                return

            # 4. INSERT sap_filter_contract_batch
            cur.execute(
                """
                INSERT INTO public.sap_filter_contract_batch
                    (end_time, filename, message, result, start_time, uuid)
                VALUES (%s, %s, NULL, 'OK', %s, NULL)
                RETURNING id
                """,
                (self._run_ts, filename, self._run_ts),
            )
            self._batch_id = cur.fetchone()[0]
            conn.commit()
            self._enqueue_log(f"[OK] Batch creato con ID: {self._batch_id}", "ok")

            # 5. INSERT sap_filter_contract dai record da aggiungere
            self._enqueue_log("[INFO] Inserimento record in sap_filter_contract ...", "info")
            cur.execute(
                """
                INSERT INTO sap_filter_contract
                    (commodity, contract, execute_time_stamp, kraken_account,
                     sap_list_supply_csv, supply_code, batch_id)
                SELECT
                    fi.commodity,
                    fi.contract,
                    %s,
                    fi.kraken_account,
                    %s,
                    fi.supply_code,
                    %s
                FROM z_dc_filter_import fi
                LEFT JOIN sap_filter_contract sfc
                    ON fi.supply_code = sfc.supply_code
                   AND fi.kraken_account = sfc.kraken_account
                WHERE sfc.supply_code IS NULL
                AND NOT EXISTS (
                    SELECT 1 FROM sap_filter_contract_on_hold oh
                    WHERE oh.supply_code = fi.supply_code
                      AND oh.kraken_account = fi.kraken_account
                )
                AND NOT EXISTS (
                    SELECT 1 FROM sap_filter_contract sfc2
                    WHERE sfc2.supply_code = fi.supply_code
                      AND sfc2.kraken_account = fi.kraken_account
                )
                """,
                (self._run_ts, cluster, self._batch_id),
            )
            inserted = cur.rowcount
            conn.commit()
            self._enqueue_log(f"[OK] {inserted} record inseriti in sap_filter_contract.", "ok")

            cur.close()
            conn.close()
            self.after(0, self._on_done, True)

        except Exception as e:
            self._enqueue_log(f"[ERRORE] {e}", "error")
            self.after(0, self._on_done, False)


_APPS = [
    {
        "key":     "hubconsole",
        "icon":    "🖥",
        "label":   "HUB Console",
        "minsize": (820, 560),
        "size":    (960, 660),
        "class":   None,
    },
    {
        "key":     "hub",
        "icon":    "🔄",
        "label":   "HUB Prod Sync",
        "minsize": (820, 560),
        "size":    (960, 660),
        "class":   None,
    },
    {
        "key":     "kraken",
        "icon":    "🐙",
        "label":   "Kraken Data Extractor",
        "minsize": (820, 620),
        "size":    (960, 720),
        "class":   None,
    },
    {
        "key":     "analysis",
        "icon":    "🔬",
        "label":   "Kraken Full Data Extractor",
        "minsize": (820, 560),
        "size":    (960, 660),
        "class":   None,
    },
    {
        "key":     "delta",
        "icon":    "⚡",
        "label":   "Delta Recovery",
        "minsize": (820, 560),
        "size":    (960, 660),
        "class":   None,
    },
    {
        "key":     "bonifica",
        "icon":    "🔧",
        "label":   "Bonifica PROD",
        "minsize": (820, 560),
        "size":    (960, 660),
        "class":   None,
    },
    {
        "key":     "cleaner",
        "icon":    "🧹",
        "label":   "Folder Cleaner",
        "minsize": (700, 520),
        "size":    (860, 620),
        "class":   None,
    },
    {
        "key":     "mover",
        "icon":    "📦",
        "label":   "Folder Mover",
        "minsize": (700, 520),
        "size":    (920, 640),
        "class":   None,
    },
    {
        "key":     "zipper",
        "icon":    "🗜",
        "label":   "ZIP Folder",
        "minsize": (700, 520),
        "size":    (960, 640),
        "class":   None,
    },
    {
        "key":     "ppfilter",
        "icon":    "💳",
        "label":   "Payment Plans Filter",
        "minsize": (820, 580),
        "size":    (960, 680),
        "class":   None,
    },
    {
        "key":     "jira",
        "icon":    "🎫",
        "label":   "Ticket Creator",
        "minsize": (960, 640),
        "size":    (1280, 800),
        "class":   None,
    },
    {
        "key":     "csvremover",
        "icon":    "📄",
        "label":   "CSV Header Remover",
        "minsize": (700, 520),
        "size":    (960, 640),
        "class":   None,
    },
    {
        "key":     "invoicewriter",
        "icon":    "🧾",
        "label":   "Invoice Writer",
        "minsize": (700, 520),
        "size":    (960, 640),
        "class":   None,
    },
    {
        "key":     "hfupdater",
        "icon":    "🔁",
        "label":   "Hub Filter Updater",
        "minsize": (820, 560),
        "size":    (960, 660),
        "class":   None,
    },
]

def _apply_dark_titlebar(hwnd, bg_hex: str = "#0f1117"):
    """Applica la title bar scura via DWM API (Windows 10 1903+ / Windows 11)."""
    try:
        import ctypes
        dwm = ctypes.windll.dwmapi

        # Dark mode (funziona da Windows 10 build 18985)
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        val = ctypes.c_int(1)
        dwm.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                                   ctypes.byref(val), ctypes.sizeof(val))

        # Colore sfondo title bar — Windows 11 only (DWMWA_CAPTION_COLOR = 35)
        r = int(bg_hex[1:3], 16)
        g = int(bg_hex[3:5], 16)
        b = int(bg_hex[5:7], 16)
        colorref = ctypes.c_uint32(r | (g << 8) | (b << 16))
        dwm.DwmSetWindowAttribute(hwnd, 35,
                                   ctypes.byref(colorref), ctypes.sizeof(colorref))
    except Exception:
        pass  # Windows più vecchi o errori DWM ignorati silenziosamente


class Launcher(_TkDnD.Tk if _HAS_DND else tkinter.Tk):

    def __init__(self):
        super().__init__()
        _setup_scrollbar_style()
        self._flag_icon = _make_flag_icon(master=self)
        self.iconphoto(True, self._flag_icon)
        self.after(1, self._set_flag_ico_windows)
        _APPS[0]["class"] = HubConsole
        _APPS[1]["class"] = HubProdSync
        _APPS[2]["class"] = KrakenDataExtractor
        _APPS[3]["class"] = KrakenFullDataExtractor
        _APPS[4]["class"] = DeltaRecovery
        _APPS[5]["class"] = BonificaProd
        _APPS[6]["class"] = FolderCleaner
        _APPS[7]["class"] = FolderMover
        _APPS[8]["class"] = ZipFolder
        _APPS[9]["class"] = PaymentPlansFilter
        _APPS[10]["class"] = JiraTicketCreator
        _APPS[11]["class"] = CsvBlankHeaderRemover
        _APPS[12]["class"] = InvoiceWriter
        _APPS[13]["class"] = HubFilterUpdater

        # Impedisce sleep, screensaver e spegnimento display
        # finché il tool è aperto (Windows only, silenzioso su altri OS)
        self._keepalive_set = False
        try:
            import ctypes
            ES_CONTINUOUS       = 0x80000000
            ES_SYSTEM_REQUIRED  = 0x00000001
            ES_DISPLAY_REQUIRED = 0x00000002
            ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
            self._keepalive_set = True
        except Exception:
            pass
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.configure(bg=_SB_BG)
        self.resizable(True, True)
        self.title("HUB Tool - All-in-one")

        self._current_key = None
        self._frames      = {}
        self._nav_btns    = {}
        self._env_buttons = {}
        _saved = _read_env_raw().get("TARGET_ENV", "INTEGRATION").upper()
        self._current_env = _saved if _saved in ("INTEGRATION", "RECETTE") else "INTEGRATION"

        self._build_sidebar()

        right_col = tkinter.Frame(self, bg=BG)
        right_col.pack(side="left", fill="both", expand=True)

        self._build_header(right_col)

        self._content = tkinter.Frame(right_col, bg=BG)
        self._content.pack(side="top", fill="both", expand=True)

        self._hdr_version.configure(text=f"v{VERSION_LAUNCHER}")

        self._select(_APPS[0]["key"])

        self.update_idletasks()
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            _apply_dark_titlebar(hwnd, BG)
        except Exception:
            pass
        w, h = _APPS[0]["size"]
        W = w + 72
        x = (self.winfo_screenwidth()  - W) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{W}x{h}+{x}+{y}")

    # ── Header unificato ──────────────────────────────────────────────────

    def _build_header(self, parent):
        hdr = tkinter.Frame(parent, bg=BG, pady=12)
        hdr.pack(fill="x", padx=20)

        # Sinistra: titolo + sottotitolo
        title_col = tkinter.Frame(hdr, bg=BG)
        title_col.pack(side="left")
        self._hdr_title = tkinter.Label(title_col, text="", bg=BG, fg=TEXT_PRI,
                                        font=("Consolas", 15, "bold"), anchor="w")
        self._hdr_title.pack(anchor="w")

        # Destra: versione + bottone ⚙ + bottoni ambiente
        right = tkinter.Frame(hdr, bg=BG)
        right.pack(side="right", anchor="center")

        self._hdr_version = tkinter.Label(right, text="", bg=BG, fg=TEXT_SEC,
                                          font=("Consolas", 9), padx=12)
        # versione spostata in basso

        self._info_btn = tkinter.Label(self)  # placeholder per compatibilità
        self._gear_btn = tkinter.Label(self)  # placeholder per compatibilità

        # Selettore ambiente — segmented control con animazione slide
        OPTIONS = [("Recette", "RECETTE"), ("Integration", "INTEGRATION")]
        SEG_H    = 26
        PAD_X    = 16
        FONT     = ("Consolas", 9, "bold")
        # Calcola larghezza di ogni opzione in base al testo
        tmp = tkinter.Label(self, font=FONT)
        opt_widths = []
        for label, _ in OPTIONS:
            tmp.configure(text=label)
            tmp.update_idletasks()
            opt_widths.append(tmp.winfo_reqwidth() + PAD_X * 2)
        tmp.destroy()
        half_w  = opt_widths[0]
        total_w = sum(opt_widths)

        seg = tkinter.Canvas(right, width=total_w, height=SEG_H,
                             bg=_SB_BG, highlightthickness=1,
                             highlightbackground=BORDER, cursor="hand2")
        seg.pack(side="left", padx=(0, 8))

        # Pill (rettangolo scorrevole)
        pill = seg.create_rectangle(0, 0, half_w, SEG_H,
                                    fill=ACCENT2, outline="")

        # Testi
        texts = []
        x_cursor = 0
        for i, (label, _) in enumerate(OPTIONS):
            cx = x_cursor + opt_widths[i] // 2
            t = seg.create_text(cx, SEG_H // 2, text=label,
                                font=FONT, fill=TEXT_PRI)
            texts.append(t)
            x_cursor += opt_widths[i]

        # Porta il pill sopra il testo (zorder)
        seg.tag_lower(pill)

        # Stato animazione
        self._seg_pill_x    = [0.0]
        self._seg_target_x  = [0.0]
        self._seg_anim_id   = [None]
        self._seg_canvas    = seg
        self._seg_pill      = pill
        self._seg_texts     = texts
        self._seg_opt_widths = opt_widths
        self._seg_h          = SEG_H
        self._seg_options    = [v for _, v in OPTIONS]

        def _update_colors():
            for i, (_, v) in enumerate(OPTIONS):
                seg.itemconfig(texts[i],
                               fill=TEXT_PRI if v == self._current_env else _SB_TEXT)

        def _animate():
            cur = self._seg_pill_x[0]
            tgt = self._seg_target_x[0]
            diff = tgt - cur
            if abs(diff) < 0.8:
                self._seg_pill_x[0] = tgt
                idx = self._seg_options.index(self._current_env)
                seg.coords(pill, tgt, 0, tgt + opt_widths[idx], SEG_H)
                _update_colors()
                return
            step = diff * 0.28
            self._seg_pill_x[0] = cur + step
            px = self._seg_pill_x[0]
            idx = self._seg_options.index(self._current_env)
            seg.coords(pill, px, 0, px + opt_widths[idx], SEG_H)
            _update_colors()
            self._seg_anim_id[0] = seg.after(14, _animate)

        def _on_click(e):
            x = e.x
            x_acc = 0
            for i, (_, value) in enumerate(OPTIONS):
                x_acc += opt_widths[i]
                if x < x_acc:
                    self._on_env_click(value)
                    break

        seg.bind("<Button-1>", _on_click)

        self._seg_animate   = _animate
        self._seg_update_colors = _update_colors

        # _env_buttons non usato ma manteniamo compatibilità
        for _, value in OPTIONS:
            self._env_buttons[value] = seg

        # ── Toggle Prod / Chopin (solo Jira Ticket Creator) ──────────────
        self._jira_env = "PROD"  # PROD o CHOPIN
        JIRA_OPTIONS = [("Prod", "PROD"), ("Chopin", "CHOPIN")]
        SEG_H2  = SEG_H
        tmp2 = tkinter.Label(self, font=FONT)
        jira_opt_widths = []
        for label, _ in JIRA_OPTIONS:
            tmp2.configure(text=label)
            tmp2.update_idletasks()
            jira_opt_widths.append(tmp2.winfo_reqwidth() + PAD_X * 2)
        tmp2.destroy()

        jseg = tkinter.Canvas(right, width=sum(jira_opt_widths), height=SEG_H2,
                              bg=_SB_BG, highlightthickness=1,
                              highlightbackground=BORDER, cursor="hand2")
        # Non packed subito — apparirà solo su Jira

        jpill = jseg.create_rectangle(0, 0, jira_opt_widths[0], SEG_H2,
                                      fill=ACCENT2, outline="")
        jtexts = []
        jx = 0
        for i, (label, _) in enumerate(JIRA_OPTIONS):
            cx = jx + jira_opt_widths[i] // 2
            t = jseg.create_text(cx, SEG_H2 // 2, text=label,
                                 font=FONT, fill=TEXT_PRI)
            jtexts.append(t)
            jx += jira_opt_widths[i]
        jseg.tag_lower(jpill)

        self._jseg_pill_x   = [0.0]
        self._jseg_target_x = [0.0]
        self._jseg_anim_id  = [None]
        self._jseg_canvas   = jseg
        self._jseg_pill     = jpill
        self._jseg_texts    = jtexts
        self._jseg_opt_widths = jira_opt_widths
        self._jseg_options  = [v for _, v in JIRA_OPTIONS]

        def _jira_update_colors():
            for i, (_, v) in enumerate(JIRA_OPTIONS):
                jseg.itemconfig(jtexts[i],
                                fill=TEXT_PRI if v == self._jira_env else _SB_TEXT)

        def _jira_animate():
            cur = self._jseg_pill_x[0]
            tgt = self._jseg_target_x[0]
            diff = tgt - cur
            if abs(diff) < 0.8:
                self._jseg_pill_x[0] = tgt
                idx = self._jseg_options.index(self._jira_env)
                jseg.coords(jpill, tgt, 0, tgt + jira_opt_widths[idx], SEG_H2)
                _jira_update_colors()
                return
            step = diff * 0.28
            self._jseg_pill_x[0] = cur + step
            px = self._jseg_pill_x[0]
            idx = self._jseg_options.index(self._jira_env)
            jseg.coords(jpill, px, 0, px + jira_opt_widths[idx], SEG_H2)
            _jira_update_colors()
            self._jseg_anim_id[0] = jseg.after(14, _jira_animate)

        def _on_jira_click(e):
            x = e.x
            x_acc = 0
            for i, (_, value) in enumerate(JIRA_OPTIONS):
                x_acc += jira_opt_widths[i]
                if x < x_acc:
                    self._jira_env = value
                    self._jseg_target_x[0] = sum(jira_opt_widths[:i])
                    if self._jseg_anim_id[0]:
                        jseg.after_cancel(self._jseg_anim_id[0])
                    _jira_animate()
                    break

        jseg.bind("<Button-1>", _on_jira_click)
        self._jseg_animate      = _jira_animate
        self._jseg_update_colors = _jira_update_colors

        tkinter.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=20)


    def _make_scrollable_canvas(self, win):
        """Crea canvas scrollabile con scrollbar auto-hide e mousewheel.
        Ritorna (canvas, inner) dove inner è il Frame contenuto."""
        canvas = tkinter.Canvas(win, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(win, orient="vertical", command=canvas.yview,
                            style="Dark.Vertical.TScrollbar")
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        def _scroll_set(first, last):
            if float(first) <= 0.0 and float(last) >= 1.0:
                if vsb.winfo_ismapped():
                    vsb.pack_forget()
            else:
                if not vsb.winfo_ismapped():
                    vsb.pack(side="right", fill="y", before=canvas)
            vsb.set(first, last)

        canvas.configure(yscrollcommand=_scroll_set)
        inner = tkinter.Frame(canvas, bg=BG)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_frame_configure(e):
            canvas.update_idletasks()
            content_h = inner.winfo_reqheight()
            canvas_h  = canvas.winfo_height()
            if content_h <= canvas_h:
                canvas.configure(scrollregion=(0, 0, 0, canvas_h))
                canvas.yview_moveto(0)
            else:
                canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_configure(e):
            canvas.itemconfig(win_id, width=e.width)
            _on_frame_configure(None)
        inner.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.bind("<Enter>", lambda e: canvas.bind_all(
            "<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units")))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        return canvas, inner

    def _open_settings(self):
        self._select_panel("settings")

    def _open_about(self):
        self._select_panel("about")

    def _select_panel(self, key):
        """Mostra about o settings nel frame principale senza popup."""
        if self._current_key == key:
            return
        self._current_key = key

        # Deseleziona tutto tramite _nav_btns (include about e settings)
        for k, (icon_lbl, label_lbl, indicator, btn_frame, inner) in self._nav_btns.items():
            bg = _SB_BG if k in ("about", "settings") else _SB_ITEM_BG
            indicator.configure(bg=bg)
            btn_frame.configure(bg=bg)
            inner.configure(bg=bg)
            icon_lbl.configure(bg=bg, fg=_SB_TEXT)
            label_lbl.configure(bg=bg, fg=_SB_TEXT)

        # Evidenzia il bottone selezionato
        if key in self._nav_btns:
            icon_lbl, label_lbl, indicator, btn_frame, inner = self._nav_btns[key]
            indicator.configure(bg=_SB_ACCENT2)
            btn_frame.configure(bg=_SB_BG_SEL)
            inner.configure(bg=_SB_BG_SEL)
            icon_lbl.configure(bg=_SB_BG_SEL, fg=_SB_TEXT_SEL)
            label_lbl.configure(bg=_SB_BG_SEL, fg=_SB_ACCENT)

        for f in self._content.winfo_children():
            f.pack_forget()

        if key not in self._frames:
            frame = tkinter.Frame(self._content, bg=BG)
            if key == "settings":
                self._build_settings_panel(frame)
            else:
                self._build_about_panel(frame)
            frame.pack(fill="both", expand=True)
            self._frames[key] = frame
        else:
            self._frames[key].pack(fill="both", expand=True)

        self._update_header(key)

    def _build_settings_panel(self, parent):
        from tkinter import ttk
        style = ttk.Style()
        style.configure("Env.TEntry",
                        fieldbackground=BG_INPUT, foreground=TEXT_PRI,
                        insertcolor=TEXT_PRI, borderwidth=1,
                        relief="flat", font=("Consolas", 10))

        style.configure("SettingsTab.TNotebook",
                        background=BG, borderwidth=0, tabmargins=[0, 0, 0, 0])
        style.configure("SettingsTab.TNotebook.Tab",
                        background=BG_CARD, foreground=TEXT_SEC,
                        font=("Consolas", 9), padding=[14, 3], borderwidth=0)
        style.map("SettingsTab.TNotebook.Tab",
                  background=[("selected", BG_CARD2), ("!selected", BG_CARD)],
                  foreground=[("selected", TEXT_PRI), ("!selected", TEXT_SEC)],
                  font=[("selected", ("Consolas", 9, "bold"))],
                  padding=[("selected", [14, 5]), ("!selected", [14, 3])])

        nb = ttk.Notebook(parent, style="SettingsTab.TNotebook")
        nb.pack(fill="both", expand=True)

        status_var = tkinter.StringVar(value="")
        tkinter.Label(parent, textvariable=status_var,
                      bg=BG, fg=TEXT_SEC, font=("Consolas", 8), anchor="w").pack(
                      side="bottom", fill="x", padx=16, pady=4)

        def _autosave(key, var):
            try:
                val = var.get().strip()
                keys = key.split("|")
                _write_env({k: val for k in keys})
                _reload_env()
                label = keys[0].replace("_SOURCE_TABLE", "").replace("_TABLE", "")
                status_var.set(f"✓ Salvato: {label}")
                parent.after(2000, lambda: status_var.set(""))
            except Exception as e:
                status_var.set(f"✗ Errore: {e}")

        for tab_label, tab_sections in SETTINGS_TABS:
            tab_frame = tkinter.Frame(nb, bg=BG)
            nb.add(tab_frame, text=f"  {tab_label}  ")

            canvas, inner = self._make_scrollable_canvas(tab_frame)

            for section_title, fields in tab_sections:
                card = tkinter.Frame(inner, bg=BG_CARD, bd=0,
                                     highlightthickness=1, highlightbackground=BORDER)
                card.pack(fill="x", padx=16, pady=(12, 0))
                tkinter.Label(card, text=section_title, bg=BG_CARD, fg=ACCENT,
                              font=("Consolas", 10, "bold"), pady=10, padx=16).pack(fill="x")
                tkinter.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=16)

                grid = tkinter.Frame(card, bg=BG_CARD)
                grid.pack(fill="x", padx=16, pady=8)
                grid.columnconfigure(1, weight=1)

                jira_vars: dict = {}
                for row_i, (key, label, is_pw) in enumerate(fields):
                    tkinter.Label(grid, text=label, bg=BG_CARD, fg=TEXT_SEC,
                                  font=("Consolas", 10), anchor="w",
                                  width=22).grid(row=row_i, column=0, sticky="w", pady=4)
                    var = tkinter.StringVar(value=_read_env_raw().get(key.split("|")[0], ""))
                    show = "*" if is_pw else ""
                    entry = ttk.Entry(grid, textvariable=var, show=show,
                                      style="Env.TEntry", font=("Consolas", 10))
                    entry.grid(row=row_i, column=1, sticky="ew", pady=4, padx=(8, 0))
                    # Jira Credenziali: salva solo al click del bottone, non all'edit
                    is_jira_cred = (section_title == "Credenziali" and
                                    tab_label == "🎫  Jira")
                    if not is_jira_cred:
                        entry.bind("<FocusOut>", lambda e, k=key, v=var: _autosave(k, v))
                        entry.bind("<Return>",   lambda e, k=key, v=var: _autosave(k, v))
                    else:
                        jira_vars[key] = var

                    if is_pw:
                        eye = tkinter.Label(grid, text="👁", bg=BG_CARD, fg=TEXT_SEC,
                                            cursor="hand2", font=("Consolas", 11))
                        eye.grid(row=row_i, column=2, padx=(4, 0))
                        def _toggle(e, ent=entry, el=eye):
                            if ent.cget("show") == "*":
                                ent.config(show=""); el.config(fg=ACCENT)
                            else:
                                ent.config(show="*"); el.config(fg=TEXT_SEC)
                        eye.bind("<Button-1>", _toggle)
                    elif key == "SSH_KEY_PATH":
                        browse = tkinter.Label(grid, text="📁", bg=BG_CARD, fg=TEXT_SEC,
                                               cursor="hand2", font=("Consolas", 11))
                        browse.grid(row=row_i, column=2, padx=(4, 0))
                        def _browse(e, v=var, k=key):
                            path = filedialog.askopenfilename(
                                title="Seleziona chiave SSH",
                                filetypes=[("Chiavi SSH", "*.pem *.ppk *.key *"),
                                           ("Tutti i file", "*.*")])
                            if path:
                                v.set(path)
                                _autosave(k, v)
                        browse.bind("<Button-1>", _browse)

                # Bottone Salva e Valida per la sezione Jira
                if section_title == "Credenziali" and tab_label == "🎫  Jira":
                    btn_row = tkinter.Frame(card, bg=BG_CARD)
                    btn_row.pack(fill="x", padx=16, pady=(0, 10))
                    jira_status = tkinter.StringVar(value="")
                    tkinter.Label(btn_row, textvariable=jira_status, bg=BG_CARD,
                                  fg=TEXT_SEC, font=("Consolas", 8),
                                  anchor="w").pack(side="left", fill="x", expand=True)

                    def _salva_e_valida(tab_lbl=tab_label, sec_title=section_title,
                                        js=jira_status, jvars=jira_vars):
                        js.set("⏳ Validazione in corso...")
                        # Legge i valori correnti dai campi (non ancora salvati)
                        url_v  = jvars.get("JIRA_URL",      tkinter.StringVar()).get().strip().rstrip("/")
                        user_v = jvars.get("JIRA_USERNAME", tkinter.StringVar()).get().strip()
                        pw_v   = jvars.get("JIRA_PASSWORD", tkinter.StringVar()).get()
                        def _worker():
                            try:
                                import requests as _req
                                from requests.auth import HTTPBasicAuth
                                if not url_v or not user_v:
                                    parent.after(0, lambda: js.set("⚠ URL o username mancante"))
                                    return
                                r = _req.get(f"{url_v}/rest/api/2/myself",
                                             auth=HTTPBasicAuth(user_v, pw_v),
                                             verify=False, timeout=10)
                                if r.ok:
                                    name = r.json().get("displayName", user_v)
                                    # Validazione OK — salva solo ora
                                    for k, v in jvars.items():
                                        _autosave(k, v)
                                    parent.after(0, lambda: js.set(f"✓ Connesso come {name} — credenziali salvate"))
                                else:
                                    parent.after(0, lambda: js.set(
                                        f"✗ Errore {r.status_code} — credenziali non salvate"))
                            except Exception as e:
                                parent.after(0, lambda: js.set(f"✗ {e} — credenziali non salvate"))
                        import threading as _thr
                        _thr.Thread(target=_worker, daemon=True).start()

                    tkinter.Button(btn_row, text="✔  Valida e Salva",
                                   command=_salva_e_valida,
                                   bg=BG_CARD, fg=SUCCESS,
                                   font=("Consolas", 10, "bold"),
                                   relief="flat", cursor="hand2",
                                   padx=10, pady=4, bd=0,
                                   activebackground=BG_HOVER,
                                   activeforeground=TEXT_PRI).pack(side="right")

            tkinter.Frame(inner, bg=BG).pack(pady=16)


    def _build_about_panel(self, parent):
        canvas, inner = self._make_scrollable_canvas(parent)

        hdr = tkinter.Frame(inner, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(30, 0))
        tkinter.Label(hdr, text="HUB Tool - All-in-one", bg=BG, fg=TEXT_PRI,
                      font=("Consolas", 16, "bold"), anchor="w").pack(anchor="w")
        tkinter.Label(hdr, text=f"v{VERSION_LAUNCHER}  |  Fatto a mano S.r.l.",
                      bg=BG, fg=TEXT_SEC, font=("Consolas", 9), anchor="w").pack(anchor="w", pady=(2, 0))
        tkinter.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=40, pady=(16, 0))

        APPS_SECTIONS = [
            ("🔄  HUB Prod Sync", [
                ("Cosa fa",
                 "Sincronizza le tabelle dal database HUB Produzione verso Integration o Recette "
                 "tramite tunnel SSH. Esegue TRUNCATE CASCADE + trasferimento bulk con cursore "
                 "server-side a batch da 10.000 righe — senza caricare l'intera tabella in memoria."),
                ("Tabelle sincronizzabili",
                 "Customer, Agreement, Sap filter contract, Identifier version map, "
                 "Sap old plan map, Old agreement id map. "
                 "Ogni tabella si abilita individualmente tramite le checkbox nel pannello sinistro."),
                ("Stop",
                 "Il bottone ■ Stop interrompe l'operazione al termine del batch corrente, "
                 "esegue rollback e chiude tutte le connessioni in modo pulito."),
            ]),
            ("🐙  Kraken Data Extractor", [
                ("Modalità operative",
                 "PRM — Estrae dati a partire da coppie PRM / Kraken Account fornite manualmente.\n\n"
                 "Identifier — Parte da una lista di document identifier. Recupera le invoice su Kraken, "
                 "estrae automaticamente le coppie PRM/Kraken Account e poi esegue i flussi secondari.\n\n"
                 "Reference — Parte da una lista di payment reference. Recupera i pagamenti, "
                 "estrae le coppie PRM/Kraken Account e poi esegue i flussi secondari."),
                ("Architettura connessioni",
                 "Kraken DB — Connessione diretta PostgreSQL al database sorgente (replica analytics).\n"
                 "SSH Tunnel — Tunnel sicuro verso Integration o Recette.\n"
                 "HUB DB — Lettura delle query SQL dalla tabella hub_config_query_kraken."),
                ("File di input",
                 "PRM: input/kraken data extractor/data_input.txt\n"
                 "Identifier: input/kraken data extractor/data_input_identifier.txt\n"
                 "Reference: input/kraken data extractor/data_input_reference.txt"),
            ]),
            ("🔬  Kraken Full Data Extractor", [
                ("Cosa fa",
                 "Estrae dati full (senza filtri) da Kraken PROD e li carica direttamente su HUB PROD "
                 "nelle tabelle j_kraken_*. Per ogni flow: TRUNCATE + estrazione Kraken + bulk insert "
                 "su HUB con cursore server-side a batch da 10.000 righe."),
                ("Tabelle estratte",
                 "Customer → j_kraken_customer\n"
                 "Agreement → j_kraken_agreement\n"
                 "Payment Plan (ELEC + GAS) → j_kraken_payment_plan\n"
                 "Renewal → j_kraken_renewal\n"
                 "Invoice (ELEC + GAS) → j_kraken_invoice\n"
                 "Payment (ELEC + GAS) → j_kraken_payments"),
                ("Tempi stimati",
                 "Dopo ogni esecuzione i tempi per flow vengono salvati nel .env (chiavi ADE_TIME_*) "
                 "e mostrati accanto alle checkbox come previsione per i run futuri. "
                 "Al passaggio del mouse appare un tooltip esplicativo."),
                ("Connessioni",
                 "Usa le stesse credenziali HUB e Kraken già configurate. "
                 "Le connessioni hanno TCP keepalive abilitato (idle 60s) per reggere "
                 "query che durano oltre un'ora. Reconnect automatico se la connessione HUB "
                 "cade durante il fetch. Il commento di ogni tabella viene aggiornato "
                 "con la data dell'ultima estrazione riuscita."),
            ]),
            ("⚡  Delta Recovery", [
                ("Cosa fa",
                 "Si connette al database HUB Produzione, estrae i pagamenti recuperabili "
                 "da ztemp_pp_delta_payment_cluster (sub_cluster = SCARTO HUB) che hanno un match "
                 "in payment_plans, li cerca nelle tabelle kraken ELE e GAS e inserisce i risultati "
                 "in test_payments / test_payments_gas su Recette o Integration via tunnel SSH."),
                ("Modalità operative",
                 "NO_PAYMENT_PLAN_FOUND — Pagamenti senza piano.\n\n"
                 "MULTIPLE_PAYMENT_PLAN_FOUND_FOR_PAYMENT_DATE — Pagamenti con più piani, risolti per conteggio.\n\n"
                 "NO_PAYMENT_PLAN_FOUND_FOR_PAYMENT_DATE — Pagamenti senza piano per la data specifica."),
                ("Tab Query",
                 "Le query SQL per ogni modalità sono modificabili e validabili direttamente dall'interfaccia. "
                 "Le modifiche vengono salvate nei file .sql in input/delta recovery/queries/. "
                 "Se il file non esiste viene usato il fallback hardcoded."),
            ]),
            ("🧹  Folder Cleaner", [
                ("Cosa fa",
                 "Elimina tutti i file e le sottocartelle dentro le cartelle configurate "
                 "(non le cartelle stesse). La cancellazione dei file avviene in parallelo, "
                 "le sottocartelle in sequenza con shutil.rmtree."),
                ("Configurazione",
                 "Le cartelle da pulire sono elencate in input/folder cleaner/folders.txt. "
                 "Si aggiungono tramite il bottone + e si rimuovono con la ✕ su ogni riga."),
            ]),
            ("📦  Folder Mover", [
                ("Cosa fa",
                 "Copia tutti i file da una cartella sorgente a una cartella destinazione. "
                 "La destinazione viene svuotata prima della copia. La copia è interrompibile."),
                ("Configurazione",
                 "Le coppie sorgente → destinazione si configurano in input/folder mover/folders.txt. "
                 "Si aggiungono tramite il bottone + selezionando prima la sorgente poi la destinazione. "
                 "Sorgente e destinazione identiche vengono rifiutate. "
                 "La ✕ su ogni riga rimuove quella coppia specifica."),
            ]),
            ("🗜  ZIP Folder", [
                ("Cosa fa",
                 "Comprime le cartelle selezionate in file ZIP individuali usando la compressione DEFLATE. "
                 "Il nome del file ZIP corrisponde al nome della cartella sorgente. "
                 "L'output viene salvato in output/zip folder/."),
                ("Filtro",
                 "È possibile filtrare i file da includere nello ZIP per sottostringa nel nome. "
                 "Se il filtro è disabilitato, tutti i file vengono compressi."),
                ("Configurazione",
                 "Le cartelle da comprimere sono elencate in input/zip folder/folders.txt. "
                 "La cartella di output è configurabile dal campo Output nel pannello."),
            ]),
            ("💳  Payment Plans Filter", [
                ("Cosa fa",
                 "Filtra file CSV (pattern K[EG]_PP_*.csv) mantenendo solo le righe che corrispondono "
                 "agli ID caricati nei file di filtro. Produce i file filtrati in una sottocartella "
                 "e li comprime in un file ZIP salvato in output/payment plans filter/."),
                ("Chiavi di filtro",
                 "Agreement ID — filtra per ID accordo.\n"
                 "Prm + Kraken Account — filtra per coppia prm;A-xxxxxxxx.\n"
                 "Agreement ID + Plan Type — filtra per coppia id;M|C|R|U."),
                ("File di filtro",
                 "I file di filtro si trovano in input/payment plans filter/. "
                 "Si modificano dalla tab Filtro con validazione automatica per tipo. "
                 "Ogni tab corrisponde a una chiave di filtro diversa."),
                ("Trasforma file",
                 "L'opzione 'Trasforma file ;C; → ;U;' sostituisce il valore C con U "
                 "nelle righe mantenute, utile per la bonifica dei payment plan."),
            ]),
            ("📄  CSV Header Remover", [
                ("Cosa fa",
                 "Rimuove la prima riga da file CSV e TXT, ma solo se è completamente vuota "
                 "(contiene esclusivamente caratteri di a capo: \\n, \\r\\n o \\r). "
                 "Se la prima riga contiene qualsiasi contenuto, il file viene saltato."),
                ("Output",
                 "I file processati vengono salvati in output/csv blank header remover/ "
                 "con il suffisso _no_head aggiunto al nome originale. "
                 "File molto grandi vengono gestiti a chunk da 64 MB senza caricarli in memoria."),
                ("Configurazione",
                 "I file da processare si aggiungono tramite il bottone + e si rimuovono "
                 "con la ✕ su ogni riga. La lista persiste in input/csv blank header remover/files.txt."),
            ]),
            ("🧾  Invoice Writer", [
                ("Cosa fa",
                 "Replica il flusso Java InvoiceService: legge le invoice direttamente da "
                 "Kraken (ELEC e GAS), filtrate per la lista di document identifier inserita "
                 "nella tab Data Input, le valida e genera i CSV SAP + ZIP in "
                 "output/invoice writer/."),
                ("Data Input",
                 "File: input/invoice writer/data_input.csv\n"
                 "Colonne: IDENTIFIER ; IMPORT_SUPPLIER_BILL_ID ; AGREEMENT_ID\n"
                 "IDENTIFIER obbligatorio (prefisso EB/GB), esattamente uno tra i due campi piano. "
                 "Validazione con evidenziazione in giallo delle righe non valide."),
                ("Database",
                 "Usa le credenziali HUB e Kraken già configurate. Nessuna configurazione separata."),
                ("Avvio",
                 "Esegue il flusso completo per ELEC e GAS in sequenza con log in tempo reale."),
            ]),
            ("🎫  Jira Ticket Creator", [
                ("Cosa fa",
                 "Crea ticket Jira direttamente dall'interfaccia. Supporta autenticazione Basic, "
                 "formattazione (bold, italic, link, liste), allegati drag & drop, template e "
                 "importazione da ticket esistente tramite chiave o URL."),
                ("Ambiente",
                 "Il toggle Prod / Chopin in alto a destra seleziona l'ambiente di destinazione. "
                 "Influenza il percorso nel file .cfg (PE1 per Prod, CE1 per Chopin)."),
                ("Assegnatario",
                 "Il bottone Valida verifica l'esistenza dell'utente su Jira tramite API "
                 "(/rest/api/2/user/search) prima di creare il ticket. "
                 "Se l'utente non esiste il flusso viene bloccato con un messaggio nel log."),
                ("File .cfg",
                 "La checkbox 'Crea file .cfg' prepopola i campi con valori fissi, li blocca in "
                 "sola lettura e abilita il bottone 'Preview .cfg'. "
                 "Il .cfg viene generato, allegato al ticket e salvato in output/jira ticket/cfg/. "
                 "Togliendo la spunta i campi tornano modificabili e vuoti."),
                ("Credenziali",
                 "JIRA_URL, JIRA_USERNAME, JIRA_PASSWORD salvati in config/.env. "
                 "Modificabili anche da Impostazioni → Jira."),
            ]),
            ("⚙  Configurazione", [
                ("Impostazioni",
                 "Tutte le credenziali e le impostazioni sono salvate in config/.env. "
                 "Si modificano dalla sezione Impostazioni nella sidebar in basso a sinistra. "
                 "I valori vengono salvati automaticamente al cambio di campo."),
                ("Ambiente DB",
                 "Il toggle Integration / Recette in alto a destra è visibile solo nelle sezioni "
                 "HUB Prod Sync, Kraken Data Extractor e Delta Recovery. "
                 "La scelta viene ricordata al riavvio."),
                ("Dipendenze",
                 "psycopg2-binary, python-dotenv, paramiko, sshtunnel, requests, tkinterdnd2. "
                 "Installate automaticamente alla prima esecuzione tramite pip. "
                 "La splash screen mostra l'avanzamento del caricamento ad ogni avvio."),
                ("Keep-alive",
                 "All'avvio il tool imposta SetThreadExecutionState su Windows per impedire "
                 "sleep, screensaver e spegnimento display. Viene rilasciato alla chiusura."),
            ]),
        ]
        text_labels = []
        for app_title, sections in APPS_SECTIONS:
            card = tkinter.Frame(inner, bg=BG_CARD, bd=0,
                                 highlightthickness=1, highlightbackground=BORDER)
            card.pack(fill="x", padx=40, pady=(16, 0))
            tkinter.Label(card, text=app_title, bg=BG_CARD, fg=TEXT_PRI,
                          font=("Consolas", 11, "bold"), pady=12, padx=20,
                          anchor="w").pack(fill="x")
            tkinter.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=20)
            body = tkinter.Frame(card, bg=BG_CARD)
            body.pack(fill="x", padx=20, pady=(8, 16))
            for sec_title, sec_text in sections:
                tkinter.Label(body, text=sec_title, bg=BG_CARD, fg=ACCENT,
                              font=("Consolas", 9, "bold"), anchor="w").pack(
                              fill="x", pady=(10, 2))
                lbl = tkinter.Label(body, text=sec_text, bg=BG_CARD, fg=TEXT_SEC,
                                    font=("Consolas", 9), anchor="w", justify="left",
                                    wraplength=560)
                lbl.pack(fill="x", padx=(8, 0))
                text_labels.append(lbl)

        def _update_wraplength(e):
            wl = max(200, e.width - 160)
            for lbl in text_labels:
                lbl.configure(wraplength=wl)
        inner.bind("<Configure>", _update_wraplength, add="+")
        tkinter.Frame(inner, bg=BG).pack(pady=20)

    def _on_env_click(self, value):
        self._current_env = value
        self._refresh_env_buttons(value)
        _write_env({"TARGET_ENV": value})

    def _refresh_env_buttons(self, current_value):
        if not hasattr(self, "_seg_animate"):
            return
        # Calcola posizione target del pill
        x_acc = 0
        for i, v in enumerate(self._seg_options):
            if v == current_value:
                self._seg_target_x[0] = float(x_acc)
                break
            x_acc += self._seg_opt_widths[i]
        # Cancella animazione precedente e riavvia
        if self._seg_anim_id[0]:
            self._seg_canvas.after_cancel(self._seg_anim_id[0])
        self._seg_animate()

    def _update_header(self, key):
        if key in ("about", "settings"):
            titles = {"about": "About", "settings": "Impostazioni"}
            self._hdr_title.configure(text=titles[key])
        else:
            app_cfg = next(a for a in _APPS if a["key"] == key)
            self._hdr_title.configure(text=app_cfg["label"])
        self._hdr_version.configure(text=f"v{VERSION_LAUNCHER}")
        self._refresh_env_buttons(self._current_env)

        # Mostra il selettore Recette/Integration solo nelle app DB
        # che lo utilizzano (non in Kraken Full Data Extractor)
        _SHOW_ENV_TOGGLE = {"hub", "kraken", "delta", "hubconsole", "bonifica"}
        if key in _SHOW_ENV_TOGGLE:
            self._seg_canvas.pack(side="left", padx=(0, 8))
        else:
            self._seg_canvas.pack_forget()

        # Mostra il selettore Prod/Chopin solo in Jira Ticket Creator
        if key == "jira":
            self._jseg_canvas.pack(side="left", padx=(0, 8))
        else:
            self._jseg_canvas.pack_forget()

    # ── Sidebar ───────────────────────────────────────────────────────────

    def _build_sidebar(self):
        sb = tkinter.Frame(self, bg=_SB_BG, width=150)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        top = tkinter.Frame(sb, bg=_SB_BG)
        top.pack(fill="x")

        logo = tkinter.Frame(top, bg=_SB_BG)
        logo.pack(pady=13)

        txt = tkinter.Frame(logo, bg=_SB_BG)
        txt.pack(side="left")
        tkinter.Label(txt, text="HUB", font=("Consolas", 14, "bold"),
                      fg=_SB_ACCENT, bg=_SB_BG, padx=0).pack(side="left", padx=0)
        tkinter.Label(txt, text="|", font=("Consolas", 14),
                      fg=_SB_BORDER, bg=_SB_BG, padx=2).pack(side="left", padx=0)
        tkinter.Label(txt, text="AIO", font=("Consolas", 14, "bold"),
                      fg=_SB_TEXT_SEL, bg=_SB_BG, padx=0).pack(side="left", padx=0)

        tkinter.Frame(sb, bg=_SB_BORDER, height=1).pack(fill="x")

        _SB_GROUPS = [
            ("db",   "🗄", "DATABASE", ["hubconsole", "hub", "kraken", "analysis", "delta", "bonifica", "hfupdater"]),
            ("file", "📁", "FILE",     ["cleaner", "mover", "zipper", "ppfilter", "csvremover", "invoicewriter"]),
            ("jira", "🎫", "JIRA",     ["jira"]),
        ]
        self._group_frames  = {}
        self._group_hdrs    = {}
        self._open_group    = tkinter.StringVar(value="")

        nav = tkinter.Frame(sb, bg=_SB_BG)
        nav.pack(fill="x")

        def _toggle_group(gid):
            hdr_f, chev = self._group_hdrs[gid]
            if self._group_frames[gid].winfo_ismapped():
                self._group_frames[gid].pack_forget()
                chev.configure(text="▶")
            else:
                self._group_frames[gid].pack(fill="x", after=hdr_f)
                chev.configure(text="▼")

        for gid, gicon, glabel, keys in _SB_GROUPS:
            # ── Header gruppo ─────────────────────────────────────────────
            hdr_frame = tkinter.Frame(nav, bg=_SB_BG_SEL, cursor="hand2")
            hdr_frame.pack(fill="x")

            tkinter.Label(hdr_frame, text=gicon, bg=_SB_BG_SEL, fg=_SB_TEXT,
                          font=("Consolas", 13), padx=6,
                          width=2, anchor="center").pack(side="left", fill="y")
            tkinter.Label(hdr_frame, text=glabel, bg=_SB_BG_SEL, fg=_SB_TEXT,
                          font=("Consolas", 10, "bold"), anchor="w",
                          pady=8).pack(side="left", fill="x", expand=True)
            chev_lbl = tkinter.Label(hdr_frame, text="▶", bg=_SB_BG_SEL, fg=_SB_TEXT,
                                     font=("Consolas", 9), padx=8)
            chev_lbl.pack(side="right")

            self._group_hdrs[gid] = (hdr_frame, chev_lbl)

            for w in [hdr_frame] + list(hdr_frame.winfo_children()):
                w.bind("<Button-1>", lambda e, g=gid: _toggle_group(g))

            # ── Items gruppo (non packato inizialmente) ───────────────────
            items_frame = tkinter.Frame(nav, bg=_SB_ITEM_BG)
            self._group_frames[gid] = items_frame

            for app in _APPS:
                key = app["key"]
                if key not in keys:
                    continue

                btn_frame = tkinter.Frame(items_frame, bg=_SB_ITEM_BG, cursor="hand2")
                btn_frame.pack(fill="x")

                indicator = tkinter.Frame(btn_frame, bg=_SB_ITEM_BG, width=3)
                indicator.pack(side="left", fill="y")

                icon = tkinter.Label(btn_frame, text=app["icon"],
                                     bg=_SB_ITEM_BG, fg=_SB_TEXT,
                                     font=("Consolas", 14), padx=6,
                                     width=2, anchor="center")
                icon.pack(side="left", fill="y")

                lbl = tkinter.Label(btn_frame, text=app["label"],
                                    bg=_SB_ITEM_BG, fg=_SB_TEXT,
                                    font=("Consolas", 9), anchor="w",
                                    wraplength=100, justify="left")
                lbl.pack(side="left", fill="x", expand=True, pady=2)

                self._nav_btns[key] = (icon, lbl, indicator, btn_frame, btn_frame)

                def _click(e, k=key):
                    self._select(k)

                def _enter(e, b=btn_frame, i=indicator, ic=icon, lb=lbl, k2=key):
                    if self._current_key == k2:
                        return
                    b.configure(bg=BG_HOVER)
                    ic.configure(bg=BG_HOVER)
                    lb.configure(bg=BG_HOVER)

                def _leave(e, b=btn_frame, i=indicator, ic=icon, lb=lbl, k2=key):
                    bg = _SB_BG_SEL if self._current_key == k2 else _SB_ITEM_BG
                    b.configure(bg=bg)
                    ic.configure(bg=bg)
                    lb.configure(bg=bg)

                for w in (btn_frame, icon, lbl):
                    w.bind("<Button-1>", _click)
                    w.bind("<Enter>",    _enter)
                    w.bind("<Leave>",    _leave)

        # Apri gruppo DB di default
        _toggle_group("db")

        # ── About e Impostazioni in fondo alla sidebar ────────────────────
        tkinter.Frame(sb, bg=_SB_BORDER, height=1).pack(side="bottom", fill="x")
        tkinter.Label(sb, text=f"v{VERSION_LAUNCHER}", bg=_SB_BG, fg=_SB_TEXT,
                      font=("Consolas", 8), anchor="center", pady=4
                      ).pack(side="bottom", fill="x")
        tkinter.Frame(sb, bg=_SB_BORDER, height=1).pack(side="bottom", fill="x")
        bottom_nav = tkinter.Frame(sb, bg=_SB_BG)
        bottom_nav.pack(side="bottom", fill="x")

        for key, icon, label, callback in [
            ("settings", "⚙", "Impostazioni", self._open_settings),
            ("about",    "ℹ", "About",         self._open_about),
        ]:
            btn_frame = tkinter.Frame(bottom_nav, bg=_SB_BG, cursor="hand2")
            btn_frame.pack(fill="x")

            indicator = tkinter.Frame(btn_frame, bg=_SB_BG, width=3)
            indicator.pack(side="left", fill="y")

            icon_lbl = tkinter.Label(btn_frame, text=icon, bg=_SB_BG, fg=_SB_TEXT,
                                     font=("Consolas", 14), padx=6, width=2,
                                     anchor="center")
            icon_lbl.pack(side="left", fill="y")

            lbl = tkinter.Label(btn_frame, text=label, bg=_SB_BG, fg=_SB_TEXT,
                                font=("Consolas", 9), anchor="w", pady=6)
            lbl.pack(side="left", fill="x", expand=True)

            self._nav_btns[key] = (icon_lbl, lbl, indicator, btn_frame, btn_frame)

            def _click(e, cb=callback):
                cb()

            def _enter(e, b=btn_frame, ic=icon_lbl, lb=lbl, k=key):
                if self._current_key == k:
                    return
                b.configure(bg=BG_HOVER)
                ic.configure(bg=BG_HOVER)
                lb.configure(bg=BG_HOVER)

            def _leave(e, b=btn_frame, ic=icon_lbl, lb=lbl, k=key):
                bg = _SB_BG_SEL if self._current_key == k else _SB_BG
                b.configure(bg=bg)
                ic.configure(bg=bg)
                lb.configure(bg=bg)

            for w in (btn_frame, icon_lbl, lbl):
                w.bind("<Button-1>", _click)
                w.bind("<Enter>",    _enter)
                w.bind("<Leave>",    _leave)

    def _hover(self, btn_frame, inner, entering, key=None):
        if key is not None and key == self._current_key:
            return
        bg = _SB_BG_SEL if entering else _SB_BG
        btn_frame.configure(bg=bg)
        inner.configure(bg=bg)
        for child in inner.winfo_children():
            child.configure(bg=bg)

    def _set_flag_ico_windows(self):
        """
        Crea un file .ico con la bandiera francese e lo imposta come icona
        del processo e della taskbar tramite Windows API.
        """
        try:
            import struct, ctypes

            ico_dir  = _HERE / "config" / "icon"
            ico_dir.mkdir(parents=True, exist_ok=True)
            ico_path = str(ico_dir / "hub_tool.ico")

            if not (ico_dir / "hub_tool.ico").exists():
                W = H = 32
                BLUE  = (149, 35,   0, 255)
                WHITE = (255, 255, 255, 255)
                RED   = ( 57,  41, 237, 255)
                pixels = []
                for row in range(H-1, -1, -1):
                    for col in range(W):
                        if col < W//3:       pixels.append(BLUE)
                        elif col < 2*W//3:   pixels.append(WHITE)
                        else:                pixels.append(RED)
                pixel_data = b"".join(struct.pack("4B", *p) for p in pixels)
                and_mask   = b"\x00" * (W * H // 8)
                bmp_size   = 40 + len(pixel_data) + len(and_mask)
                bmp  = struct.pack("<IiiHHIIiiII", 40, W, H*2, 1, 32, 0, len(pixel_data), 0, 0, 0, 0)
                bmp += pixel_data + and_mask
                ico  = struct.pack("<HHH", 0, 1, 1)
                ico += struct.pack("<BBBBHHII", W, H, 0, 0, 1, 32, bmp_size, 22)
                ico += bmp
                with open(ico_path, "wb") as f:
                    f.write(ico)

            self.iconbitmap(ico_path)
            # Ripristina iconphoto per i popup Toplevel (iconbitmap la sovrascrive)
            self.iconphoto(True, self._flag_icon)
            user32 = ctypes.windll.user32
            hwnd   = self.winfo_id()
            hicon  = user32.LoadImageW(None, ico_path, 1, 0, 0, 0x10)
            if hicon:
                user32.SendMessageW(hwnd, 0x0080, 0, hicon)
                user32.SendMessageW(hwnd, 0x0080, 1, hicon)

        except Exception:
            pass

    def _on_close(self):
        if self._keepalive_set:
            try:
                import ctypes
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)  # ES_CONTINUOUS only → reset
            except Exception:
                pass
        self.destroy()

    def _select(self, key):
        if key == self._current_key:
            return
        self._current_key = key

        for k, (icon_lbl, label_lbl, indicator, btn_frame, inner) in self._nav_btns.items():
            if k == key:
                indicator.configure(bg=_SB_ACCENT2)
                btn_frame.configure(bg=_SB_BG_SEL)
                inner.configure(bg=_SB_BG_SEL)
                icon_lbl.configure(bg=_SB_BG_SEL, fg=_SB_TEXT_SEL)
                label_lbl.configure(bg=_SB_BG_SEL, fg=_SB_ACCENT)
            else:
                bg = _SB_BG if k in ("about", "settings") else _SB_ITEM_BG
                indicator.configure(bg=bg)
                btn_frame.configure(bg=bg)
                inner.configure(bg=bg)
                icon_lbl.configure(bg=bg, fg=_SB_TEXT)
                label_lbl.configure(bg=bg, fg=_SB_TEXT)

        for f in self._content.winfo_children():
            f.pack_forget()

        if key not in self._frames:
            app_cfg = next(a for a in _APPS if a["key"] == key)
            frame = app_cfg["class"](self._content)
            frame.pack(fill="both", expand=True)
            self._frames[key] = frame
        else:
            self._frames[key].pack(fill="both", expand=True)

        app_cfg = next(a for a in _APPS if a["key"] == key)
        self.minsize(*app_cfg["minsize"])
        self._update_header(key)


def _migrate_env():
    """Aggiunge al .env le variabili di SETTINGS_SECTIONS non ancora presenti."""
    if not _ENV.exists():
        return []
    existing = set(_read_env_raw().keys())
    expected = [
        field[0]
        for _, fields in SETTINGS_SECTIONS
        for field in fields
    ]
    missing = [k for k in expected if k not in existing]
    if missing:
        _write_env({k: "" for k in missing})
    return missing


def _show_update_dialog(app):
    if not _UPDATE_INFO:
        return
    latest, url = _UPDATE_INFO

    popup = _tk.Toplevel(app)
    popup.title("Aggiornamento disponibile")
    popup.configure(bg=BG)
    popup.resizable(False, False)
    popup.grab_set()
    W, H = 420, 210
    x = app.winfo_x() + (app.winfo_width()  - W) // 2
    y = app.winfo_y() + (app.winfo_height() - H) // 2
    popup.geometry(f"{W}x{H}+{x}+{y}")

    outer = _tk.Frame(popup, bg=BORDER, bd=1)
    outer.pack(fill="both", expand=True, padx=1, pady=1)
    inner = _tk.Frame(outer, bg=BG)
    inner.pack(fill="both", expand=True, padx=1, pady=1)

    _tk.Label(inner, text="Aggiornamento disponibile",
              bg=BG, fg=TEXT_PRI, font=("Consolas", 12, "bold")).pack(pady=(20, 4))
    _tk.Label(inner, text=f"Versione attuale:  {VERSION_LAUNCHER}",
              bg=BG, fg=TEXT_SEC, font=("Consolas", 10)).pack()
    _tk.Label(inner, text=f"Nuova versione:    {latest}",
              bg=BG, fg=SUCCESS, font=("Consolas", 10, "bold")).pack(pady=(2, 16))

    _tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=20)

    status_var = _tk.StringVar()
    status_lbl = _tk.Label(inner, textvariable=status_var,
                           bg=BG, fg=TEXT_SEC, font=("Consolas", 9))
    status_lbl.pack(pady=(8, 0))

    btn_row = _tk.Frame(inner, bg=BG)
    btn_row.pack(pady=(6, 16))

    def _do_update():
        btn_aggiorna.configure(state="disabled")
        btn_dopo.configure(state="disabled")
        status_var.set("Download in corso...")
        popup.update()
        try:
            import requests as _req
            import shutil
            resp = _req.get(url, timeout=60, stream=True)
            resp.raise_for_status()
            current = Path(__file__)
            tmp = current.with_suffix(".pyw.new")
            with open(tmp, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            shutil.move(str(tmp), str(current))
            status_var.set("Aggiornato. Riavvio in corso...")
            popup.update()
            import subprocess
            subprocess.Popen([sys.executable, str(current)])
            sys.exit(0)
        except Exception as e:
            status_var.set(f"Errore: {e}")
            btn_dopo.configure(state="normal")

    btn_aggiorna = _tk.Button(
        btn_row, text="Aggiorna ora", command=_do_update,
        bg=ACCENT, fg="#ffffff", font=("Consolas", 10, "bold"),
        relief="flat", padx=18, pady=6, cursor="hand2",
        activebackground=ACCENT, activeforeground="#ffffff",
    )
    btn_aggiorna.pack(side="left", padx=(0, 10))

    btn_dopo = _tk.Button(
        btn_row, text="Più tardi", command=popup.destroy,
        bg=BG_CARD, fg=TEXT_SEC, font=("Consolas", 10),
        relief="flat", padx=18, pady=6, cursor="hand2",
        activebackground=BG_HOVER, activeforeground=TEXT_PRI,
    )
    btn_dopo.pack(side="left")


if __name__ == "__main__":
    _splash.set("Pronto.")
    _splash.progress(1.0)
    _splash._root.update()
    _splash._root.after(300, _splash.destroy)
    _splash._root.mainloop()
    _first_run = not _ENV.exists()
    if _first_run:
        _ENV.parent.mkdir(parents=True, exist_ok=True)
        _ENV.touch()

    _new_keys = [] if _first_run else _migrate_env()

    app = Launcher()
    app.lift()
    app.attributes("-topmost", True)
    app.after(200, lambda: app.attributes("-topmost", False))
    app.focus_force()

    if _first_run:
        def _show_first_run():
            popup = _tk.Toplevel(app)
            popup.title("Prima configurazione")
            popup.configure(bg=BG)
            popup.resizable(False, False)
            popup.grab_set()
            W, H = 440, 180
            x = app.winfo_x() + (app.winfo_width()  - W) // 2
            y = app.winfo_y() + (app.winfo_height() - H) // 2
            popup.geometry(f"{W}x{H}+{x}+{y}")

            outer = _tk.Frame(popup, bg=BORDER, bd=1)
            outer.pack(fill="both", expand=True, padx=1, pady=1)
            inner = _tk.Frame(outer, bg=BG)
            inner.pack(fill="both", expand=True, padx=1, pady=1)

            _tk.Label(inner, text="Benvenuto in HUB Tool AIO",
                      bg=BG, fg=TEXT_PRI, font=("Consolas", 12, "bold")).pack(pady=(20, 6))
            _tk.Label(inner,
                      text="Nessuna configurazione trovata.\nCompila le credenziali nella sezione Impostazioni per iniziare.",
                      bg=BG, fg=TEXT_SEC, font=("Consolas", 9), justify="center").pack(pady=(0, 16))
            _tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=20)

            def _go():
                popup.destroy()
                app._open_settings()

            _tk.Button(inner, text="Vai alle Impostazioni", command=_go,
                       bg=ACCENT, fg="#ffffff", font=("Consolas", 10, "bold"),
                       relief="flat", padx=18, pady=6, cursor="hand2",
                       activebackground=ACCENT, activeforeground="#ffffff").pack(pady=14)

        app.after(400, _show_first_run)
    elif _new_keys:
        def _show_migration_dialog():
            popup = _tk.Toplevel(app)
            popup.title("Nuove impostazioni disponibili")
            popup.configure(bg=BG)
            popup.resizable(False, False)
            popup.grab_set()
            W, H = 460, 210
            x = app.winfo_x() + (app.winfo_width()  - W) // 2
            y = app.winfo_y() + (app.winfo_height() - H) // 2
            popup.geometry(f"{W}x{H}+{x}+{y}")

            outer = _tk.Frame(popup, bg=BORDER, bd=1)
            outer.pack(fill="both", expand=True, padx=1, pady=1)
            inner = _tk.Frame(outer, bg=BG)
            inner.pack(fill="both", expand=True, padx=1, pady=1)

            _tk.Label(inner, text="Nuove impostazioni rilevate",
                      bg=BG, fg=TEXT_PRI, font=("Consolas", 12, "bold")).pack(pady=(18, 4))
            _tk.Label(inner,
                      text=f"Questo aggiornamento ha introdotto {len(_new_keys)} nuova/e variabile/i\n"
                           f"nel file di configurazione. Compilale per usare le nuove funzionalità.",
                      bg=BG, fg=TEXT_SEC, font=("Consolas", 9), justify="center").pack(pady=(0, 4))

            keys_text = "  •  " + "\n  •  ".join(_new_keys)
            _tk.Label(inner, text=keys_text, bg=BG, fg=WARNING,
                      font=("Consolas", 9), justify="left").pack(pady=(0, 12))

            _tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=20)

            def _go():
                popup.destroy()
                app._open_settings()

            btn_row = _tk.Frame(inner, bg=BG)
            btn_row.pack(pady=12)
            _tk.Button(btn_row, text="Vai alle Impostazioni", command=_go,
                       bg=ACCENT, fg="#ffffff", font=("Consolas", 10, "bold"),
                       relief="flat", padx=18, pady=6, cursor="hand2",
                       activebackground=ACCENT, activeforeground="#ffffff").pack(side="left", padx=(0, 10))
            _tk.Button(btn_row, text="Più tardi", command=popup.destroy,
                       bg=BG_CARD, fg=TEXT_SEC, font=("Consolas", 10),
                       relief="flat", padx=18, pady=6, cursor="hand2",
                       activebackground=BG_HOVER, activeforeground=TEXT_PRI).pack(side="left")

        app.after(500, _show_migration_dialog)
    else:
        app.after(500, lambda: _show_update_dialog(app))

    app.mainloop()