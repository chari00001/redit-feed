import json
from typing import Any, Dict

import gradio as gr
import requests

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"  # FastAPI'deki router prefix

def safe_request(method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    """Yardımcı istek fonksiyonu: hata yakalama ve JSON yanıtını döndürme"""
    url = f"{BASE_URL}{API_PREFIX}{endpoint}"
    try:
        if method.lower() == "get":
            resp = requests.get(url, **kwargs)
        else:
            resp = requests.post(url, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e), "endpoint": endpoint}

# ---------------------- API Sarmalayıcı Fonksiyonlar ---------------------- #

def get_feed(user_id: int, limit: int) -> Dict[str, Any]:
    return safe_request("get", "/feed", params={"user_id": user_id, "limit": limit})

def get_recommendations(user_id: int, limit: int) -> Dict[str, Any]:
    return safe_request("get", "/recommendations", params={"user_id": user_id, "limit": limit})

def track_interaction(user_id: int, post_id: int, interaction_type: str) -> Dict[str, Any]:
    return safe_request(
        "post",
        "/track-interaction",
        params={"user_id": user_id, "post_id": post_id, "interaction_type": interaction_type},
    )

def get_similar_posts(post_id: int, limit: int) -> Dict[str, Any]:
    return safe_request("get", f"/similar-posts/{post_id}", params={"limit": limit})

def get_post_analysis(post_id: int) -> Dict[str, Any]:
    return safe_request("get", f"/post-analysis/{post_id}")

def get_topics() -> Dict[str, Any]:
    return safe_request("get", "/topics")

def get_topic_posts(topic_id: int, limit: int) -> Dict[str, Any]:
    return safe_request("get", f"/topic-posts/{topic_id}", params={"limit": limit})

def analyze_new_posts() -> Dict[str, Any]:
    return safe_request("post", "/analyze-new-posts")

def retrain_model() -> Dict[str, Any]:
    return safe_request("post", "/retrain-model")

def get_user_profile(user_id: int) -> Dict[str, Any]:
    return safe_request("get", f"/user-profile/{user_id}")

# --------------------------- Gradio Arayüzü --------------------------- #

def json_pretty(obj: Dict[str, Any]) -> str:
    """JSON çıktısını okunabilir biçime getirir"""
    return json.dumps(obj, indent=2, ensure_ascii=False)

with gr.Blocks(title="Redit Öneri Sistemi Arayüzü") as demo:
    gr.Markdown("# 🚀 Redit Öneri Sistemi Gradio Arayüzü\nTüm API fonksiyonlarını kolayca test edin.")

    with gr.Tab("Feed"):
        user_feed = gr.Number(label="Kullanıcı ID", value=1)
        limit_feed = gr.Slider(minimum=1, maximum=200, value=100, step=1, label="Gönderi Limiti")
        btn_feed = gr.Button("Feed'i Getir")
        out_feed = gr.Code(label="Sonuç (JSON)")
        btn_feed.click(lambda uid, lim: json_pretty(get_feed(int(uid), int(lim))), inputs=[user_feed, limit_feed], outputs=out_feed)

    with gr.Tab("Öneriler"):
        user_rec = gr.Number(label="Kullanıcı ID", value=1)
        limit_rec = gr.Slider(minimum=1, maximum=100, value=50, step=1, label="Öneri Limiti")
        btn_rec = gr.Button("Önerileri Getir")
        out_rec = gr.Code(label="Sonuç (JSON)")
        btn_rec.click(lambda uid, lim: json_pretty(get_recommendations(int(uid), int(lim))), inputs=[user_rec, limit_rec], outputs=out_rec)

    with gr.Tab("Etkileşim Takip"):
        user_int = gr.Number(label="Kullanıcı ID", value=1)
        post_int = gr.Number(label="Post ID", value=1)
        type_int = gr.Dropdown(["view", "like", "comment", "share"], value="view", label="Etkileşim Türü")
        btn_int = gr.Button("Etkileşimi Gönder")
        out_int = gr.Code(label="Sonuç (JSON)")
        btn_int.click(lambda uid, pid, t: json_pretty(track_interaction(int(uid), int(pid), t)), inputs=[user_int, post_int, type_int], outputs=out_int)

    with gr.Tab("Benzer Postlar"):
        post_sim = gr.Number(label="Post ID", value=1)
        limit_sim = gr.Slider(minimum=1, maximum=20, value=5, step=1, label="Limit")
        btn_sim = gr.Button("Benzerleri Getir")
        out_sim = gr.Code(label="Sonuç (JSON)")
        btn_sim.click(lambda pid, lim: json_pretty(get_similar_posts(int(pid), int(lim))), inputs=[post_sim, limit_sim], outputs=out_sim)

    with gr.Tab("Post Analizi"):
        post_ana = gr.Number(label="Post ID", value=1)
        btn_ana = gr.Button("Analizi Getir")
        out_ana = gr.Code(label="Sonuç (JSON)")
        btn_ana.click(lambda pid: json_pretty(get_post_analysis(int(pid))), inputs=post_ana, outputs=out_ana)

    with gr.Tab("Konular"):
        btn_topics = gr.Button("Konuları Listele")
        out_topics = gr.Code(label="Sonuç (JSON)")
        btn_topics.click(lambda: json_pretty(get_topics()), inputs=None, outputs=out_topics)

    with gr.Tab("Konu Postları"):
        topic_id = gr.Number(label="Konu ID", value=0)
        limit_topic = gr.Slider(minimum=1, maximum=50, value=10, step=1, label="Limit")
        btn_topic = gr.Button("Postları Getir")
        out_topic = gr.Code(label="Sonuç (JSON)")
        btn_topic.click(lambda tid, lim: json_pretty(get_topic_posts(int(tid), int(lim))), inputs=[topic_id, limit_topic], outputs=out_topic)

    with gr.Tab("Yeni Postları Analiz Et"):
        btn_new_posts = gr.Button("Analizi Başlat")
        out_new_posts = gr.Code(label="Sonuç (JSON)")
        btn_new_posts.click(lambda: json_pretty(analyze_new_posts()), inputs=None, outputs=out_new_posts)

    with gr.Tab("Modeli Yeniden Eğit"):
        btn_retrain = gr.Button("Yeniden Eğit")
        out_retrain = gr.Code(label="Sonuç (JSON)")
        btn_retrain.click(lambda: json_pretty(retrain_model()), inputs=None, outputs=out_retrain)

    with gr.Tab("Kullanıcı Profili"):
        user_prof = gr.Number(label="Kullanıcı ID", value=1)
        btn_prof = gr.Button("Profili Getir")
        out_prof = gr.Code(label="Sonuç (JSON)")
        btn_prof.click(lambda uid: json_pretty(get_user_profile(int(uid))), inputs=user_prof, outputs=out_prof)

if __name__ == "__main__":
    demo.launch() 