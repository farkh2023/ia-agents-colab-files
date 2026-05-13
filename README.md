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

## Prochaines améliorations

- [ ] **Versionner les notebooks** : exporter régulièrement les `.ipynb` depuis Colab et les commiter dans `notebooks/`.
- [ ] **Automatiser la récupération des clés** : utiliser un fichier `.env` local avec `python-dotenv` pour éviter de redéfinir les variables à chaque session.
- [ ] **Ajouter des tests unitaires** : extraire les fonctions métier des notebooks dans des modules Python (`.py`) testables indépendamment.
- [ ] **Structurer les sorties** : normaliser le format des résultats dans `outputs/` (JSON avec métadonnées : date, modèle, paramètres).
- [ ] **Documenter chaque notebook** : ajouter une cellule Markdown d'introduction en haut de chaque notebook (objectif, entrées attendues, sorties produites).
- [ ] **Migrer vers un pipeline reproductible** : envisager [Papermill](https://papermill.readthedocs.io) pour paramétrer et exécuter les notebooks en lot.
