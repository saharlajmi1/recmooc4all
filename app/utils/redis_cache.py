import redis
import numpy as np
from sentence_transformers import SentenceTransformer
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_context(chat_history, user_query):
    contextual_query = f"{chat_history} || {user_query}"
    return contextual_query, embedding_model.encode(contextual_query)

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))



def save_to_cache(contextual_query, embedding, response, intent=None):
    """
    Stocke dans Redis un cache global basé uniquement sur le hash du contexte complet (historique + requête).
    """
    cache_key = f"query_hash:{hash(contextual_query)}"
    cache_entry = {
        "embedding": embedding.tolist(),
        "response": response,
        "intent": intent
    }
    redis_client.setex(cache_key, 3600, json.dumps(cache_entry))

def search_in_cache(new_embedding, threshold=0.95):
    """
    Recherche dans le cache Redis global en utilisant la similarité cosinus sur les embeddings.
    Retourne la réponse, la similarité et l'intent du cache.
    """
    pattern = "query_hash:*"
    for key in redis_client.scan_iter(match=pattern):
        value = redis_client.get(key)
        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            continue
        cached_embedding = np.array(data["embedding"])
        similarity = cosine_similarity(new_embedding, cached_embedding)
        if similarity >= threshold:
            return data["response"], similarity, data.get("intent")  # Use .get() for backward compatibility
    return None, 0, None

