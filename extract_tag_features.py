#!/usr/bin/env python3
import asyncio
import numpy as np
import json
import os
from app.db import database
from app.features import TagFeatureExtractor

async def extract_tag_features():
    try:
        # Veritabanına bağlan
        print("Veritabanına bağlanılıyor...")
        await database.connect()
        print("Veritabanı bağlantısı başarılı!")

        # Posts tablosundaki tüm verileri çek
        query = "SELECT id, title, tags FROM posts"
        results = await database.fetch_all(query)
        
        # Dict listesine dönüştür
        posts = [dict(row) for row in results]
        print(f"Toplam {len(posts)} gönderi bulundu.")
        
        # Etiket vektörlerini oluştur - TF-IDF ile
        print("\nTF-IDF vektörleri oluşturuluyor...")
        tfidf_extractor = TagFeatureExtractor(method="tfidf")
        tfidf_vectors = tfidf_extractor.fit_transform(posts)
        
        print(f"TF-IDF vektör boyutu: {tfidf_vectors.shape}")
        print(f"Toplam {len(tfidf_extractor.feature_names)} benzersiz etiket bulundu.")
        
        # İlk 5 gönderinin etiket vektörlerini yazdır
        print("\nİlk 5 gönderinin TF-IDF vektörleri:")
        for i in range(min(5, len(posts))):
            # Seyrek matris olduğu için yoğun matrise dönüştürüyoruz
            if hasattr(tfidf_vectors, "toarray"):
                dense_vector = tfidf_vectors[i].toarray()[0]
            else:
                dense_vector = tfidf_vectors[i]
                
            # Sıfır olmayan değerleri yazdır
            nonzero_indices = np.nonzero(dense_vector)[0]
            nonzero_features = {tfidf_extractor.feature_names[idx]: dense_vector[idx] for idx in nonzero_indices}
            
            print(f"Gönderi ID: {posts[i]['id']}, Başlık: {posts[i]['title']}")
            print(f"Etiketler: {posts[i]['tags']}")
            print(f"TF-IDF: {nonzero_features}")
            print()
        
        # One-Hot Encoding ile
        print("\nOne-Hot Encoding vektörleri oluşturuluyor...")
        onehot_extractor = TagFeatureExtractor(method="onehot")
        onehot_vectors = onehot_extractor.fit_transform(posts)
        
        print(f"One-Hot vektör boyutu: {onehot_vectors.shape}")
        
        # İlk 5 gönderinin etiket vektörlerini yazdır
        print("\nİlk 5 gönderinin One-Hot vektörleri:")
        for i in range(min(5, len(posts))):
            # Seyrek matris olduğu için yoğun matrise dönüştürüyoruz
            if hasattr(onehot_vectors, "toarray"):
                dense_vector = onehot_vectors[i].toarray()[0]
            else:
                dense_vector = onehot_vectors[i]
                
            # Sıfır olmayan değerleri yazdır
            nonzero_indices = np.nonzero(dense_vector)[0]
            nonzero_features = {onehot_extractor.feature_names[idx]: dense_vector[idx] for idx in nonzero_indices}
            
            print(f"Gönderi ID: {posts[i]['id']}, Başlık: {posts[i]['title']}")
            print(f"Etiketler: {posts[i]['tags']}")
            print(f"One-Hot: {nonzero_features}")
            print()

    except Exception as e:
        print(f"Hata oluştu: {e}")
    finally:
        # Bağlantıyı kapat
        await database.disconnect()
        print("\nVeritabanı bağlantısı kapatıldı.")

if __name__ == "__main__":
    asyncio.run(extract_tag_features()) 