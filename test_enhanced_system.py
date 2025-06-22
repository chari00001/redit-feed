#!/usr/bin/env python3
import asyncio
import json
import sys
from app.db import database
from app.enhanced_recommender import EnhancedRecommender

async def get_user_recommendations(user_id: int, limit: int = 50):
    """
    Belirli bir kullanıcı için kişiselleştirilmiş öneriler alır
    """
    try:
        print(f"🚀 Kullanıcı {user_id} için {limit} öneri getiriliyor...")
        print("-" * 50)
        
        # Veritabanına bağlan
        await database.connect()
        print("✅ Veritabanı bağlantısı kuruldu")
        
        # Tüm postları yükle
        posts_query = "SELECT * FROM posts ORDER BY created_at DESC"
        posts = await database.fetch_all(posts_query)
        posts_list = [dict(row) for row in posts]
        
        # Etiketleri düzenle
        for post in posts_list:
            if isinstance(post.get("tags"), str):
                try:
                    post["tags"] = json.loads(post["tags"])
                except:
                    post["tags"] = []
        
        print(f"📊 {len(posts_list)} post yüklendi")
        
        # Öneri sistemini başlat
        recommender = EnhancedRecommender()
        await recommender.fit(posts_list, use_content_analysis=True)
        print("✅ Öneri sistemi hazırlandı")
        
        # Kullanıcı etkileşimlerini yükle (yeni yapı)
        await recommender.load_user_profiles_from_db(user_id)
        
        # Önerileri al
        recommendations = await recommender.recommend_for_user(user_id, top_n=limit)
        
        # Sonuçları göster
        print(f"\n🎯 Kullanıcı {user_id} için {len(recommendations)} öneri:")
        print("=" * 50)
        
        for i, rec in enumerate(recommendations, 1):
            title = rec.get('title', 'Başlık yok')[:60]
            score = rec.get('recommendation_score', 0)
            reason = rec.get('recommendation_reason', 'Genel öneri')
            
            print(f"{i:2d}. Post {rec['id']}: {title}")
            print(f"    📊 Skor: {score:.3f}")
            print(f"    💡 Neden: {reason}")
            
            # Etiketleri göster
            if rec['id'] in recommender.post_analysis:
                tags = recommender.post_analysis[rec['id']].get('enhanced_tags', [])[:3]
                if tags:
                    print(f"    🏷️  Etiketler: {', '.join(tags)}")
            elif rec.get('tags'):
                tags = rec['tags'][:3]
                print(f"    🏷️  Etiketler: {', '.join(tags)}")
            print()
        
        print("✅ Öneriler başarıyla getirildi!")
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await database.disconnect()
        print("✅ Veritabanı bağlantısı kapatıldı")

async def load_user_interactions(recommender, user_id):
    """
    DEPRECATED: Bu fonksiyon artık kullanılmayacak.
    Yeni yapı user_tag_interactions tablosuna dayanıyor.
    """
    pass

def main():
    """
    Ana fonksiyon - komut satırından kullanıcı ID alır
    """
    if len(sys.argv) < 2:
        print("📋 Kullanım: python test_enhanced_system.py <user_id> [limit]")
        print("📋 Örnek: python test_enhanced_system.py 123")
        print("📋 Örnek: python test_enhanced_system.py 123 5")
        sys.exit(1)
    
    try:
        user_id = int(sys.argv[1])
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        
        if limit < 1 or limit > 50:
            print("⚠️  Limit 1-50 arasında olmalı!")
            sys.exit(1)
            
        asyncio.run(get_user_recommendations(user_id, limit))
        
    except ValueError:
        print("❌ Geçersiz kullanıcı ID! Sayı girmelisiniz.")
        sys.exit(1)

if __name__ == "__main__":
    main() 