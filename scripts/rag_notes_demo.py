"""
rag_notes_demo.py — Pipeline RAG minimale avec Gemini.

Usage :
    python scripts/rag_notes_demo.py
    python scripts/rag_notes_demo.py --question "Votre question ici"
    python scripts/rag_notes_demo.py --top-k 3 --question "Votre question"
    python scripts/rag_notes_demo.py --rebuild-index
    python scripts/rag_notes_demo.py --embedding-model gemini-embedding-exp-03-07
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from google import genai

# ── Constantes ────────────────────────────────────────────────────────────────

DEFAULT_EMBEDDING_MODEL  = "text-embedding-004"
DEFAULT_GENERATION_MODEL = "gemini-2.0-flash"
DEFAULT_QUESTION = "Comment utiliser Gemini pour générer du texte en Python ?"
CACHE_FILE       = "embeddings.json"
EXAMPLE_NOTE     = (
    "Gemini est un modèle de langage multimodal développé par Google DeepMind.\n"
    "Il est accessible via l'API Gemini et le SDK officiel python google-genai.\n"
    "Le modèle gemini-2.0-flash est optimisé pour la rapidité et les tâches courantes.\n"
    "Le modèle gemini-2.5-pro offre des capacités avancées de raisonnement complexe.\n"
    "Pour générer du texte, on utilise client.models.generate_content().\n"
    "Les embeddings transforment du texte en vecteurs numériques de haute dimension.\n"
    "Le modèle text-embedding-004 produit des vecteurs de dimension 768.\n"
    "La technique RAG améliore la précision en fournissant un contexte externe retrouvé\n"
    "par recherche sémantique.\n"
    "La similarité cosine mesure l'angle entre deux vecteurs : 1 = identiques, 0 = orthogonaux."
)

# ── Fonctions utilitaires ─────────────────────────────────────────────────────


def content_hash(text: str) -> str:
    """Retourne le SHA-256 du contenu texte (détection de modification)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_embedding_cache(cache_path: Path) -> dict:
    """Charge outputs/embeddings.json. Retourne {} si absent ou corrompu."""
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        print(f"[WARN] Cache illisible, reconstruction complète : {cache_path.name}")
        return {}


def save_embedding_cache(cache_path: Path, cache: dict) -> None:
    """Sauvegarde le cache d'embeddings dans outputs/embeddings.json."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def find_project_root(start: Path) -> Path:
    """Remonte l'arborescence depuis `start` jusqu'à trouver requirements.txt."""
    for candidate in [start, *start.parents]:
        if (candidate / "requirements.txt").exists():
            return candidate
    raise FileNotFoundError(
        "Racine du projet introuvable. "
        "Assurez-vous que requirements.txt existe à la racine."
    )


def load_env(project_root: Path) -> str:
    """Charge .env et retourne GEMINI_API_KEY. Lève une erreur si absente."""
    env_path = project_root / ".env"
    load_dotenv(dotenv_path=env_path)
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY introuvable.\n"
            f"  → Copiez {project_root / '.env.example'} vers {env_path}\n"
            "  → Puis renseignez votre clé Gemini."
        )
    return api_key


def load_text_notes(assets_dir: Path) -> list[dict]:
    """
    Lit tous les .txt de `assets_dir`.
    Crée assets/example_note.txt si le dossier ne contient aucun .txt.
    Retourne une liste de dicts {source, content}.
    """
    txt_files = sorted(assets_dir.glob("*.txt"))

    if not txt_files:
        example_path = assets_dir / "example_note.txt"
        example_path.write_text(EXAMPLE_NOTE, encoding="utf-8")
        txt_files = [example_path]
        print(f"[INFO] Aucun .txt trouvé — exemple créé : {example_path.name}")

    notes = []
    for path in txt_files:
        content = path.read_text(encoding="utf-8").strip()
        notes.append({"source": path.name, "content": content})
        print(f"  [OK] {path.name}  ({len(content)} caractères)")

    print(f"\n{len(notes)} note(s) chargée(s).\n")
    return notes


# ── Fonctions Gemini ──────────────────────────────────────────────────────────


def embed_text(client: genai.Client, text: str, model: str) -> list[float]:
    """Retourne le vecteur d'embedding d'un texte via Gemini."""
    try:
        response = client.models.embed_content(
            model=model,
            contents=text,
        )
        return response.embeddings[0].values
    except Exception as exc:
        raise RuntimeError(
            f"Échec de l'embedding avec le modèle '{model}'.\n"
            "  → Vérifiez que le modèle est disponible pour votre version d'API.\n"
            "  → Modèles valides : text-embedding-004, gemini-embedding-exp-03-07\n"
            "  → Modifiable via GEMINI_EMBEDDING_MODEL dans .env ou --embedding-model\n"
            f"  Erreur originale : {exc}"
        ) from exc


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Similarité cosine entre deux vecteurs. Retourne 0.0 si l'un est nul."""
    a = np.array(vec_a, dtype=float)
    b = np.array(vec_b, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def retrieve(
    client: genai.Client,
    question: str,
    notes: list[dict],
    top_k: int = 2,
    embed_model: str = DEFAULT_EMBEDDING_MODEL,
) -> list[dict]:
    """
    Calcule l'embedding de la question, puis retourne les `top_k` notes
    les plus proches par similarité cosine décroissante.
    """
    q_embedding = embed_text(client, question, model=embed_model)

    scored = [
        {
            "source":  note["source"],
            "content": note["content"],
            "score":   cosine_similarity(q_embedding, note["embedding"]),
        }
        for note in notes
    ]
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def answer(
    client: genai.Client,
    question: str,
    notes: list[dict],
    top_k: int = 2,
    embed_model: str = DEFAULT_EMBEDDING_MODEL,
    gen_model: str = DEFAULT_GENERATION_MODEL,
    retrieve_only: bool = False,
) -> str:
    """
    Retrouve le contexte pertinent via `retrieve()`, affiche les sources,
    puis génère une réponse avec Gemini (sauf si retrieve_only=True).
    Retourne le texte de la réponse, ou "" en mode retrieve_only.
    """
    retrieved = retrieve(client, question, notes, top_k=top_k, embed_model=embed_model)

    print(f"Question : {question}\n")
    print("=== Sources retrouvées ===")
    for i, r in enumerate(retrieved, 1):
        print(f"  [{i}] {r['source']}  (score : {r['score']:.4f})")
        print(f"       {r['content'][:120]}...")

    if retrieve_only:
        return ""

    context = "\n\n".join(
        f"[Source : {r['source']}]\n{r['content']}"
        for r in retrieved
    )

    prompt = (
        "Tu es un assistant qui répond uniquement à partir du contexte fourni.\n"
        "Si la réponse n'est pas dans le contexte, dis-le explicitement.\n\n"
        f"Contexte :\n{context}\n\n"
        f"Question : {question}\n\n"
        "Réponds de façon concise et précise."
    )

    try:
        response = client.models.generate_content(
            model=gen_model,
            contents=prompt,
        )
    except Exception as exc:
        error_str = str(exc)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            raise RuntimeError(
                f"Quota Gemini dépassé pour le modèle de génération '{gen_model}'.\n"
                "  → Attendez la réinitialisation du quota (généralement 1 minute).\n"
                f"  → Changez de modèle avec --generation-model gemini-1.5-flash\n"
                "  → Utilisez --retrieve-only pour ignorer la génération."
            ) from exc
        raise RuntimeError(
            f"Échec de la génération avec le modèle '{gen_model}' : {exc}"
        ) from exc

    print("\n=== Réponse Gemini ===")
    print(response.text)

    return response.text


# ── Point d'entrée ────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pipeline RAG minimale avec Gemini.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemples :\n"
            "  python scripts/rag_notes_demo.py\n"
            '  python scripts/rag_notes_demo.py --question "Qu\'est-ce que RAG ?"\n'
            "  python scripts/rag_notes_demo.py --top-k 3 --question \"Votre question\"\n"
            "  python scripts/rag_notes_demo.py --rebuild-index\n"
            "  python scripts/rag_notes_demo.py --retrieve-only\n"
            "  python scripts/rag_notes_demo.py --embedding-model gemini-embedding-exp-03-07\n"
            "  python scripts/rag_notes_demo.py --generation-model gemini-1.5-flash"
        ),
    )
    parser.add_argument(
        "--question", "-q",
        default=DEFAULT_QUESTION,
        help=f'Question à poser (défaut : "{DEFAULT_QUESTION}")',
    )
    parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=2,
        metavar="N",
        help="Nombre de notes à retrouver (défaut : 2)",
    )
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Forcer la régénération de tous les embeddings (ignore le cache).",
    )
    parser.add_argument(
        "--embedding-model",
        default=None,
        metavar="MODEL",
        help=(
            f"Modèle d'embedding Gemini (défaut : {DEFAULT_EMBEDDING_MODEL}). "
            "Surcharge GEMINI_EMBEDDING_MODEL dans .env."
        ),
    )
    parser.add_argument(
        "--generation-model",
        default=None,
        metavar="MODEL",
        help=(
            f"Modèle de génération Gemini (défaut : {DEFAULT_GENERATION_MODEL}). "
            "Surcharge GEMINI_GENERATION_MODEL dans .env."
        ),
    )
    parser.add_argument(
        "--retrieve-only",
        action="store_true",
        help="Afficher uniquement les sources retrouvées, sans appeler generate_content().",
    )
    args = parser.parse_args()

    # 1. Racine du projet
    project_root = find_project_root(Path(__file__).resolve().parent)
    print(f"Racine du projet : {project_root}\n")

    # 2. Clé API + modèle d'embedding
    api_key = load_env(project_root)
    print("Clé API chargée.")

    # Priorité : CLI > .env > défaut
    embed_model = (
        args.embedding_model
        or os.environ.get("GEMINI_EMBEDDING_MODEL", "").strip()
        or DEFAULT_EMBEDDING_MODEL
    )
    gen_model = (
        args.generation_model
        or os.environ.get("GEMINI_GENERATION_MODEL", "").strip()
        or DEFAULT_GENERATION_MODEL
    )
    print(f"Modèle d'embedding  : {embed_model}")
    if args.retrieve_only:
        print("Modèle de génération : (désactivé — mode --retrieve-only)")
    else:
        print(f"Modèle de génération : {gen_model}")
    print()

    # 3. Chargement des notes
    print("=== Chargement des notes ===")
    notes = load_text_notes(project_root / "assets")

    # 4. Client Gemini + embeddings (avec cache)
    client = genai.Client(api_key=api_key)
    outputs_dir = project_root / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    cache_path = outputs_dir / CACHE_FILE

    print("=== Génération des embeddings ===")
    cache = {} if args.rebuild_index else load_embedding_cache(cache_path)
    if args.rebuild_index:
        print("[INFO] Reconstruction forcée de l'index (--rebuild-index).")

    cache_updated = False
    for note in notes:
        h = content_hash(note["content"])
        cached = cache.get(note["source"], {})
        if cached.get("hash") == h:
            note["embedding"] = cached["embedding"]
            print(f"  [CACHE] {note['source']}  — embedding réutilisé")
        else:
            note["embedding"] = embed_text(client, note["content"], model=embed_model)
            cache[note["source"]] = {"hash": h, "embedding": note["embedding"]}
            cache_updated = True
            print(f"  [NEW]   {note['source']}  — dimension : {len(note['embedding'])}")

    if cache_updated:
        save_embedding_cache(cache_path, cache)
        print(f"  → Cache sauvegardé : {cache_path.relative_to(project_root)}")
    print()

    # 5-8. Recherche et génération (ou retrieve-only)
    label = "Recherche sémantique" if args.retrieve_only else "Recherche et génération"
    print(f"=== {label} ===\n")
    answer(
        client,
        question=args.question,
        notes=notes,
        top_k=args.top_k,
        embed_model=embed_model,
        gen_model=gen_model,
        retrieve_only=args.retrieve_only,
    )


if __name__ == "__main__":
    try:
        main()
    except (EnvironmentError, FileNotFoundError, RuntimeError) as exc:
        print(f"\n[ERREUR] {exc}", file=sys.stderr)
        sys.exit(1)
