# Application TTS Groq (Text-to-Speech)

> **Objectif du projet** : fournir une petite application graphique (Tkinter) qui transforme un texte en audio grâce à l’API **Groq TTS**.
>
> Ce README est volontairement **très détaillé et pédagogique** pour qu’un(e) débutant(e) comprenne chaque étape.

---

## ✅ Ce que fait le programme (explication simple)

Le programme :

1. **Vérifie** si les bibliothèques Python nécessaires sont installées.
2. **Demande** une clé API Groq (et l’enregistre dans un fichier `api_key.txt`).
3. **Récupère** la liste des modèles TTS disponibles sur Groq.
4. **Laisse l’utilisateur** choisir un modèle, une voix et une vitesse.
5. **Convertit le texte en audio** et :
   - soit **lit directement** l’audio,
   - soit **enregistre** l’audio dans un fichier `.wav`.

---

## 🧩 Prérequis (ce qu’il faut avant de commencer)

### 1) Un ordinateur sous **Windows**
Le programme utilise `winsound` et `os.startfile`, qui sont des fonctions **spécifiques à Windows**.

### 2) Python installé
- Version recommandée : **Python 3.10+**
- Vérifier la version dans un terminal :
  ```bash
  python --version
  ```

### 3) Une clé API Groq
Tu dois créer un compte Groq et récupérer une clé API personnelle.

---

## 📁 Fichiers importants du projet

- `tts.py` : le programme principal.
- `README.md` : ce guide.
- `api_key.txt` : créé automatiquement pour stocker ta clé (localement).
- `logd.txt` : fichier de logs (créé automatiquement).

---

## 🧪 Installation pas à pas (niveau débutant)

### ✅ Étape 1 — Ouvrir un terminal
Sur Windows :
- **Invite de commandes** (`cmd`)
- ou **PowerShell**

### ✅ Étape 2 — Aller dans le dossier du projet
Exemple :
```bash
cd C:\chemin\vers\le\projet
```

### ✅ Étape 3 — (Optionnel mais recommandé) créer un environnement virtuel
Cela évite de mélanger les bibliothèques entre projets.

```bash
python -m venv .venv
```

Activer l’environnement :
```bash
.venv\Scripts\activate
```

Tu dois voir `(.venv)` au début de la ligne du terminal.

### ✅ Étape 4 — Installer les dépendances
Le programme a besoin de :
- `groq`
- `requests`

Installe-les avec :
```bash
pip install groq requests
```

---

## ▶️ Lancer le programme

Toujours dans le dossier du projet :

```bash
python tts.py
```

Une fenêtre graphique s’ouvre.

---

## 🧭 Utilisation du programme (explication détaillée)

### 1) Vérification des bibliothèques
Au démarrage, une fenêtre s’ouvre et vérifie que `groq` et `requests` sont bien installés.

- Si tout est bon : un message vert s’affiche ✅
- Sinon : tu verras des commandes `pip install ...` que tu peux copier

Clique sur **Re‑vérifier** après installation.

---

### 2) Saisie de la clé API
Une deuxième fenêtre te demande ta **clé API Groq**.

- Elle est **enregistrée localement** dans un fichier `api_key.txt`.
- Tu n’auras pas besoin de la retaper à chaque fois.

---

### 3) Choix du modèle, de la voix et de la vitesse
Dans la fenêtre principale :

- **Modèle TTS** : liste des modèles disponibles sur ton compte Groq.
- **Voix** : certaines voix sont proposées selon le modèle.
- **Vitesse** : tu peux choisir entre **0.5x** (lent) et **3.0x** (très rapide).

---

### 4) Écrire le texte
Dans la grande zone de texte, écris ce que tu veux entendre.

Exemple :
```
Bonjour, ceci est un test de synthèse vocale.
```

---

### 5) Lire ou sauvegarder
Tu as deux boutons :

- **Lire** : le texte est transformé en audio et lu directement.
- **Sauvegarder** : l’audio est enregistré dans un fichier `.wav`.

---

## 🧠 Comment fonctionne le programme (version simple)

### 1) L’application demande les modèles Groq
L’API Groq renvoie une liste de modèles disponibles.

### 2) L’application filtre les modèles TTS
Elle garde ceux qui contiennent des mots comme `tts`, `speech` ou `orpheus`.

### 3) Quand tu cliques sur Lire ou Sauvegarder
Elle envoie une requête HTTP à :

```
https://api.groq.com/openai/v1/audio/speech
```

Avec :
- le texte
- le modèle
- la voix
- la vitesse

Groq renvoie un fichier audio **WAV**, que le programme lit ou sauvegarde.

---

## 🔧 Dépannage (problèmes fréquents)

### ❌ "Module introuvable"
Si une erreur dit que `groq` ou `requests` manque :
```bash
pip install groq requests
```

### ❌ Erreur de clé API
- Vérifie que la clé est correcte.
- Tu peux supprimer `api_key.txt` pour la saisir à nouveau.

### ❌ Pas de son
- Vérifie que tes haut‑parleurs sont actifs.
- Assure-toi que Windows sait lire les fichiers `.wav`.

---

## 📌 Conseils d’utilisation

- Reste sous **Windows** pour éviter les incompatibilités.
- Utilise un texte court pour tester la première fois.
- Si tu veux changer de clé API :
  - Supprime `api_key.txt`
  - Relance le programme

---

## 📄 Licence

Ce projet est libre d’utilisation pour apprendre et expérimenter.

---

## ✅ Résumé ultra-court

1. Installer Python
2. Installer `groq` et `requests`
3. Lancer `python tts.py`
4. Entrer la clé Groq
5. Écrire un texte → Lire ou sauvegarder

---

Si tu débutes en programmation, tu peux relire ce guide étape par étape et tout fonctionnera. 🎉
