#!/usr/bin/env python3
import asyncio
import json
from app.db import database
from app.models import Post, PostCreate, parse_json_tags
from typing import List, Dict, Any

async def test_post_model():
    try:
        # Veritabanına bağlan
        print("Veritabanına bağlanılıyor...")
        await database.connect()
        print("Veritabanı bağlantısı başarılı!")

        # Posts tablosundaki tüm alanları çek
        query = """
        SELECT column_name, data_type, character_maximum_length 
        FROM information_schema.columns 
        WHERE table_name = 'posts'
        """
        columns = await database.fetch_all(query)
        
        # Tablo yapısını yazdır
        print("\nPosts Tablosu Yapısı:")
        for column in columns:
            print(f"Alan: {column['column_name']}, Tür: {column['data_type']}")
        
        # Örnek veri çek ve modelle eşleşip eşleşmediğini kontrol et
        query = "SELECT * FROM posts LIMIT 1"
        result = await database.fetch_one(query)
        
        if result:
            # Dict'e dönüştür
            result_dict = dict(result)
            
            print("\nÖrnek Veri:")
            for key, value in result_dict.items():
                print(f"{key}: {value} ({type(value).__name__})")
            
            # Tags alanını işle
            if 'tags' in result_dict and result_dict['tags']:
                try:
                    if isinstance(result_dict['tags'], str):
                        result_dict['tags'] = json.loads(result_dict['tags'])
                    print(f"İşlenmiş tags: {result_dict['tags']} ({type(result_dict['tags']).__name__})")
                except Exception as e:
                    print(f"Tags alanını işlerken hata: {e}")
            
            # Modele dönüştürmeyi dene
            try:
                post = Post(**result_dict)
                print("\nModel Doğrulaması: BAŞARILI ✅")
                print(f"Post modeli: {post}")
                print(f"Tags: {post.tags}")
            except Exception as e:
                print(f"\nModel Doğrulaması: BAŞARISIZ ❌")
                print(f"Hata: {e}")

    except Exception as e:
        print(f"Hata oluştu: {e}")
    finally:
        # Bağlantıyı kapat
        await database.disconnect()
        print("\nVeritabanı bağlantısı kapatıldı.")

if __name__ == "__main__":
    asyncio.run(test_post_model()) 