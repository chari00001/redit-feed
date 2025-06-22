import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any
from app.features import TagFeatureExtractor

class ContentBasedRecommender:
    def __init__(self):
        self.posts = []
        self.post_ids = []
        self.tag_extractor = TagFeatureExtractor()  # TF-IDF metodu sabit olarak kullanılıyor
        self.feature_matrix = None
        self.user_interactions = {}  # Kullanıcı ID'sine göre etkileşimleri saklayacak sözlük
        
    def fit(self, posts: List[Dict[str, Any]]):
        """
        Etiket vektörleri üzerinden öneri modelini eğitir
        
        Args:
            posts: Etiket içeren gönderiler listesi
        """
        self.posts = posts
        self.post_ids = [post["id"] for post in posts]
        
        # Etiket vektörlerini hesapla
        self.feature_matrix = self.tag_extractor.fit_transform(posts)
        print(f"Öneri modeli {len(posts)} gönderi ve {self.feature_matrix.shape[1]} özellik üzerinde eğitildi.")
    
    def update_user_interactions(self, user_id: int, tag: str, interaction_count: int):
        """
        Kullanıcı etiket etkileşimini günceller ve modeli hemen günceller
        
        Args:
            user_id: Kullanıcı ID'si
            tag: Etkileşimde bulunulan etiket
            interaction_count: Etkileşim sayısı
        """
        # Kullanıcının etkileşimlerini sözlükte sakla
        if user_id not in self.user_interactions:
            self.user_interactions[user_id] = {}
        
        # Etiket etkileşimini güncelle
        if tag in self.user_interactions[user_id]:
            self.user_interactions[user_id][tag] = self.user_interactions[user_id][tag] + interaction_count
        else:
            self.user_interactions[user_id][tag] = interaction_count
        
        print(f"Kullanıcı {user_id} için etiket {tag} etkileşimi güncellendi. Yeni değer: {self.user_interactions[user_id][tag]}")
    
    def load_all_user_interactions(self, interactions_data: List[Dict[str, Any]]):
        """
        Tüm kullanıcı etkileşimlerini yükler
        
        Args:
            interactions_data: Veritabanından alınan etkileşim kayıtları
        """
        # Etkileşimleri temizle ve yeniden yükle
        self.user_interactions = {}
        
        for interaction in interactions_data:
            user_id = interaction["user_id"]
            tag = interaction["tag"]
            count = interaction["interaction_count"]
            
            if user_id not in self.user_interactions:
                self.user_interactions[user_id] = {}
                
            if tag in self.user_interactions[user_id]:
                self.user_interactions[user_id][tag] += count
            else:
                self.user_interactions[user_id][tag] = count
        
        print(f"Toplam {len(self.user_interactions)} kullanıcı için etkileşim verileri yüklendi.")
        
    def recommend_similar_posts(self, post_id: int, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Belirli bir gönderiye benzer içerikleri önerir
        
        Args:
            post_id: Benzerlik aranacak gönderi ID'si
            top_n: Döndürülecek benzer gönderi sayısı
            
        Returns:
            Benzerlik skoruna göre sıralanmış gönderi listesi
        """
        if post_id not in self.post_ids:
            raise ValueError(f"ID {post_id} olan gönderi bulunamadı!")
            
        # Gönderi indeksini bul
        idx = self.post_ids.index(post_id)
        
        # Bu gönderinin özellik vektörünü al
        post_vector = self.feature_matrix[idx]
        
        # Tüm gönderilerle kosinüs benzerliğini hesapla
        similarities = cosine_similarity(post_vector, self.feature_matrix).flatten()
        
        # Kendisini hariç tut ve en benzer N gönderiyi bul
        similar_indices = np.argsort(similarities)[::-1]
        similar_indices = [i for i in similar_indices if i != idx][:top_n]
        
        # Benzer gönderileri ve benzerlik skorlarını döndür
        similar_posts = []
        for i in similar_indices:
            post = self.posts[i].copy()
            post["similarity_score"] = float(similarities[i])
            similar_posts.append(post)
            
        return similar_posts
    
    def recommend_for_user(self, user_id: int, user_interactions: List[Dict[str, Any]] = None, 
                          top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Kullanıcının etkileşimlerine dayalı içerik önerileri yapar
        
        Args:
            user_id: Kullanıcı ID'si
            user_interactions: Kullanıcının etiket etkileşimleri (None ise, iç veritabanından alınır)
            top_n: Döndürülecek öneri sayısı
            
        Returns:
            Benzerlik skoruna göre sıralanmış gönderi önerileri
        """
        # Kullanıcı etkileşimlerinden etiket profili oluştur
        user_tags = {}
        
        # Dışardan verilen etkileşimler veya saklanan etkileşimleri kullan
        if user_interactions is not None:
            for interaction in user_interactions:
                tag = interaction["tag"]
                count = interaction["interaction_count"]
                user_tags[tag] = user_tags.get(tag, 0) + count
        elif user_id in self.user_interactions:
            user_tags = self.user_interactions[user_id]
        
        # Kullanıcı etiketi yoksa rastgele öneriler döndür
        if not user_tags:
            import random
            random_indices = random.sample(range(len(self.posts)), min(top_n, len(self.posts)))
            return [self.posts[i] for i in random_indices]
        
        # Kullanıcı etiket vektörü oluştur - etiketleri birleştir
        user_post = {"tags": list(user_tags.keys())}
        
        # Bu vektörü özellik uzayına dönüştür
        user_vector = self.tag_extractor.transform([user_post])
        
        # Tüm gönderilerle kosinüs benzerliğini hesapla
        similarities = cosine_similarity(user_vector, self.feature_matrix).flatten()
        
        # En benzer N gönderiyi indekslerini al
        similar_indices = np.argsort(similarities)[::-1][:top_n]
        
        # Önerilen gönderileri ve benzerlik skorlarını döndür
        recommendations = []
        for i in similar_indices:
            post = self.posts[i].copy()
            post["similarity_score"] = float(similarities[i])
            recommendations.append(post)
            
        return recommendations 