import io
import sys
import logging
from pathlib import Path
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk, filedialog

# Vérification des modules requis
try:
    import groq
except ImportError:
    print("Module manquant: groq. Installez-le avec 'pip install groq'")
    sys.exit(1)

try:
    from pydub import AudioSegment
    from pydub.playback import play
except ImportError:
    print("Module manquant: pydub. Installez-le avec 'pip install pydub'")
    sys.exit(1)

# ---------------- Logging ----------------
log_file = Path("logs.txt")
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logging.info("--- LOG SYSTEM INITIALIZED ---")

# ----------------- API Key -----------------
API_KEY_FILE = Path("api_key.txt")

def get_api_key():
    if API_KEY_FILE.exists():
        return API_KEY_FILE.read_text().strip()
    return None

def save_api_key(key):
    API_KEY_FILE.write_text(key)
    logging.info("Clé API sauvegardée.")

# ----------------- TTS App -----------------
class TTSApp:
    def __init__(self, master, api_key):
        self.master = master
        self.master.title("TTS Orpheus")
        self.api_key = api_key
        self.client = groq.Client(api_key=self.api_key)

        self.selected_model = tk.StringVar()
        self.selected_voice = tk.StringVar()

        self.models = []
        self.voices = []

        self.build_ui()
        self.fetch_models()

    def build_ui(self):
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
        self.text_entry = tk.Text(frame, height=5, width=40)
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
        self.voices = ["autumn", "spring", "summer", "winter"]
        self.voice_combo["values"] = self.voices
        self.selected_voice.set(self.voices[0])

    def _notify(self, title, message, level="info"):
        def _show():
            if level == "error":
                messagebox.showerror(title, message)
            elif level == "warning":
                messagebox.showwarning(title, message)
            else:
                messagebox.showinfo(title, message)
        self.master.after(0, _show)

    def generate_speech_bytes(self, text, model, voice):
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
        text = self.text_entry.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Attention", "Veuillez saisir un texte.")
            return
        model = self.selected_model.get()
        voice = self.selected_voice.get()

        def worker():
            audio_bytes = self.generate_speech_bytes(text, model, voice)
            if audio_bytes:
                audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
                play(audio)
            else:
                self._notify("Erreur", "Génération TTS échouée.", level="error")
        threading.Thread(target=worker, daemon=True).start()

    def save_text(self):
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
    # Création de la fenêtre Tk principale pour saisir clé API
    root = tk.Tk()
    root.withdraw()  # Cacher la fenêtre principale
    api_key = get_api_key()
    api_key = simpledialog.askstring("Clé API", "Entrez votre clé API Groq:", initialvalue=api_key)
    if not api_key:
        messagebox.showerror("Erreur", "Clé API vide")
        sys.exit(1)
    save_api_key(api_key)
    root.destroy()

    # Lancer la fenêtre principale du TTS
    main_root = tk.Tk()
    app = TTSApp(main_root, api_key)
    main_root.mainloop()


if __name__ == "__main__":
    main()
