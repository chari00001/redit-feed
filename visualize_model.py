#!/usr/bin/env python3
import asyncio
import numpy as np
import json
import pandas as pd
from app.db import database
from app.features import TagFeatureExtractor
from app.recommender import ContentBasedRecommender
from sklearn.metrics.pairwise import cosine_similarity

async def visualize_model():
    try:
        print("-" * 80)
        print("ÖNERİ MODELİ VİZUALİZASYONU")
        print("-" * 80)
        
        # Veritabanına bağlan
        print("\n[1] Veritabanına bağlanılıyor...")
        await database.connect()
        print("Veritabanı bağlantısı başarılı!")

        # Gönderileri çek
        posts_query = "SELECT id, title, tags FROM posts LIMIT 30"
        posts = await database.fetch_all(posts_query)
        posts_list = [dict(row) for row in posts]
        
        # Etiketleri JSON dizesinden listeye dönüştür
        for post in posts_list:
            if isinstance(post.get("tags"), str):
                try:
                    post["tags"] = json.loads(post["tags"])
                except:
                    post["tags"] = []
        
        print(f"Analiz için {len(posts_list)} gönderi yüklendi.")
        
        # Etiket vektörlerini oluştur - TF-IDF kullanılıyor
        print("\n[2] TF-IDF etiket vektörleri oluşturuluyor...")
        extractor = TagFeatureExtractor()
        feature_matrix = extractor.fit_transform(posts_list)
        
        if hasattr(feature_matrix, "toarray"):
            feature_matrix_dense = feature_matrix.toarray()
        else:
            feature_matrix_dense = feature_matrix
            
        print(f"TF-IDF vektör matris boyutu: {feature_matrix.shape}")
        print(f"Toplam {len(extractor.feature_names)} benzersiz etiket bulundu")
        
        # En sık kullanılan etiketleri göster
        tag_usage = {}
        for post in posts_list:
            for tag in post.get("tags", []):
                tag_usage[tag] = tag_usage.get(tag, 0) + 1
                
        top_tags = sorted(tag_usage.items(), key=lambda x: x[1], reverse=True)[:15]
        print("\n[3] En sık kullanılan 15 etiket:")
        for tag, count in top_tags:
            print(f"  - {tag}: {count} gönderi")
        
        # Etiket vektörlerini göster
        print("\n[4] İlk 5 gönderinin etiket vektörleri:")
        print("\nGönderi ID | Başlık | Etiketler | Vektör Gösterimi")
        print("-" * 80)
        
        for i in range(min(5, len(posts_list))):
            post = posts_list[i]
            # Sıfır olmayan değerleri bul
            if hasattr(feature_matrix, "toarray"):
                dense_vector = feature_matrix[i].toarray()[0]
            else:
                dense_vector = feature_matrix[i]
                
            nonzero_indices = np.nonzero(dense_vector)[0]
            nonzero_features = {extractor.feature_names[idx]: round(float(dense_vector[idx]), 3) 
                               for idx in nonzero_indices}
            
            print(f"{post['id']} | {post.get('title', 'Başlık yok')[:30]} | {post.get('tags', [])} | {nonzero_features}")
        
        # Öneri modelini oluştur
        print("\n[5] Öneri modeli oluşturuluyor...")
        recommender = ContentBasedRecommender()
        recommender.fit(posts_list)
        
        # Benzerlik matrisini hesapla
        print("\n[6] Benzerlik matrisi hesaplanıyor...")
        similarity_matrix = cosine_similarity(feature_matrix_dense)
        
        print(f"Benzerlik matris boyutu: {similarity_matrix.shape}")
        print("\nBenzerlik matrisi (ilk 5x5):")
        print(pd.DataFrame(
            similarity_matrix[:5, :5],
            index=[f"Post {posts_list[i]['id']}" for i in range(5)],
            columns=[f"Post {posts_list[i]['id']}" for i in range(5)]
        ).round(3))
        
        # En benzer gönderi çiftlerini bul
        print("\n[7] En benzer gönderi çiftleri:")
        
        similar_pairs = []
        for i in range(len(posts_list)):
            for j in range(i+1, len(posts_list)):
                if similarity_matrix[i, j] > 0:  # Sadece benzerliği sıfırdan büyük olanlar
                    similar_pairs.append((
                        posts_list[i]['id'], 
                        posts_list[j]['id'],
                        posts_list[i].get('title', 'Başlık yok'),
                        posts_list[j].get('title', 'Başlık yok'),
                        similarity_matrix[i, j]
                    ))
        
        # Benzerliğe göre sırala
        similar_pairs.sort(key=lambda x: x[4], reverse=True)
        
        # En benzer 5 çifti göster
        for i, (id1, id2, title1, title2, sim) in enumerate(similar_pairs[:5]):
            print(f"{i+1}. ID:{id1} '{title1[:20]}...' - ID:{id2} '{title2[:20]}...' = {sim:.3f}")
            
        # Kullanıcı bazlı öneri örneği
        print("\n[8] Kullanıcı 1 için etiket profili oluşturuluyor...")
        
        # Kullanıcının etiket etkileşimlerini çek
        interactions_query = """
            SELECT tag, interaction_count 
            FROM User_Tag_Interactions 
            WHERE user_id = 1
        """
        interactions = await database.fetch_all(interactions_query)
        user_interactions = [dict(row) for row in interactions]
        
        # Kullanıcı etiket profilini oluştur
        user_tags = {}
        for interaction in user_interactions:
            tag = interaction["tag"]
            count = interaction["interaction_count"]
            user_tags[tag] = user_tags.get(tag, 0) + count
            
        # Etiketleri ağırlıklarına göre sırala
        sorted_tags = sorted(user_tags.items(), key=lambda x: x[1], reverse=True)
        
        print(f"Kullanıcı 1 için {len(sorted_tags)} etkileşimli etiket bulundu:")
        for tag, weight in sorted_tags[:10]:  # En yüksek 10 etiket
            print(f"  - {tag}: {weight} etkileşim")
            
        # Kullanıcının etiket vektörünü oluştur
        user_post = {"tags": list(user_tags.keys())}
        user_vector = extractor.transform([user_post])
        
        if hasattr(user_vector, "toarray"):
            user_vector_dense = user_vector.toarray()[0]
        else:
            user_vector_dense = user_vector[0]
        
        nonzero_indices = np.nonzero(user_vector_dense)[0]
        user_tfidf = {extractor.feature_names[idx]: round(float(user_vector_dense[idx]), 3) 
                      for idx in nonzero_indices}
        
        print("\nKullanıcı 1 için TF-IDF vektörü:")
        print(user_tfidf)
        
        # Kullanıcıyla gönderi benzerliklerini hesapla ve en benzerleri göster
        user_similarities = cosine_similarity(user_vector, feature_matrix).flatten()
        top_indices = user_similarities.argsort()[::-1][:5]
        
        print("\n[9] Kullanıcı için en benzer 5 gönderi:")
        for i, idx in enumerate(top_indices):
            post = posts_list[idx]
            print(f"{i+1}. Gönderi ID: {post['id']}, Başlık: {post.get('title', 'Başlık yok')[:30]}")
            print(f"   Benzerlik: {user_similarities[idx]:.4f}")
            print(f"   Etiketler: {post.get('tags', [])}")

    except Exception as e:
        print(f"Hata oluştu: {e}")
    finally:
        # Bağlantıyı kapat
        await database.disconnect()
        print("\nVeritabanı bağlantısı kapatıldı.")

if __name__ == "__main__":
    asyncio.run(visualize_model()) 