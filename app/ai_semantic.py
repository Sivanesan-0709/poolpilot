import time
from typing import List, Dict, Any, Optional
from app.config import AI_CONFIG
from app.routing import load_chennai_places

_SENTENCE_MODEL = None
_PRECOMPUTED_EMBEDDINGS = None


def get_sentence_model():
    """Lazy-loads sentence-transformers MiniLM model."""
    global _SENTENCE_MODEL
    if not AI_CONFIG.get("ENABLE_SEMANTIC_SEARCH", True):
        return None
    if _SENTENCE_MODEL is not None:
        return _SENTENCE_MODEL
    try:
        from sentence_transformers import SentenceTransformer
        _SENTENCE_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        return _SENTENCE_MODEL
    except Exception:
        return None


def semantic_place_search(
    query: str,
    limit: int = 8
) -> Dict[str, Any]:
    """
    Ranks Chennai gazetteer locations using semantic text embeddings (all-MiniLM-L6-v2).
    Allows free-text queries like 'IT park near OMR', 'engineering college in west', 'beach in south'.
    Falls back to multi-keyword weighted gazetteer search if model is missing or times out.
    """
    if not query or not query.strip():
        return {
            "query": query,
            "results": load_chennai_places()[:limit],
            "model_used": "Gazetteer Direct",
            "is_fallback": False
        }

    start_time = time.time()
    places = load_chennai_places()
    is_fallback = True
    ranked_results = []

    # 1. Try Sentence Transformers
    if AI_CONFIG.get("ENABLE_SEMANTIC_SEARCH", True):
        try:
            model = get_sentence_model()
            if model is not None and (time.time() - start_time) < AI_CONFIG.get("MODEL_TIMEOUT_SECONDS", 5.0):
                from sentence_transformers import util
                place_texts = [f"{p['name']} in {p.get('zone','')} Chennai {p.get('category','')} {' '.join(p.get('keywords',[]))}" for p in places]
                query_emb = model.encode(query, convert_to_tensor=True)
                place_embs = model.encode(place_texts, convert_to_tensor=True)
                cos_scores = util.cos_sim(query_emb, place_embs)[0].tolist()

                scored = [(cos_scores[i], places[i]) for i in range(len(places))]
                scored.sort(key=lambda x: x[0], reverse=True)
                ranked_results = [item[1] for item in scored[:limit]]
                is_fallback = False
        except Exception:
            pass

    # 2. Multi-Keyword Semantic Fallback
    if is_fallback or not ranked_results:
        q_tokens = query.lower().split()
        scored = []
        for p in places:
            p_text = f"{p['name']} {p.get('zone','')} {p.get('category','')} {' '.join(p.get('keywords',[]))}".lower()
            score = 0
            for t in q_tokens:
                if t in p_text:
                    score += 20
                if t == p.get("category", ""):
                    score += 35
                if t in p.get("zone", "").lower():
                    score += 30

            if score > 0:
                scored.append((score, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        ranked_results = [item[1] for item in scored[:limit]] if scored else places[:limit]
        is_fallback = True

    return {
        "query": query,
        "results": ranked_results,
        "count": len(ranked_results),
        "model_used": "sentence-transformers (all-MiniLM-L6-v2)" if not is_fallback else "Multi-Keyword Semantic Search (Fallback)",
        "is_fallback": is_fallback
    }
