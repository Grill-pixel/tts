[Français](README.md) | [English](README.en.md) | [العربية](README.ar.md)

# Groq TTS Application (Text-to-Speech)

> **Project goal**: provide a small Tkinter GUI that converts text to audio using the **Groq TTS API**.
>
> This README is **detailed and beginner‑friendly** so newcomers can follow every step.

---

## 📚 Table of Contents

- [✅ What the program does (simple explanation)](#-what-the-program-does-simple-explanation)
- [🧩 Prerequisites (what you need first)](#-prerequisites-what-you-need-first)
- [📁 Important project files](#-important-project-files)
- [🧪 Step-by-step installation (beginner level)](#-step-by-step-installation-beginner-level)
- [▶️ Run the program](#️-run-the-program)
- [🧭 Using the program (detailed walkthrough)](#-using-the-program-detailed-walkthrough)
- [🧠 How the program works (simple version)](#-how-the-program-works-simple-version)
- [🔧 Troubleshooting (common issues)](#-troubleshooting-common-issues)
- [📌 Usage tips](#-usage-tips)
- [📄 License](#-license)
- [✅ Ultra‑short summary](#-ultra-short-summary)

---

## ✅ What the program does (simple explanation)

The program:

1. **Checks** whether required Python libraries are installed.
2. **Asks** for a Groq API key (and stores it in `api_key.txt`).
3. **Fetches** the list of available Groq TTS models.
4. **Lets the user** pick a model, a voice, and a speed.
5. **Converts text to audio** and either:
   - **plays** the audio directly,
   - or **saves** it to a `.wav` file.

---

## 🧩 Prerequisites (what you need first)

### 1) A **Windows** computer
The program uses `winsound` and `os.startfile`, which are **Windows‑specific**.

### 2) Python installed
- Recommended version: **Python 3.10+**
- Check your version in a terminal:
  ```bash
  python --version
  ```

### 3) A Groq API key
Create a Groq account and get your personal API key.

---

## 📁 Important project files

- `tts.py`: main program.
- `README.md`: French guide.
- `README.en.md`: English guide.
- `README.ar.md`: Arabic guide.
- `api_key.txt`: created automatically to store your key (locally).
- `logd.txt`: log file (created automatically).

---

## 🧪 Step-by-step installation (beginner level)

### ✅ Step 1 — Open a terminal
On Windows:
- **Command Prompt** (`cmd`)
- or **PowerShell**

### ✅ Step 2 — Go to the project folder
Example:
```bash
cd C:\path\to\the\project
```

### ✅ Step 3 — (Optional but recommended) create a virtual environment
This avoids mixing dependencies across projects.

```bash
python -m venv .venv
```

Activate it:
```bash
.venv\Scripts\activate
```

You should see `(.venv)` at the start of your terminal line.

### ✅ Step 4 — Install dependencies
The program needs:
- `groq`
- `requests`

Install them with:
```bash
pip install groq requests
```

---

## ▶️ Run the program

From the project folder:

```bash
python tts.py
```

A GUI window opens.

---

## 🧭 Using the program (detailed walkthrough)

### 1) Library check
At startup, a window verifies that `groq` and `requests` are installed.

- If everything is OK: a green message appears ✅
- Otherwise: you will see `pip install ...` commands you can copy

Click **Re-check** after installing.

---

### 2) API key input
A second window asks for your **Groq API key**.

- It is **stored locally** in `api_key.txt`.
- You won’t have to retype it every time.

---

### 3) Choose model, voice, and speed
In the main window:

- **TTS model**: list of models available on your Groq account.
- **Voice**: available voices depend on the model.
- **Speed**: choose between **0.5x** (slow) and **3.0x** (very fast).

---

### 4) Write the text
In the large text box, enter what you want to hear.

Example:
```
Hello, this is a text-to-speech test.
```

---

### 5) Play or save
You have two buttons:

- **Play**: converts text to audio and plays it.
- **Save**: saves the audio to a `.wav` file.

---

## 🧠 How the program works (simple version)

### 1) The app requests Groq models
The Groq API returns a list of available models.

### 2) The app filters TTS models
It keeps those containing words like `tts`, `speech`, or `orpheus`.

### 3) When you click Play or Save
It sends an HTTP request to:

```
https://api.groq.com/openai/v1/audio/speech
```

Including:
- text
- model
- voice
- speed

Groq returns a **WAV** file, which the program plays or saves.

---

## 🔧 Troubleshooting (common issues)

### ❌ "Module not found"
If an error says `groq` or `requests` is missing:
```bash
pip install groq requests
```

### ❌ API key error
- Make sure the key is correct.
- You can delete `api_key.txt` to enter it again.

### ❌ No sound
- Check that your speakers are on.
- Make sure Windows can play `.wav` files.

---

## 📌 Usage tips

- Stay on **Windows** to avoid incompatibilities.
- Use short text when testing the first time.
- To change your API key:
  - Delete `api_key.txt`
  - Relaunch the program

---

## 📄 License

This project is released under the MIT license. See [LICENSE](LICENSE) for the full text.

---

## ✅ Ultra‑short summary

1. Install Python
2. Install `groq` and `requests`
3. Run `python tts.py`
4. Enter your Groq key
5. Type text → Play or Save

---

If you’re new to programming, follow this guide step by step and everything will work. 🎉
