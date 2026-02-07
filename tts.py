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
import winsound  # Module Windows natif pour lire des WAV

LOG_FILE = Path("logs.txt")


def initialize_logging():
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
    def handle_exception(exc_type, exc_value, exc_traceback):
        logging.critical(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    sys.excepthook = handle_exception


def install_line_tracer():
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
]


API_KEY_FILE = Path("api_key.txt")

def get_api_key():
    if API_KEY_FILE.exists():
        return API_KEY_FILE.read_text().strip()
    return ""

def save_api_key(key):
    API_KEY_FILE.write_text(key, encoding="utf-8")
    logging.info("Clé API sauvegardée.")


def show_error(title, message):
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(title, message)
    root.destroy()


def check_missing_dependencies():
    if hasattr(importlib, "invalidate_caches"):
        importlib.invalidate_caches()
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
    return missing


def install_dependency(dep):
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", dep.pip_name],
        capture_output=True,
        text=True,
        check=False
    )
    logging.info("pip output: %s", result.stdout.strip())
    if result.returncode != 0:
        logging.error("pip error: %s", result.stderr.strip())
    return result.returncode == 0


def load_dependencies():
    import_module = getattr(importlib, "import_module", None)
    if not import_module:
        def import_module(name):
            return __import__(name, fromlist=["*"])
    groq_module = import_module("groq")
    return groq_module


class DependencyManager(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Installation des bibliothèques")
        self.geometry("620x360")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._finish)
        self._show_modal()
        self.missing = check_missing_dependencies()
        self.status_vars = {}
        self.next_ready = tk.BooleanVar(value=False)
        self._build_ui()
        self._refresh_status()

    def _build_ui(self):
        self.configure(padx=16, pady=16)
        ttk.Label(self, text="Vérification des dépendances", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(self, text="Les bibliothèques manquantes sont listées ci-dessous. Installez-les une par une.", foreground="#555").pack(anchor="w", pady=(4, 12))
        self.dep_frame = ttk.Frame(self)
        self.dep_frame.pack(fill="both", expand=True)

        if not self.missing:
            ttk.Label(self.dep_frame, text="Toutes les bibliothèques sont déjà installées.").pack(anchor="w")
        else:
            for dep in self.missing:
                row = ttk.Frame(self.dep_frame)
                row.pack(fill="x", pady=4)
                ttk.Label(row, text=f"{dep.module} — {dep.description}").pack(side="left", padx=(0, 8))
                status_var = tk.StringVar(value="Manquante")
                self.status_vars[dep.module] = status_var
                ttk.Label(row, textvariable=status_var, foreground="#b91c1c").pack(side="left", padx=(0, 12))
                ttk.Button(row, text="Installer", command=lambda d=dep: self._install_one(d)).pack(side="right")

        self.progress = ttk.Label(self, text="")
        self.progress.pack(anchor="w", pady=(10, 0))
        self.next_button = ttk.Button(self, text="Suivant", command=self._finish)
        self.next_button.pack(anchor="e", pady=(12, 0))
        self.next_button.state(["disabled"])

    def _install_one(self, dep):
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
        missing = check_missing_dependencies()
        if not missing:
            self.next_ready.set(True)
            self.next_button.state(["!disabled"])
            self.after(200, self._finish)
        else:
            self.next_ready.set(False)
            self.next_button.state(["disabled"])

    def _finish(self):
        self.grab_release()
        self.destroy()

    def _show_modal(self):
        self.update_idletasks()
        self.deiconify()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(250, lambda: self.attributes("-topmost", False))


class ApiKeyWindow(tk.Toplevel):
    def __init__(self, master, existing_key):
        super().__init__(master)
        self.title("Clé API Groq")
        self.geometry("420x220")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self._show_modal()
        self.api_key = None
        self._build_ui(existing_key)

    def _build_ui(self, existing_key):
        self.configure(padx=20, pady=20)
        ttk.Label(self, text="Entrez votre clé API Groq", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(self, text="Elle sera enregistrée localement dans api_key.txt.", foreground="#555").pack(anchor="w", pady=(4, 12))
        self.entry = ttk.Entry(self, width=44)
        self.entry.pack(fill="x")
        self.entry.insert(0, existing_key)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", pady=(16, 0))
        ttk.Button(btn_frame, text="Annuler", command=self._cancel).pack(side="right", padx=(6, 0))
        ttk.Button(btn_frame, text="Valider", command=self._submit).pack(side="right")

    def _submit(self):
        value = self.entry.get().strip()
        if not value:
            messagebox.showerror("Erreur", "Clé API vide.")
            return
        self.api_key = value
        self.grab_release()
        self.destroy()

    def _cancel(self):
        self.api_key = None
        self.grab_release()
        self.destroy()

    def _show_modal(self):
        self.update_idletasks()
        self.deiconify()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(250, lambda: self.attributes("-topmost", False))


class TTSApp:
    def __init__(self, master, api_key, groq_module):
        self.master = master
        self.master.title("TTS Orpheus")
        self.api_key = api_key
        self.groq_module = groq_module
        self.client = self.groq_module.Client(api_key=self.api_key)
        self.selected_model = tk.StringVar()
        self.selected_voice = tk.StringVar()
        self.models = []
        self.voices = []
        self.build_ui()
        self.fetch_models()

    def build_ui(self):
        frame = ttk.Frame(self.master, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="Modèle TTS:").grid(row=0, column=0, sticky="w")
        self.model_combo = ttk.Combobox(frame, textvariable=self.selected_model, state="readonly")
        self.model_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(frame, text="Voix:").grid(row=1, column=0, sticky="w")
        self.voice_combo = ttk.Combobox(frame, textvariable=self.selected_voice, state="readonly")
        self.voice_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(frame, text="Texte:").grid(row=2, column=0, sticky="nw")
        self.text_entry = tk.Text(frame, height=6, width=48, wrap="word")
        self.text_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Lire", command=self.read_text).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Sauvegarder (.wav)", command=self.save_text).grid(row=0, column=1, padx=5)

        frame.columnconfigure(1, weight=1)

    def fetch_models(self):
        try:
            response = self.client.models.list()
            self.models = [m.id for m in response.data if "orpheus" in m.id.lower()]
            if not self.models:
                messagebox.showerror("Erreur", "Aucun modèle TTS Orpheus disponible.")
                return
            self.model_combo["values"] = self.models
            self.selected_model.set(self.models[0])
            self.voices = ["autumn", "spring", "summer", "winter"]
            self.voice_combo["values"] = self.voices
            self.selected_voice.set(self.voices[0])
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de récupérer les modèles: {e}")

    def generate_speech_bytes(self, text, model, voice):
        try:
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                response_format="wav"
            )
            return bytes(response), None
        except Exception as e:
            return None, f"Génération TTS échouée: {e}"

    def _notify_error(self, title, message):
        self.master.after(0, lambda: messagebox.showerror(title, message))

    def _notify_info(self, title, message):
        self.master.after(0, lambda: messagebox.showinfo(title, message))

    def read_text(self):
        text = self.text_entry.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Attention", "Veuillez saisir un texte.")
            return
        model = self.selected_model.get()
        voice = self.selected_voice.get()

        def worker():
            audio_bytes, error = self.generate_speech_bytes(text, model, voice)
            if error:
                self._notify_error("Erreur", error)
                return
            if audio_bytes:
                temp_file = "temp_tts.wav"
                Path(temp_file).write_bytes(audio_bytes)
                winsound.PlaySound(temp_file, winsound.SND_FILENAME)
        threading.Thread(target=worker, daemon=True).start()

    def save_text(self):
        text = self.text_entry.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Attention", "Veuillez saisir un texte.")
            return
        model = self.selected_model.get()
        voice = self.selected_voice.get()
        out_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV", "*.wav")])
        if not out_path:
            return

        def worker():
            audio_bytes, error = self.generate_speech_bytes(text, model, voice)
            if error:
                self._notify_error("Erreur", error)
                return
            if audio_bytes:
                Path(out_path).write_bytes(audio_bytes)
                self._notify_info("Succès", f"Fichier sauvegardé: {out_path}")
        threading.Thread(target=worker, daemon=True).start()


def main():
    initialize_logging()
    install_exception_logger()
    install_line_tracer()
    try:
        root = tk.Tk()
        root.withdraw()
        dependency_window = DependencyManager(root)
        root.wait_window(dependency_window)

        if check_missing_dependencies():
            show_error("Dépendances manquantes", "Certaines bibliothèques sont toujours manquantes.")
            sys.exit(1)

        api_key_window = ApiKeyWindow(root, get_api_key())
        root.wait_window(api_key_window)
        api_key = api_key_window.api_key
        if not api_key:
            show_error("Erreur", "Clé API vide")
            sys.exit(1)
        save_api_key(api_key)

        groq_module = load_dependencies()

        root.deiconify()
        app = TTSApp(root, api_key, groq_module)
        root.mainloop()
    except Exception:
        logging.exception("Erreur inattendue pendant l'exécution.")
        raise


if __name__ == "__main__":
    main()
