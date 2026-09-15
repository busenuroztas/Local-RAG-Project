import os
import gradio as gr
from openai import OpenAI

from database.db_manager import init_db, clear_db, save_document, get_all_documents, get_top_chunks
from models.embedding import get_embedding
from utils.file_loader import load_file, chunk_text

CHAT_MODEL = "phi-3.5-mini"
EMBED_MODEL = "qwen3-embedding-0.6b"

CLIENT = None

def handle_file_upload(file):
    global CLIENT
    if CLIENT is None:
        return "Yapay zeka istemcisi başlatılmadı. Lütfen uygulamayı main.py üzerinden çalıştırın."

    if file is None:
        return "Lütfen bir dosya yükleyin."
    
    file_path = file.name if hasattr(file, 'name') else file
    filename = os.path.basename(file_path)
    
    try:
        text = load_file(file_path)
        if not text.strip():
            return f"'{filename}' dosyasından okunabilir metin çıkarılamadı."
        
        chunks = chunk_text(text, chunk_size=1000, overlap=150)
        if not chunks:
            return f"'{filename}' dosyasında bölünecek metin bulunamadı."
        
        embeddings = []
        for chunk in chunks:
            emb = get_embedding(CLIENT, chunk, EMBED_MODEL)
            if emb:
                embeddings.append(emb)
        
        if len(embeddings) != len(chunks):
            return "Vektör oluşturma aşamasında bir hata oluştu. Foundry Local sunucusunu kontrol edin."

        save_document(filename, chunks, embeddings)
        return f"'{filename}' başarıyla işlendi ve {len(chunks)} parça veritabanına eklendi."
    
    except Exception as e:
        return f"Dosya yükleme hatası: {str(e)}"

def chat_respond(message):
    global CLIENT
    if CLIENT is None:
        return "Yapay zeka istemcisi başlatılmadı. Lütfen uygulamayı main.py üzerinden çalıştırın."

    if not message or not str(message).strip():
        return "Lütfen geçerli bir soru girin."
    
    query_text = str(message).strip()
    
    try:
        documents = get_all_documents()
        if not documents:
            return "Veritabanında henüz hiç doküman yok. Lütfen önce sol taraftan bir dosya yükleyin."
        
        query_emb = get_embedding(CLIENT, query_text, EMBED_MODEL)
        if not query_emb:
            return "Soru için vektör üretilemedi. Foundry Local bağlantısını kontrol edin."

        relevant_docs = get_top_chunks(query_emb, documents, top_k=5)
        if not relevant_docs:
            return "Bağlantılı herhangi bir doküman parçası bulunamadı."

        context_text = "\n\n---\n\n".join(
            [f"[Kaynak: {doc['filename']}]\n{doc['content']}" for doc in relevant_docs]
        )
        
        system_prompt = (
    "Sen son derece dikkatli, tarafsız ve akıcı Türkçe konuşan bir yapay zeka asistansın.\n"
    "Görevin: Aşağıda verilen bağlam (context) bilgilerini analiz ederek kullanıcının sorusuna doğrudan yanıt vermektir.\n\n"
    "Kurallar:\n"
    "1. Yalnızca sağlanan bağlamdaki bilgilere dayan. Bağlamda yer almayan hiçbir bilgiyi dışarıdan ekleme veya tahmin etme.\n"
    "2. Metindeki başlıklar, kategoriler, alt gruplar ve listeler arasındaki ayrımlara kesinlikle dikkat et. Bir kategoriye ait bilgiyi başka bir kategoriyle karıştırma.\n"
    "3. Yanıtı anlaşılır, düzgün bir gramer ve doğal bir Türkçe ile oluştur. Gereksiz tekrarlardan ve karmaşık cümlelerden kaçın.\n"
    "4. Eğer bağlamda sorunun cevabı açıkça bulunmuyorsa, kesinlikle uydurma yapma ve sadece 'Verilen dokümanlarda bu sorunun cevabı bulunmamaktadır.' yanıtını ver."
)
        user_prompt = f"Bağlam Bilgisi:\n{context_text}\n\nSoru: {query_text}"
        
        response = CLIENT.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1 
        )
        
        bot_content = response.choices[0].message.content
        if not bot_content or not bot_content.strip():
            return "Model boş bir yanıt döndürdü. Lütfen sorunuzu tekrar girin."
            
        return bot_content
        
    except Exception as e:
        return f"Bir hata oluştu: {str(e)}"

def user_submit(user_msg, history):
    if not user_msg or not user_msg.strip():
        return "", history
    
    if history is None:
        history = []
    
    bot_reply = chat_respond(user_msg)
    
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": bot_reply})
    
    return "", history

def launch_gradio_app(server_url):
    global CLIENT
    CLIENT = OpenAI(
        base_url=server_url,
        api_key="foundry-local"
    )

    init_db()

    with gr.Blocks(title="Microsoft Local RAG Projesi") as demo:
        gr.Markdown("# Local RAG - Doküman Soru/Cevap Sistemi")
        
        with gr.Row():
            with gr.Column(scale=1):
                file_input = gr.File(label="Dosya Yükle (.pdf, .txt, .docx, .doc)", file_types=[".pdf", ".txt", ".docx", ".doc"])
                upload_btn = gr.Button("Dokümanı İşle", variant="primary")
                status_output = gr.Textbox(label="İşlem Durumu", lines=3, interactive=False)
                
                clear_db_btn = gr.Button("Veritabanını Sıfırla", variant="stop")
                
                upload_btn.click(
                    fn=handle_file_upload,
                    inputs=[file_input],
                    outputs=[status_output]
                )
                
                clear_db_btn.click(
                    fn=clear_db,
                    inputs=[],
                    outputs=[status_output]
                )
                
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(label="Sohbet Geçmişi", height=500)
                msg_input = gr.Textbox(label="Sorunuzu yazın ve Enter'a basın...", placeholder="Örn: Bu raporda ne anlatılıyor?")
                clear_chat_btn = gr.Button("Sohbeti Temizle")

                msg_input.submit(
                    fn=user_submit,
                    inputs=[msg_input, chatbot],
                    outputs=[msg_input, chatbot]
                )

                clear_chat_btn.click(lambda: [], None, chatbot, queue=False)

    demo.launch(server_name="0.0.0.0", server_port=7865)

if __name__ == "__main__":
    launch_gradio_app("http://127.0.0.1:5272/v1")