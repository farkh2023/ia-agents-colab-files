# IA Agents — Colab Files

Ce dossier regroupe les artefacts locaux liés aux notebooks Google Colab du projet **IA Agents**.  
Les notebooks eux-mêmes sont hébergés sur Google Drive et exécutés dans l'environnement Colab.  
Ce répertoire sert de point d'ancrage local : cache de sorties, exports, et ressources de travail.

---

## Workflow recommandé

1. **Ouvrir le notebook** directement depuis [Google Colab](https://colab.research.google.com) via Google Drive.
2. **Configurer les secrets Colab** (menu *Secrets* dans la barre latérale gauche) :
   - `GOOGLE_API_KEY` → votre clé Gemini API
3. **Monter Google Drive** en exécutant la cellule d'initialisation du notebook (`drive.mount("/content/drive")`).
4. **Exécuter les cellules** dans l'ordre, en vérifiant la sortie de chaque étape.
5. **Sauvegarder les résultats** dans Google Drive ou les exporter localement si nécessaire.
6. **Télécharger le notebook** (`.ipynb`) dans ce dossier si vous souhaitez travailler hors ligne ou versionner le code.

---

## Structure recommandée

```
Colab_files/
├── README.md               # Ce fichier
├── CLAUDE.md               # Instructions pour Claude Code
├── notebooks/              # Notebooks .ipynb téléchargés depuis Colab
│   └── mon_agent.ipynb
├── outputs/                # Résultats exportés (JSON, CSV, texte...)
│   └── resultat_session_1.json
├── assets/                 # Images, fichiers de données utilisés par les notebooks
│   └── data.csv
└── cache/                  # Artefacts HTML sauvegardés depuis le navigateur (auto-généré)
    ├── outputframe*.html
    └── saved_resource*.html
```

> Les fichiers `outputframe*.html` et `saved_resource*.html` présents à la racine sont des captures  
> automatiques du navigateur. Ils peuvent être déplacés dans `cache/` pour garder la racine propre.

---

## Notebooks disponibles

Tout nouveau notebook doit être placé dans le dossier `notebooks/` afin de rester organisé, versionnable et exécutable localement.

| Notebook | Rôle | Statut |
|---|---|---|
| `notebooks/gemini_starter.ipynb` | Notebook de démarrage pour tester Gemini API avec `google-genai` : chargement de `GEMINI_API_KEY` depuis `.env` et génération de texte simple. | Actif |
| `notebooks/cretionimg.ipynb` | Notebook préexistant lié à la création ou expérimentation d'images. À auditer avant documentation complète. | À vérifier |
| `notebooks/rag_notes_demo.ipynb` | Démonstration RAG minimale : lecture de notes `.txt` depuis `assets/`, embeddings Gemini, recherche par similarité cosine, puis génération d'une réponse avec contexte. | Actif |

---

## Scripts disponibles

Tout nouveau script doit être placé dans `scripts/` et documenté ici.

| Script | Type | Rôle |
|---|---|---|
| `scripts/run_jupyter.ps1` | PowerShell | Lance Jupyter Notebook depuis la racine du projet, vérifie les pré-requis (`.env`, `notebooks/`, dépendances) avant démarrage. |
| `scripts/rag_notes_demo.py` | Python | Pipeline RAG exécutable sans Jupyter : charge les notes `.txt` depuis `assets/`, génère les embeddings Gemini, retrouve les passages pertinents et génère une réponse. Accepte `--question` et `--top-k`. |

---

## Préparer une exécution locale

Si vous souhaitez exécuter un notebook **sans Google Colab**, suivez ces étapes :

### 1. Installer les dépendances

```bash
pip install google-genai jupyter
```

### 2. Définir la clé API

```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY = "votre_clé_ici"

# macOS / Linux
export GEMINI_API_KEY="votre_clé_ici"
```

### 3. Adapter les imports Colab

Les modules `google.colab.*` n'existent pas en dehors de Colab. Remplacez :

```python
# Avant (Colab uniquement)
from google.colab import userdata, drive
os.environ["GEMINI_API_KEY"] = userdata.get("GOOGLE_API_KEY")
drive.mount("/content/drive")
```

par :

```python
# Après (exécution locale)
import os
# La clé est déjà dans l'environnement via $env:GEMINI_API_KEY
# Remplacez les chemins /content/drive/... par des chemins locaux
```

### 4. Lancer Jupyter

```bash
jupyter notebook notebooks/mon_agent.ipynb
```

---

## Lancement local rapide

### Installer les dépendances

```powershell
pip install -r requirements.txt
```

### Configurer l'environnement

```powershell
Copy-Item .env.example .env
# Ouvrez .env et renseignez votre GEMINI_API_KEY
```

### Lancer Jupyter

Via le script automatisé (vérifie les pré-requis avant de démarrer) :

```powershell
.\scripts\run_jupyter.ps1
```

Ou directement :

```powershell
jupyter notebook notebooks/
```

### Exécuter le script RAG local

```powershell
python scripts/rag_notes_demo.py --question "Quel est l'objectif de ce projet ?"
```

> **Note :** Le fichier `outputs/embeddings.json` est généré automatiquement lors de la première exécution du script RAG. Il est ignoré par Git (voir `.gitignore`) et n'a pas besoin d'être versionné.

---

## API Flask RAG

L'API expose le pipeline RAG local via HTTP.

### Lancer l'API

```powershell
python app.py
```

L'API démarre sur `http://localhost:5000`. Les notes de `assets/` sont indexées au démarrage (les embeddings sont mis en cache dans `outputs/embeddings.json`).

### GET /health

Vérifie que le service est opérationnel.

```powershell
curl http://localhost:5000/health
```

```json
{ "status": "ok", "service": "ia-agents-rag-api" }
```

### POST /query

Effectue une recherche RAG et retourne les sources (et optionnellement une réponse générée).

| Champ | Type | Défaut | Description |
|---|---|---|---|
| `question` | string | — | Question à poser (obligatoire) |
| `top_k` | int | `2` | Nombre de notes à retrouver |
| `retrieve_only` | bool | `true` | Si `true`, n'appelle pas `generate_content()` |

> **Par défaut `retrieve_only: true`** pour éviter les erreurs de quota Gemini.

**Exemple — recherche seule :**

```powershell
curl -X POST http://localhost:5000/query `
  -H "Content-Type: application/json" `
  -d '{"question": "Comment fonctionne RAG ?", "top_k": 2}'
```

```json
{
  "question": "Comment fonctionne RAG ?",
  "answer": null,
  "sources": [
    { "source": "example_note.txt", "score": 0.8741, "excerpt": "..." }
  ]
}
```

**Exemple — avec génération :**

```powershell
curl -X POST http://localhost:5000/query `
  -H "Content-Type: application/json" `
  -d '{"question": "Comment fonctionne RAG ?", "retrieve_only": false}'
```

```json
{
  "question": "Comment fonctionne RAG ?",
  "answer": "RAG améliore la précision en...",
  "sources": [
    { "source": "example_note.txt", "score": 0.8741, "excerpt": "..." }
  ]
}
```

---

## Prochaines améliorations

- [ ] **Versionner les notebooks** : exporter régulièrement les `.ipynb` depuis Colab et les commiter dans `notebooks/`.
- [ ] **Automatiser la récupération des clés** : utiliser un fichier `.env` local avec `python-dotenv` pour éviter de redéfinir les variables à chaque session.
- [ ] **Ajouter des tests unitaires** : extraire les fonctions métier des notebooks dans des modules Python (`.py`) testables indépendamment.
- [ ] **Structurer les sorties** : normaliser le format des résultats dans `outputs/` (JSON avec métadonnées : date, modèle, paramètres).
- [ ] **Documenter chaque notebook** : ajouter une cellule Markdown d'introduction en haut de chaque notebook (objectif, entrées attendues, sorties produites).
- [ ] **Migrer vers un pipeline reproductible** : envisager [Papermill](https://papermill.readthedocs.io) pour paramétrer et exécuter les notebooks en lot.
