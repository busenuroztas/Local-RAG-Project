import sqlite3
import json
import numpy as np

DB_NAME = "rag_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            content TEXT,
            embedding TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_document(filename, chunks, embeddings):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for chunk, emb in zip(chunks, embeddings):
        cursor.execute(
            "INSERT INTO documents (filename, content, embedding) VALUES (?, ?, ?)",
            (filename, chunk, json.dumps(emb))
        )
    conn.commit()
    conn.close()

def get_all_documents():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, content, embedding FROM documents")
    rows = cursor.fetchall()
    conn.close()
    
    docs = []
    for row in rows:
        docs.append({
            "filename": row[0],
            "content": row[1],
            "embedding": json.loads(row[2])
        })
    return docs

def clear_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                content TEXT,
                embedding TEXT
            )
        """)
        cursor.execute("DELETE FROM documents")
        conn.commit()
        conn.close()
        return "Veritabanı başarıyla temizlendi! Yeni dosyalar yükleyebilirsiniz."
    except Exception as e:
        return f"Sıfırlama hatası: {str(e)}"

def cosine_similarity(a, b):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

def get_top_chunks(query_embedding, all_documents, top_k=6):
    if not all_documents:
        return []

    scored_docs = []
    for doc in all_documents:
        sim = cosine_similarity(query_embedding, doc["embedding"])
        scored_docs.append((sim, doc))

    scored_docs.sort(key=lambda x: x[0], reverse=True)
    
    return [doc for score, doc in scored_docs[:top_k]]