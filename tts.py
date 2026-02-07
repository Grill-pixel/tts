import importlib
import pkgutil
import io
import linecache
import logging
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
LOG_FILE = Path("logs.txt")


def initialize_logging():
    logging.info("Initialisation du système de logs.")
    if LOG_FILE.exists():
        LOG_FILE.unlink()
    LOG_FILE.write_text("", encoding="utf-8")
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )
    logging.info("--- LOG SYSTEM INITIALIZED ---")


def install_exception_logger():
    logging.debug("Installation du gestionnaire d'exceptions.")
    def handle_exception(exc_type, exc_value, exc_traceback):
        logging.critical(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = handle_exception


def install_line_tracer():
    logging.debug("Activation du traçage ligne par ligne.")
    module_path = Path(__file__).resolve()

    def trace_lines(frame, event, arg):
        if event != "line":
            return trace_lines
        if Path(frame.f_code.co_filename).resolve() != module_path:
            return trace_lines
        line_no = frame.f_lineno
        line_text = linecache.getline(frame.f_code.co_filename, line_no).rstrip()
        logging.debug("TRACE %s:%s %s", module_path.name, line_no, line_text)
        return trace_lines

    sys.settrace(trace_lines)
    threading.settrace(trace_lines)


@dataclass
class Dependency:
    module: str
    pip_name: str
    description: str


REQUIRED_DEPENDENCIES = [
    Dependency(module="groq", pip_name="groq", description="Client API Groq"),
    Dependency(module="pydub", pip_name="pydub", description="Lecture et manipulation audio"),
]

# ----------------- API Key -----------------
API_KEY_FILE = Path("api_key.txt")

def get_api_key():
    logging.debug("Lecture de la clé API depuis %s.", API_KEY_FILE)
    if API_KEY_FILE.exists():
        return API_KEY_FILE.read_text().strip()
    return ""

def save_api_key(key):
    API_KEY_FILE.write_text(key, encoding="utf-8")
    logging.info("Clé API sauvegardée.")


def show_error(title, message):
    logging.error("Affichage erreur: %s - %s", title, message)
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(title, message)
    root.destroy()


def check_missing_dependencies():
    logging.debug("Vérification des dépendances manquantes.")
    missing = []
    find_spec = None
    importlib_util = getattr(importlib, "util", None)
    importlib_machinery = getattr(importlib, "machinery", None)
    if importlib_util and hasattr(importlib_util, "find_spec"):
        find_spec = importlib_util.find_spec
    elif importlib_machinery and hasattr(importlib_machinery, "PathFinder"):
        find_spec = importlib_machinery.PathFinder.find_spec
    for dep in REQUIRED_DEPENDENCIES:
        if find_spec:
            spec = find_spec(dep.module)
        else:
            spec = pkgutil.find_loader(dep.module)
        if spec is None:
            missing.append(dep)
            logging.debug("Dépendance manquante: %s (%s)", dep.module, dep.pip_name)
    return missing


def install_dependency(dep):
    logging.info("Installation du module %s…", dep.pip_name)
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", dep.pip_name],
        capture_output=True,
        text=True,
        check=False
    )
    logging.info("Sortie pip: %s", result.stdout.strip())
    if result.returncode != 0:
        logging.error("Erreur pip: %s", result.stderr.strip())
    return result.returncode == 0


def load_dependencies():
    logging.debug("Chargement des dépendances.")
    import_module = getattr(importlib, "import_module", None)
    if not import_module:
        def import_module(name):
            return __import__(name, fromlist=["*"])
    groq_module = import_module("groq")
    pydub_module = import_module("pydub")
    playback_module = import_module("pydub.playback")
    return groq_module, pydub_module.AudioSegment, playback_module.play


class DependencyManager(tk.Tk):
    def __init__(self):
        logging.debug("Initialisation de la fenêtre DependencyManager.")
        super().__init__()
        self.title("Installation des bibliothèques")
        self.geometry("620x360")
        self.resizable(False, False)
        self.missing = check_missing_dependencies()
        self.status_vars = {}
        self.next_ready = tk.BooleanVar(value=False)
        self._build_ui()
        self._refresh_status()

    def _build_ui(self):
        logging.debug("Construction UI DependencyManager.")
        self.configure(padx=16, pady=16)
        title = ttk.Label(self, text="Vérification des dépendances", font=("Segoe UI", 14, "bold"))
        title.pack(anchor="w")

        subtitle = ttk.Label(
            self,
            text="Les bibliothèques manquantes sont listées ci-dessous. Installez-les une par une.",
            foreground="#555"
        )
        subtitle.pack(anchor="w", pady=(4, 12))

        self.dep_frame = ttk.Frame(self)
        self.dep_frame.pack(fill="both", expand=True)

        if not self.missing:
            ttk.Label(self.dep_frame, text="Toutes les bibliothèques sont déjà installées.").pack(anchor="w")
        else:
            for dep in self.missing:
                row = ttk.Frame(self.dep_frame)
                row.pack(fill="x", pady=4)
                info = ttk.Label(row, text=f"{dep.module} — {dep.description}")
                info.pack(side="left", padx=(0, 8))
                status_var = tk.StringVar(value="Manquante")
                self.status_vars[dep.module] = status_var
                status_label = ttk.Label(row, textvariable=status_var, foreground="#b91c1c")
                status_label.pack(side="left", padx=(0, 12))
                install_button = ttk.Button(row, text="Installer", command=lambda d=dep: self._install_one(d))
                install_button.pack(side="right")

        self.progress = ttk.Label(self, text="")
        self.progress.pack(anchor="w", pady=(10, 0))

        self.next_button = ttk.Button(self, text="Next", command=self._finish)
        self.next_button.pack(anchor="e", pady=(12, 0))
        self.next_button.state(["disabled"])

    def _install_one(self, dep):
        logging.debug("Installation demandée pour %s.", dep.pip_name)
        self.progress.config(text=f"Installation en cours: {dep.pip_name}…")
        self.update_idletasks()
        success = install_dependency(dep)
        if success:
            self.status_vars[dep.module].set("Installée")
            self.progress.config(text=f"{dep.pip_name} installée.")
        else:
            self.progress.config(text=f"Échec installation {dep.pip_name}. Consultez logs.txt.")
            messagebox.showerror("Erreur", f"Impossible d'installer {dep.pip_name}.")
        self._refresh_status()

    def _refresh_status(self):
        logging.debug("Rafraîchissement statut dépendances.")
        missing = check_missing_dependencies()
        if not missing:
            self.next_ready.set(True)
            self.next_button.state(["!disabled"])
        else:
            self.next_ready.set(False)
            self.next_button.state(["disabled"])

    def _finish(self):
        logging.debug("Fermeture DependencyManager.")
        self.destroy()


class ApiKeyWindow(tk.Tk):
    def __init__(self, existing_key):
        logging.debug("Initialisation de la fenêtre ApiKeyWindow.")
        super().__init__()
        self.title("Clé API Groq")
        self.geometry("420x220")
        self.resizable(False, False)
        self.api_key = None
        self._build_ui(existing_key)

    def _build_ui(self, existing_key):
        logging.debug("Construction UI ApiKeyWindow.")
        self.configure(padx=20, pady=20)
        ttk.Label(self, text="Entrez votre clé API Groq", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(
            self,
            text="Elle sera enregistrée localement dans api_key.txt pour les prochains lancements.",
            foreground="#555"
        ).pack(anchor="w", pady=(4, 12))

        self.entry = ttk.Entry(self, width=44)
        self.entry.pack(fill="x")
        self.entry.insert(0, existing_key)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", pady=(16, 0))
        ttk.Button(btn_frame, text="Annuler", command=self._cancel).pack(side="right", padx=(6, 0))
        ttk.Button(btn_frame, text="Valider", command=self._submit).pack(side="right")

    def _submit(self):
        logging.debug("Validation clé API.")
        value = self.entry.get().strip()
        if not value:
            messagebox.showerror("Erreur", "Clé API vide.")
            return
        self.api_key = value
        self.destroy()

    def _cancel(self):
        logging.debug("Annulation saisie clé API.")
        self.api_key = None
        self.destroy()

# ----------------- TTS App -----------------
class TTSApp:
    def __init__(self, master, api_key, groq_module, audio_segment, play_audio):
        logging.debug("Initialisation de TTSApp.")
        self.master = master
        self.master.title("TTS Orpheus")
        self.api_key = api_key
        self.groq_module = groq_module
        self.audio_segment = audio_segment
        self.play_audio = play_audio
        self.client = self.groq_module.Client(api_key=self.api_key)

        self.selected_model = tk.StringVar()
        self.selected_voice = tk.StringVar()

        self.models = []
        self.voices = []

        self.build_ui()
        self.fetch_models()

    def build_ui(self):
        logging.debug("Construction UI TTSApp.")
        frame = ttk.Frame(self.master, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Modèle TTS
        ttk.Label(frame, text="Modèle TTS:").grid(row=0, column=0, sticky="w")
        self.model_combo = ttk.Combobox(frame, textvariable=self.selected_model, state="readonly")
        self.model_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        # Voix
        ttk.Label(frame, text="Voix:").grid(row=1, column=0, sticky="w")
        self.voice_combo = ttk.Combobox(frame, textvariable=self.selected_voice, state="readonly")
        self.voice_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        # Texte
        ttk.Label(frame, text="Texte:").grid(row=2, column=0, sticky="nw")
        self.text_entry = tk.Text(frame, height=6, width=48, wrap="word")
        self.text_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        # Boutons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Lire", command=self.read_text).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Sauvegarder (.wav)", command=self.save_text).grid(row=0, column=1, padx=5)

        frame.columnconfigure(1, weight=1)

    def fetch_models(self):
        logging.info("Récupération des modèles disponibles…")
        try:
            response = self.client.models.list()
            self.models = [m.id for m in response.data if "orpheus" in m.id.lower()]
            if not self.models:
                logging.warning("Aucun modèle Orpheus détecté.")
                messagebox.showerror("Erreur", "Aucun modèle TTS Orpheus disponible.")
                return
            self.model_combo["values"] = self.models
            self.selected_model.set(self.models[0])
            self.fetch_voices()
            logging.info(f"Modèles TTS détectés: {self.models}")
        except Exception as e:
            logging.error(f"Erreur récupération modèles: {e}")
            messagebox.showerror("Erreur", f"Impossible de récupérer les modèles: {e}")

    def fetch_voices(self):
        # Ici on peut définir quelques voix par défaut pour Orpheus
        logging.debug("Chargement des voix par défaut.")
        self.voices = ["autumn", "spring", "summer", "winter"]
        self.voice_combo["values"] = self.voices
        self.selected_voice.set(self.voices[0])

    def _notify(self, title, message, level="info"):
        logging.debug("Notification %s: %s", level, message)
        def _show():
            if level == "error":
                messagebox.showerror(title, message)
            elif level == "warning":
                messagebox.showwarning(title, message)
            else:
                messagebox.showinfo(title, message)
        self.master.after(0, _show)

    def generate_speech_bytes(self, text, model, voice):
        logging.debug("Génération TTS demandée. Modèle=%s Voix=%s", model, voice)
        try:
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                response_format="wav"  # Groq Orpheus supporte wav
            )
            audio_bytes = bytes(response)
            logging.info("Audio reçu depuis l'API.")
            return audio_bytes
        except Exception as e:
            logging.error(f"Génération a échoué: {e}")
            return None

    def read_text(self):
        logging.debug("Lecture du texte demandée.")
        text = self.text_entry.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Attention", "Veuillez saisir un texte.")
            return
        model = self.selected_model.get()
        voice = self.selected_voice.get()

        def worker():
            logging.debug("Thread lecture démarré.")
            audio_bytes = self.generate_speech_bytes(text, model, voice)
            if audio_bytes:
                audio = self.audio_segment.from_file(io.BytesIO(audio_bytes), format="wav")
                self.play_audio(audio)
            else:
                self._notify("Erreur", "Génération TTS échouée.", level="error")
        threading.Thread(target=worker, daemon=True).start()

    def save_text(self):
        logging.debug("Sauvegarde du texte demandée.")
        text = self.text_entry.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Attention", "Veuillez saisir un texte.")
            return
        model = self.selected_model.get()
        voice = self.selected_voice.get()

        out_path = filedialog.asksaveasfilename(defaultextension=".wav",
                                                filetypes=[("WAV", "*.wav")])
        if not out_path:
            return

        def worker():
            logging.debug("Thread sauvegarde démarré.")
            audio_bytes = self.generate_speech_bytes(text, model, voice)
            if not audio_bytes:
                self._notify("Erreur", "Génération TTS échouée.", level="error")
                return
            Path(out_path).write_bytes(audio_bytes)
            logging.info(f"Fichier audio sauvegardé: {out_path}")
            self._notify("Succès", f"Fichier sauvegardé: {out_path}")
        threading.Thread(target=worker, daemon=True).start()


# ----------------- Main -----------------
def main():
    logging.debug("Entrée dans main.")
    initialize_logging()
    install_exception_logger()
    install_line_tracer()

    try:
        logging.debug("Lancement DependencyManager.")
        dependency_window = DependencyManager()
        dependency_window.mainloop()

        if check_missing_dependencies():
            show_error(
                "Dépendances manquantes",
                "Certaines bibliothèques sont toujours manquantes. Installation requise."
            )
            sys.exit(1)

        logging.debug("Chargement des dépendances applicatives.")
        groq_module, audio_segment, play_audio = load_dependencies()

        logging.debug("Ouverture fenêtre clé API.")
        api_key_window = ApiKeyWindow(get_api_key())
        api_key_window.mainloop()
        api_key = api_key_window.api_key
        if not api_key:
            show_error("Erreur", "Clé API vide")
            sys.exit(1)
        save_api_key(api_key)

        logging.debug("Démarrage interface principale.")
        main_root = tk.Tk()
        app = TTSApp(main_root, api_key, groq_module, audio_segment, play_audio)
        main_root.mainloop()
    except Exception:
        logging.exception("Erreur inattendue pendant l'exécution.")
        raise


if __name__ == "__main__":
    main()
