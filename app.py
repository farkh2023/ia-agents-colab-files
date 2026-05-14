"""
app.py — API Flask minimale pour le RAG Gemini.

Usage :
    python app.py

Endpoints :
    GET  /health
    POST /query   {"question": "...", "top_k": 2, "retrieve_only": true}
"""

import os
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from google import genai

# ── Import des fonctions RAG depuis scripts/ ──────────────────────────────────

sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))

from rag_notes_demo import (  # noqa: E402
    CACHE_FILE,
    DEFAULT_GENERATION_MODEL,
    content_hash,
    embed_text,
    find_project_root,
    load_embedding_cache,
    load_env,
    load_text_notes,
    retrieve,
    save_embedding_cache,
)

# Défaut local aligné avec .env.example — remplace le défaut du script (text-embedding-004)
_DEFAULT_EMBED_MODEL = "gemini-embedding-001"

# ── Initialisation au démarrage ───────────────────────────────────────────────


def _init() -> tuple:
    """
    Charge l'environnement, indexe les notes (avec cache) et retourne
    le client Gemini, les notes enrichies et les modèles choisis.
    """
    project_root = find_project_root(Path(__file__).resolve().parent)
    api_key = load_env(project_root)

    embed_model = (
        os.environ.get("GEMINI_EMBEDDING_MODEL", "").strip() or _DEFAULT_EMBED_MODEL
    )
    gen_model = (
        os.environ.get("GEMINI_GENERATION_MODEL", "").strip() or DEFAULT_GENERATION_MODEL
    )

    print(f"Modèle d'embedding  : {embed_model}")
    print(f"Modèle de génération : {gen_model}")

    client = genai.Client(api_key=api_key)

    print("=== Chargement des notes ===")
    notes = load_text_notes(project_root / "assets")

    outputs_dir = project_root / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    cache_path = outputs_dir / CACHE_FILE

    print("=== Indexation des embeddings ===")
    cache = load_embedding_cache(cache_path)
    cache_updated = False
    for note in notes:
        h = content_hash(note["content"])
        cached = cache.get(note["source"], {})
        if cached.get("hash") == h:
            note["embedding"] = cached["embedding"]
            print(f"  [CACHE] {note['source']}")
        else:
            note["embedding"] = embed_text(client, note["content"], model=embed_model)
            cache[note["source"]] = {"hash": h, "embedding": note["embedding"]}
            cache_updated = True
            print(f"  [NEW]   {note['source']}  — dim : {len(note['embedding'])}")

    if cache_updated:
        save_embedding_cache(cache_path, cache)
        print(f"  → Cache sauvegardé : outputs/{CACHE_FILE}")

    return client, notes, embed_model, gen_model, project_root


try:
    _client, _notes, _embed_model, _gen_model, _project_root = _init()
    print(f"\n[OK] API prête — {len(_notes)} note(s) indexée(s).")
    print(f"     Embedding : {_embed_model}  |  Génération : {_gen_model}\n")
except (EnvironmentError, FileNotFoundError, RuntimeError) as _exc:
    print(f"\n[ERREUR] Initialisation impossible : {_exc}", file=sys.stderr)
    sys.exit(1)

# ── Application Flask ─────────────────────────────────────────────────────────

app = Flask(__name__)


# ── GET / ────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# ── GET /health ───────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "ia-agents-rag-api"})


# ── POST /query ───────────────────────────────────────────────────────────────

@app.route("/query", methods=["POST"])
def query():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Corps JSON manquant ou Content-Type incorrect."}), 400

    # Validation des champs
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Le champ 'question' est requis et ne peut pas être vide."}), 400

    top_k = data.get("top_k", 2)
    if not isinstance(top_k, int) or top_k < 1:
        return jsonify({"error": "'top_k' doit être un entier >= 1."}), 400

    retrieve_only = data.get("retrieve_only", True)
    if not isinstance(retrieve_only, bool):
        return jsonify({"error": "'retrieve_only' doit être un booléen (true ou false)."}), 400

    try:
        # Recherche sémantique
        retrieved = retrieve(
            _client, question, _notes, top_k=top_k, embed_model=_embed_model
        )
        sources = [
            {
                "source": r["source"],
                "score": round(r["score"], 4),
                "excerpt": r["content"][:200],
            }
            for r in retrieved
        ]

        # Mode retrieve_only : pas d'appel à generate_content
        if retrieve_only:
            return jsonify({"question": question, "answer": None, "sources": sources})

        # Génération de la réponse à partir du contexte retrouvé
        context = "\n\n".join(
            f"[Source : {r['source']}]\n{r['content']}" for r in retrieved
        )
        prompt = (
            "Tu es un assistant qui répond uniquement à partir du contexte fourni.\n"
            "Si la réponse n'est pas dans le contexte, dis-le explicitement.\n\n"
            f"Contexte :\n{context}\n\n"
            f"Question : {question}\n\n"
            "Réponds de façon concise et précise."
        )

        response = _client.models.generate_content(
            model=_gen_model,
            contents=prompt,
        )
        return jsonify({
            "question": question,
            "answer": response.text,
            "sources": sources,
        })

    except Exception as exc:
        error_str = str(exc)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            return jsonify({
                "error": f"Quota Gemini dépassé pour le modèle '{_gen_model}'.",
                "hint": (
                    "Attendez la réinitialisation du quota, "
                    "ou relancez avec retrieve_only: true."
                ),
            }), 503
        return jsonify({"error": f"Erreur interne : {error_str}"}), 500


# ── Lancement ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
