def get_embedding(client, text: str, model_name: str = "qwen3-embedding-0.6b") -> list:
    
    if not text or not text.strip():
        return []
        
    try:
        response = client.embeddings.create(
            input=text,
            model=model_name
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding oluşturma hatası: {str(e)}")
        return []