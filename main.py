import os
from foundry_local_sdk import Configuration, FoundryLocalManager
from app import launch_gradio_app  

def main():
    print("Foundry Local Servisi Başlatılıyor...")
    config = Configuration(app_name="MicrosoftRagProjesi")
    FoundryLocalManager.initialize(config)
    manager = FoundryLocalManager.instance

    embed_model_name = "qwen3-embedding-0.6b"
    chat_model_name = "phi-3.5-mini"

    print(f"Embedding Modeli hazırlanıyor: '{embed_model_name}'...")
    embed_model = manager.catalog.get_model(embed_model_name)
    if not embed_model.is_cached:
        print("Embedding modeli indiriliyor, lütfen bekleyin...")
        embed_model._selected_variant.download()
    embed_model.load()

    print(f"Chat Modeli hazırlanıyor: '{chat_model_name}'...")
    chat_model = manager.catalog.get_model(chat_model_name)
    if not chat_model.is_cached:
        print("Chat modeli indiriliyor, lütfen bekleyin...")
        chat_model._selected_variant.download()
    chat_model.load()

    manager.start_web_service()
    server_url = manager.urls[0]
    print(f"Foundry Local Servisi Aktif: {server_url}")

    print("Gradio Kullanıcı Arayüzü Açılıyor...")
    launch_gradio_app(server_url=f"{server_url}/v1")

if __name__ == "__main__":
    main()