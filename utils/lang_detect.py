# utils/lang_detect.py
from sentence_transformers import SentenceTransformer
import chromadb

# Connect to ChromaDB (assumes it's running locally or with persistent config)
client = chromadb.HttpClient(host="localhost", port=8002)
collection = client.get_or_create_collection("language_embeddings")

embedder = SentenceTransformer("all-MiniLM-L6-v2")  # ✅ only once

def detect_language(text: str) -> str:
    print("[LangDetect] Input:", text)
    embedding = embedder.encode([text])[0]
    result = collection.query(query_embeddings=[embedding], n_results=1)
    if result and result["metadatas"] and result["metadatas"][0]:
        lang = result["metadatas"][0][0]["lang"]
        print("[LangDetect] Detected Language:", lang)
        return lang
    return "unknown"