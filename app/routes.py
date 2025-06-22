from fastapi import APIRouter, HTTPException, Depends, Query
from app.db import database
from app.models import Post, PostCreate, UserTagInteractionCreate
from app.enhanced_recommender import EnhancedRecommender
from typing import List, Optional
import json
from datetime import datetime, timedelta

router = APIRouter()

# Global enhanced model instance
recommender = EnhancedRecommender()

async def load_recommender_data(force_reload=False):
    """
    Gelişmiş öneri modeli için gerekli verileri yükle ve modeli başlat
    """
    # Model zaten eğitilmişse ve force_reload false ise erken çık
    if recommender.feature_matrix is not None and not force_reload:
        return recommender
        
    print("🚀 Gelişmiş öneri sistemi yükleniyor...")
        
    # Gönderileri çek
    posts_query = "SELECT * FROM posts ORDER BY created_at DESC"
    posts = await database.fetch_all(posts_query)
    posts_list = [dict(row) for row in posts]
    
    # Etiketleri JSON dizesinden listeye dönüştür
    for post in posts_list:
        if isinstance(post.get("tags"), str):
            try:
                post["tags"] = json.loads(post["tags"])
            except:
                post["tags"] = []
    
    # Modeli eğit (içerik analizi dahil)
    await recommender.fit(posts_list, use_content_analysis=True)
    
    # Kullanıcı etkileşimlerini yükleme (bu artık fit içinde yapılıyor)
    # await load_user_interactions() # Bu satır gereksiz
    
    print("✅ Gelişmiş öneri sistemi hazır!")
    return recommender

async def load_user_interactions():
    """
    Kullanıcı etkileşimlerini veritabanından yükle
    """
    # Likes tablosundan etkileşimleri çek
    likes_query = """
        SELECT user_id, post_id, 'like' as interaction_type, liked_at as timestamp
        FROM Likes
        ORDER BY liked_at DESC
    """
    likes = await database.fetch_all(likes_query)
    
    # Comments tablosundan etkileşimleri çek
    comments_query = """
        SELECT user_id, post_id, 'comment' as interaction_type, created_at as timestamp
        FROM Comments
        ORDER BY created_at DESC
    """
    comments = await database.fetch_all(comments_query)
    
    # Etkileşimleri modele yükle
    for like in likes:
        recommender.update_user_interactions(
            user_id=like['user_id'],
            post_id=like['post_id'],
            interaction_type='like',
            weight=3.0
        )
    
    for comment in comments:
        recommender.update_user_interactions(
            user_id=comment['user_id'],
            post_id=comment['post_id'],
            interaction_type='comment',
            weight=4.0
        )
    
    print(f"✅ {len(likes)} like ve {len(comments)} yorum etkileşimi yüklendi.")

@router.post("/track-interaction")
async def track_interaction(user_id: int, post_id: int, interaction_type: str):
    """
    Kullanıcı etkileşimini kaydet ve öneri modelini güncelle
    """
    # Öneri modelini yükle
    await load_recommender_data()
    
    # Etkileşim ağırlıkları
    weights = {
        'view': 1.0,
        'like': 3.0,
        'comment': 4.0,
        'share': 5.0
    }
    
    weight = weights.get(interaction_type, 1.0)
    
    # Modeli güncelle
    recommender.update_user_interactions(
        user_id=user_id,
        post_id=post_id,
        interaction_type=interaction_type,
        weight=weight
    )
    
    return {
        "status": "success",
        "message": f"Etkileşim kaydedildi: {interaction_type}",
        "user_id": user_id,
        "post_id": post_id,
        "weight": weight
    }

@router.get("/recommendations")
async def get_recommendations(user_id: int = Query(...), limit: int = 50):
    """
    Kullanıcıya kişiselleştirilmiş içerik önerileri sunar
    """
    # Öneri modelini yükle
    await load_recommender_data()
    
    # Kullanıcıya özel öneriler yap
    recommendations = await recommender.recommend_for_user(
        user_id=user_id,
        top_n=limit,
        exclude_seen=True
    )
    
    return {
        "user_id": user_id,
        "recommendations": recommendations,
        "count": len(recommendations),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/post-analysis/{post_id}")
async def get_post_analysis(post_id: int):
    """
    Belirli bir postun detaylı analizini döndürür
    """
    await load_recommender_data()
    
    # Post analiz sonuçlarını al
    if post_id in recommender.post_analysis:
        analysis = recommender.post_analysis[post_id]
        return {
            "post_id": post_id,
            "analysis": analysis,
            "status": "analyzed"
        }
    else:
        # Post bulunamadı veya analiz edilmemiş
        post_query = "SELECT * FROM posts WHERE id = :post_id"
        post = await database.fetch_one(post_query, {"post_id": post_id})
        
        if not post:
            raise HTTPException(status_code=404, detail="Post bulunamadı")
        
        return {
            "post_id": post_id,
            "status": "not_analyzed",
            "message": "Bu post henüz analiz edilmemiş"
        }

@router.get("/similar-posts/{post_id}")
async def get_similar_posts(post_id: int, limit: int = Query(5, ge=1, le=20)):
    """
    Belirli bir posta benzer postları döndürür
    """
    await load_recommender_data()
    
    similar = recommender.get_similar_posts(post_id, limit)
    
    if not similar:
        raise HTTPException(status_code=404, detail="Benzer post bulunamadı veya post mevcut değil")
    
    return {
        "post_id": post_id,
        "similar_posts": similar,
        "count": len(similar)
    }

@router.get("/user-profile/{user_id}")
async def get_user_interest_profile(user_id: int):
    """
    Kullanıcının ilgi profiline ilişkin bir özet döndürür.
    Veriyi doğrudan user_tag_interactions tablosundan alır.
    """
    profile = await recommender.get_user_interest_profile(user_id)
    return profile

@router.get("/topics")
async def get_topics():
    """
    Tüm konuların özetini döndürür
    """
    await load_recommender_data()
    
    topics_summary = recommender.get_topics_summary()
    
    return topics_summary

@router.get("/topic-posts/{topic_id}")
async def get_topic_posts(topic_id: int, limit: int = Query(10, le=50)):
    """
    Belirli bir konudaki postları döndürür
    """
    await load_recommender_data()
    
    topic_posts = recommender.get_topic_posts(topic_id, top_n=limit)
    
    return {
        "topic_id": topic_id,
        "posts": topic_posts,
        "count": len(topic_posts)
    }

@router.post("/analyze-new-posts")
async def analyze_new_posts():
    """
    Son 3 saatte eklenen yeni postları analiz eder
    """
    # Son 3 saatteki postları bul
    three_hours_ago = datetime.now() - timedelta(hours=3)
    
    new_posts_query = """
        SELECT * FROM posts 
        WHERE created_at >= :since_time
        ORDER BY created_at DESC
    """
    new_posts = await database.fetch_all(new_posts_query, {"since_time": three_hours_ago})
    new_posts_list = [dict(row) for row in new_posts]
    
    if not new_posts_list:
        return {
            "status": "no_new_posts",
            "message": "Son 3 saatte yeni post eklenmemiş",
            "analyzed_count": 0
        }
    
    # Etiketleri düzenle
    for post in new_posts_list:
        if isinstance(post.get("tags"), str):
            try:
                post["tags"] = json.loads(post["tags"])
            except:
                post["tags"] = []
    
    # Yeni postları mevcut sisteme ekle ve analiz et
    await load_recommender_data()
    
    # Mevcut postlarla birleştir
    all_posts = recommender.posts + new_posts_list
    
    # Modeli yeniden eğit
    recommender.fit(all_posts, use_content_analysis=True)
    
    return {
        "status": "success",
        "message": "Yeni postlar analiz edildi",
        "analyzed_count": len(new_posts_list),
        "total_posts": len(all_posts),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/retrain-model")
async def retrain_model():
    """
    Öneri modelini tüm verileri kullanarak yeniden eğitir (günlük eğitim)
    """
    # Modeli zorla yeniden eğit
    await load_recommender_data(force_reload=True)
    
    # Modelleri kaydet
    recommender.save_models()
    
    return {
        "status": "success",
        "message": "Model başarıyla yeniden eğitildi ve kaydedildi",
        "posts_count": len(recommender.posts),
        "features_count": recommender.feature_matrix.shape[1] if recommender.feature_matrix is not None else 0,
        "users_count": len(recommender.user_profiles),
        "topics_count": len(recommender.content_analyzer.cluster_keywords),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/feed")
async def feed(user_id: int = Query(...), limit: int = 100):
    """
    Kullanıcıya kişiselleştirilmiş ana feed'i döndürür.
    Bu endpoint, `recommendations` ile aynı mantığı kullanır ancak
    genellikle daha fazla sayıda sonuç döndürür.
    """
    # Öneri modelini yükle ve kullanıcı profillerini hazırla
    await load_recommender_data()
    
    # Kullanıcıya özel öneriler yap
    recommendations = await recommender.recommend_for_user(
        user_id=user_id,
        top_n=limit,
        exclude_seen=True
    )
    
    # Eğer hiç öneri yoksa, popüler gönderileri döndür
    if not recommendations:
        recommendations = recommender._get_diversified_popular_posts(top_n=limit)

    return {
        "user_id": user_id,
        "feed": recommendations,
        "count": len(recommendations),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/interact")
async def interact(interaction: UserTagInteractionCreate):
    """
    Eski etkileşim endpoint'i (geriye uyumluluk için)
    """
    return await track_interaction(
        user_id=interaction.user_id,
        post_id=1,  # Varsayılan post ID
        interaction_type=interaction.interaction_type
    ) 