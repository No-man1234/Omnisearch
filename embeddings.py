import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Restrict multi-threading memory buffers in low-memory container environments (e.g. Render 512MB tier)
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "fastembed")
_model_instance = None

def _get_fastembed_model():
    global _model_instance
    if _model_instance is None:
        from fastembed import TextEmbedding
        model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        print(f"Loading FastEmbed model: {model_name} (constrained to 1 thread for low-memory container limits)...")
        # Explicitly pass threads=1 to prevent ONNX Runtime from spawning 32-64 thread buffers on cloud host nodes
        _model_instance = TextEmbedding(model_name=model_name, threads=1)
    return _model_instance

def get_embedding(text: str) -> List[float]:
    """Generates a single dense embedding vector for the given text."""
    return get_embeddings([text])[0]

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Generates dense embedding vectors for a batch of texts."""
    model = _get_fastembed_model()
    embeddings = list(model.embed(texts))
    return [emb.tolist() for emb in embeddings]

def get_embedding_dimension() -> int:
    return int(os.getenv("EMBEDDING_DIM", "384"))
