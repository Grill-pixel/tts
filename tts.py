import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from pathlib import Path
import importlib.util
import requests
import sys
import threading
import winsound
import os

# ===================== LOG SYSTEM =====================
logging.basicConfig(
    filename="logd.txt",
    level=logging.DEBUG,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
)
logging.info("--- LOG SYSTEM INITIALIZED ---")

# ===================== CONSTANTS =====================
API_KEY_FILE = Path("api_key.txt")
REQUIRED_DEPENDENCIES = [
    ("groq", "groq"),
    ("requests", "requests"),
]

GROQ_API_BASE = "https://api.groq.com/openai/v1"

# ===================== UTIL FUNCTIONS =====================
def check_missing_dependencies():
    missing = []
    for pip_name, module_name in REQUIRED_DEPENDENCIES:
        if importlib.util.find_spec(module_name) is None:
            missing.append((pip_name, module_name))
    return missing

def save_api_key(key):
    API_KEY_FILE.write_text(key.strip(), encoding="utf-8")

def load_api_key():
    if API_KEY_FILE.exists():
        return API_KEY_FILE.read_text(encoding="utf-8").strip()
    return ""

def copy_to_clipboard(text, root):
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()

# ===================== DEPENDENCY WINDOW =====================
class DependencyManager(tk.Toplevel):
    def __init__(self, master, on_done):
        super().__init__(master)
        self.on_done = on_done
        self.title("Vérification des bibliothèques")
        self.geometry("700x380")
        self.resizable(False, False)

        self.configure(padx=16, pady=16)
        ttk.Label(self, text="Vérification des dépendances", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(self, text="Installe les bibliothèques manquantes, puis clique sur Re-vérifier.", foreground="#555").pack(anchor="w", pady=(4, 12))

        self.frame = ttk.Frame(self)
        self.frame.pack(fill="both", expand=True)

        self.progress = ttk.Label(self, text="")
        self.progress.pack(anchor="w", pady=(10, 0))

        btn_row = ttk.Frame(self)
        btn_row.pack(fill="x", pady=(12, 0))

        self.recheck_button = ttk.Button(btn_row, text="Re-vérifier", command=self._refresh)
        self.recheck_button.pack(side="left")

        self.next_button = ttk.Button(btn_row, text="Suivant", command=self._finish)
        self.next_button.pack(side="right")
        self.next_button.state(["disabled"])

        self._populate()

        self.after(50, self._center)
        self.after(50, self.lift)
        self.after(50, self.focus_force)

    def _populate(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

        missing = check_missing_dependencies()
        if not missing:
            ttk.Label(self.frame, text="Toutes les bibliothèques sont maintenant installées ✅", foreground="green").pack(anchor="w")
            self.progress.config(text="Tu peux continuer.")
            self.next_button.state(["!disabled"])
        else:
            self.progress.config(text="Bibliothèques manquantes :")
            for pip_name, module_name in missing:
                row = ttk.Frame(self.frame)
                row.pack(fill="x", pady=4)

                ttk.Label(row, text=pip_name, width=18).pack(side="left")

                cmd = f"pip install {pip_name}"
                cmd_entry = ttk.Entry(row, width=42)
                cmd_entry.insert(0, cmd)
                cmd_entry.configure(state="readonly")
                cmd_entry.pack(side="left", padx=6)

                copy_btn = ttk.Button(row, text="Copier", command=lambda c=cmd: self._copy(c))
                copy_btn.pack(side="left")

            self.next_button.state(["disabled"])

    def _refresh(self):
        self.progress.config(text="Re-vérification en cours...")
        self.after(100, self._populate)

    def _copy(self, text):
        copy_to_clipboard(text, self)
        messagebox.showinfo("Copié", f"Commande copiée :\n{text}")

    def _finish(self):
        self.destroy()
        if self.on_done:
            self.on_done()

    def _center(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

# ===================== API KEY WINDOW =====================
class ApiKeyWindow(tk.Toplevel):
    def __init__(self, master, existing_key, on_done):
        super().__init__(master)
        self.api_key = None
        self.on_done = on_done

        self.title("Clé API Groq")
        self.geometry("420x220")
        self.resizable(False, False)

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

        self.after(50, self._center)
        self.after(50, self.lift)
        self.after(50, self.focus_force)

    def _submit(self):
        key = self.entry.get().strip()
        if not key:
            messagebox.showerror("Erreur", "La clé API ne peut pas être vide.")
            return
        save_api_key(key)
        self.api_key = key
        self.destroy()
        if self.on_done:
            self.on_done(key)

    def _cancel(self):
        self.destroy()
        if self.on_done:
            self.on_done(None)

    def _center(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

# ===================== MAIN APP =====================
class TTSApp:
    def __init__(self, root):
        self.root = root
        self.api_key = None

        self.models = []
        self.voices_by_model = {}
        self.selected_model = tk.StringVar()
        self.selected_voice = tk.StringVar()
        self.selected_speed = tk.DoubleVar(value=1.0)

        self.root.title("TTS Groq")
        self.root.geometry("720x520")

        self._build_main_ui()
        self.root.after(50, self._start_dependency_check)

    # ---------------- UI ----------------
    def _build_main_ui(self):
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill="both", expand=True)

        ttk.Label(self.main_frame, text="Application Text-to-Speech Groq", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(self.main_frame, text="Choisis un modèle, une voix, puis génère l'audio.", foreground="#555").pack(anchor="w", pady=(4, 12))

        form = ttk.Frame(self.main_frame)
        form.pack(fill="x", pady=(0, 12))

        # Modèle
        ttk.Label(form, text="Modèle TTS :", width=16).grid(row=0, column=0, sticky="w", pady=4)
        self.model_combo = ttk.Combobox(form, textvariable=self.selected_model, state="readonly", width=48)
        self.model_combo.grid(row=0, column=1, sticky="w", pady=4)
        self.model_combo.bind("<<ComboboxSelected>>", self._on_model_change)

        # Voix
        ttk.Label(form, text="Voix :", width=16).grid(row=1, column=0, sticky="w", pady=4)
        self.voice_combo = ttk.Combobox(form, textvariable=self.selected_voice, state="readonly", width=48)
        self.voice_combo.grid(row=1, column=1, sticky="w", pady=4)

        # Vitesse
        ttk.Label(form, text="Vitesse :", width=16).grid(row=2, column=0, sticky="w", pady=4)
        speed_frame = ttk.Frame(form)
        speed_frame.grid(row=2, column=1, sticky="w", pady=4)
        ttk.Scale(speed_frame, from_=0.5, to=3.0, variable=self.selected_speed, orient="horizontal", length=200).pack(side="left")
        ttk.Label(speed_frame, textvariable=self.selected_speed, width=5).pack(side="left", padx=(8, 0))

        # Texte
        ttk.Label(self.main_frame, text="Texte à lire :", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.text_box = tk.Text(self.main_frame, height=8, wrap="word")
        self.text_box.pack(fill="both", expand=True, pady=(4, 12))

        # Boutons
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(anchor="e")

        self.play_button = ttk.Button(btn_frame, text="Lire", command=self._play_audio, state="disabled")
        self.play_button.pack(side="left", padx=6)

        self.save_button = ttk.Button(btn_frame, text="Sauvegarder", command=self._save_audio, state="disabled")
        self.save_button.pack(side="left")

    # ---------------- Flow ----------------
    def _start_dependency_check(self):
        logging.info("Ouverture de la fenêtre de vérification des dépendances.")
        DependencyManager(self.root, on_done=self._after_dependencies)

    def _after_dependencies(self):
        if check_missing_dependencies():
            messagebox.showerror(
                "Bibliothèques manquantes",
                "Certaines bibliothèques sont encore manquantes.\nInstalle-les puis clique sur Re-vérifier.",
            )
            self._start_dependency_check()
            return

        logging.info("Ouverture de la fenêtre de clé API.")
        ApiKeyWindow(self.root, load_api_key(), on_done=self._after_api_key)

    def _after_api_key(self, key):
        if not key:
            messagebox.showwarning("Clé manquante", "Aucune clé API fournie. Fermeture du programme.")
            self.root.destroy()
            return

        self.api_key = key

        # Charger les modèles TTS
        try:
            self._fetch_models()
        except Exception as e:
            messagebox.showerror("Erreur API", f"Impossible de récupérer les modèles :\n{e}")
            self.root.destroy()
            return

        if not self.models:
            messagebox.showerror("Aucun modèle", "Aucun modèle TTS disponible avec cette clé API.")
            self.root.destroy()
            return

        self.model_combo["values"] = self.models
        self.selected_model.set(self.models[0])
        self._on_model_change()

        self.play_button.state(["!disabled"])
        self.save_button.state(["!disabled"])

        messagebox.showinfo("Prêt", "Application prête à l'emploi 🎉")

    # ---------------- API ----------------
    def _fetch_models(self):
        url = f"{GROQ_API_BASE}/models"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()

        # Filtrer uniquement les modèles TTS
        self.models = [
            m["id"] for m in data.get("data", [])
            if "tts" in m["id"].lower() or "speech" in m["id"].lower() or "orpheus" in m["id"].lower()
        ]

        # Définition des voix connues par modèle (API Groq ne fournit pas encore un endpoint "list voices")
        self.voices_by_model = {}
        for model in self.models:
            lname = model.lower()
            if "english" in lname or "orpheus" in lname:
                self.voices_by_model[model] = ["autumn", "diana", "hannah", "austin"]
            elif "arabic" in lname:
                self.voices_by_model[model] = ["arabic1", "arabic2", "arabic3", "arabic4"]
            else:
                self.voices_by_model[model] = ["default"]

    def _on_model_change(self, event=None):
        model = self.selected_model.get()
        voices = self.voices_by_model.get(model, ["default"])
        self.voice_combo["values"] = voices
        self.selected_voice.set(voices[0])

    def _generate_audio(self, text, model, voice, speed):
        url = f"{GROQ_API_BASE}/audio/speech"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": "wav",
            "speed": speed,
        }

        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        return r.content

    # ---------------- Actions ----------------
    def _play_audio(self):
        text = self.text_box.get("1.0", "end").strip()
        if not text:
            messagebox.showerror("Erreur", "Veuillez entrer du texte.")
            return

        model = self.selected_model.get()
        voice = self.selected_voice.get()
        speed = float(self.selected_speed.get())

        self._disable_buttons()

        def worker():
            try:
                audio_data = self._generate_audio(text, model, voice, speed)
                temp_file = Path("temp_tts.wav")
                temp_file.write_bytes(audio_data)
                os.startfile(str(temp_file))
            except Exception as e:
                messagebox.showerror("Erreur TTS", str(e))
            finally:
                self._enable_buttons()

        threading.Thread(target=worker, daemon=True).start()

    def _save_audio(self):
        text = self.text_box.get("1.0", "end").strip()
        if not text:
            messagebox.showerror("Erreur", "Veuillez entrer du texte.")
            return

        path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV audio", "*.wav")])
        if not path:
            return

        model = self.selected_model.get()
        voice = self.selected_voice.get()
        speed = float(self.selected_speed.get())

        self._disable_buttons()

        def worker():
            try:
                audio_data = self._generate_audio(text, model, voice, speed)
                Path(path).write_bytes(audio_data)
                messagebox.showinfo("Succès", f"Audio sauvegardé :\n{path}")
            except Exception as e:
                messagebox.showerror("Erreur TTS", str(e))
            finally:
                self._enable_buttons()

        threading.Thread(target=worker, daemon=True).start()

    def _disable_buttons(self):
        self.play_button.state(["disabled"])
        self.save_button.state(["disabled"])

    def _enable_buttons(self):
        self.play_button.state(["!disabled"])
        self.save_button.state(["!disabled"])

# ===================== ENTRY POINT =====================
def main():
    root = tk.Tk()
    app = TTSApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
