# ROADMAP — IA Agents / Colab Files

Feuille de route du projet, organisée par phases progressives.  
Les phases marquées ✅ sont déjà réalisées.

---

## Phase 1 — Initialisation ✅

- Créer la structure du projet (`notebooks/`, `outputs/`, `assets/`, `cache/`, `scripts/`)
- Configurer `.gitignore`, `requirements.txt`, `.env.example`
- Rédiger `README.md` avec workflow, structure et guide de lancement local
- Créer `scripts/run_jupyter.ps1` pour le lancement automatisé

---

## Phase 2 — Notebooks de base ✅

- Créer `notebooks/gemini_starter.ipynb` (test Gemini API, chargement `.env`)
- Créer `notebooks/rag_notes_demo.ipynb` (pipeline RAG minimale)
- Ajouter `assets/example_note.txt` comme donnée de démonstration

---

## Phase 3 — Données et assets

- Auditer et documenter `notebooks/cretionimg.ipynb`
- Ajouter des notes réelles dans `assets/` (`.txt`, `.md`)
- Normaliser les sorties dans `outputs/` (JSON avec horodatage et métadonnées)
- Documenter les formats de données supportés

---

## Phase 4 — RAG amélioré

- Persister les embeddings dans `outputs/` (JSON ou NumPy `.npy`)
- Ajouter une recherche sémantique persistante (rechargement sans recalcul)
- Découper les notes longues en chunks avant indexation
- Étendre le support aux fichiers `.md` et `.pdf`

---

## Phase 5 — Interface web

- Créer une interface Flask ou FastAPI
- Ajouter une page de recherche RAG
- Ajouter upload de fichiers
- Afficher les sources utilisées

---

## Phase 6 — Automatisation

- Ajouter scripts de lancement
- Ajouter tests simples
- Ajouter export Markdown/JSON
- Préparer une future CI GitHub Actions

---

## Priorités immédiates

1. Auditer `cretionimg.ipynb`
2. Transformer `rag_notes_demo.ipynb` en script Python
3. Ajouter une structure `docs/`
4. Documenter les commandes utiles
