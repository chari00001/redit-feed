import numpy as np
import json
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
from app.features import TagFeatureExtractor
from app.content_analyzer import SmartContentAnalyzer
from app.db import database
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.cluster import MiniBatchKMeans

class EnhancedRecommender:
    def __init__(self):
        self.posts = []
        self.post_ids = []
        self.tag_extractor = TagFeatureExtractor()
        self.content_analyzer = SmartContentAnalyzer()
        self.feature_matrix = None
        self.user_interactions = {}
        self.user_profiles = {}
        self.post_analysis = {}
        self.vectorizer = None
        
    async def load_user_profiles_from_db(self, user_id: Optional[int] = None):
        """
        user_tag_interactions tablosundan kullanıcı profillerini yükler
        """
        print("👤 Kullanıcı profilleri veritabanından yükleniyor...")
        
        query = "SELECT * FROM user_tag_interactions"
        if user_id:
            query += f" WHERE user_id = {user_id}"
            
        interactions = await database.fetch_all(query)
        
        self.user_profiles = {}
        
        for interaction in interactions:
            uid = interaction['user_id']
            if uid not in self.user_profiles:
                self.user_profiles[uid] = {
                    'tag_preferences': defaultdict(float),
                    'interaction_summary': defaultdict(int),
                    'total_interactions': 0
                }
            
            tag = interaction['tag']
            interaction_type = interaction['interaction_type']
            count = interaction['interaction_count']
            
            # Etkileşim türüne göre ağırlık
            weight_map = {'view': 1.0, 'like': 3.0, 'comment': 4.0, 'share': 5.0}
            score = count * weight_map.get(interaction_type, 1.0)
            
            self.user_profiles[uid]['tag_preferences'][tag] += score
            self.user_profiles[uid]['interaction_summary'][interaction_type] += count
            self.user_profiles[uid]['total_interactions'] += count
            
        print(f"✅ {len(self.user_profiles)} kullanıcının profili yüklendi.")

    async def fit(self, posts: List[Dict[str, Any]], use_content_analysis: bool = True):
        """
        Gelişmiş makine öğrenmesi ile öneri modelini eğitir
        """
        self.posts = posts
        self.post_ids = [post["id"] for post in posts]
        
        print(f"🚀 {len(posts)} post için gelişmiş öneri sistemi eğitiliyor...")
        
        if use_content_analysis and len(posts) > 3:
            # İçerik analizi yap
            analysis_results = self.content_analyzer.analyze_posts(posts)
            self.post_analysis = analysis_results['post_analysis']
            
            # Enhanced tags ile yeni post listesi oluştur
            enhanced_posts = []
            for post in posts:
                enhanced_post = post.copy()
                post_analysis = self.post_analysis.get(post['id'], {})
                enhanced_post['tags'] = post_analysis.get('enhanced_tags', post.get('tags', []))
                enhanced_posts.append(enhanced_post)
            
            # Enhanced tags ile feature matrix oluştur
            self.feature_matrix = self.tag_extractor.fit_transform(enhanced_posts)
        else:
            # Sadece mevcut etiketlerle
            self.feature_matrix = self.tag_extractor.fit_transform(posts)
        
        self.vectorizer = self.tag_extractor.vectorizer
        
        # Tüm kullanıcı profillerini yükle
        await self.load_user_profiles_from_db()
        
        print(f"✅ Öneri sistemi eğitildi. {self.feature_matrix.shape[1]} özellik oluşturuldu.")
    
    def update_user_interactions(self, user_id: int, post_id: int, interaction_type: str, weight: float = 1.0):
        """
        Kullanıcı etkileşimini günceller ve kullanıcı profilini yeniden hesaplar
        """
        if user_id not in self.user_interactions:
            self.user_interactions[user_id] = []
        
        # Etkileşimi kaydet
        interaction = {
            'post_id': post_id,
            'interaction_type': interaction_type,
            'weight': weight,
            'timestamp': np.datetime64('now')
        }
        self.user_interactions[user_id].append(interaction)
        
        # Kullanıcı profilini güncelle
        self._update_user_profile(user_id)
    
    def _update_user_profile(self, user_id: int):
        """
        Kullanıcının etkileşimlerinden ilgi profilini oluşturur
        """
        if user_id not in self.user_interactions:
            return
        
        tag_weights = defaultdict(float)
        cluster_weights = defaultdict(float)
        total_weight = 0
        
        # Etkileşim ağırlıkları
        interaction_weights = {
            'view': 1.0,
            'like': 3.0,
            'comment': 4.0,
            'share': 5.0
        }
        
        for interaction in self.user_interactions[user_id]:
            post_id = interaction['post_id']
            interaction_type = interaction['interaction_type']
            base_weight = interaction_weights.get(interaction_type, 1.0)
            
            # Bu postun etiketlerini bul
            post_data = next((p for p in self.posts if p['id'] == post_id), None)
            if not post_data:
                continue
            
            # Enhanced tags kullan
            if post_id in self.post_analysis:
                tags = self.post_analysis[post_id].get('enhanced_tags', [])
                cluster_id = self.post_analysis[post_id].get('cluster_id', -1)
            else:
                tags = post_data.get('tags', [])
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except:
                        tags = []
                cluster_id = -1
            
            # Etiket ağırlıklarını güncelle
            for tag in tags:
                tag_weights[tag] += base_weight
                total_weight += base_weight
            
            # Küme ağırlıklarını güncelle
            if cluster_id != -1:
                cluster_weights[cluster_id] += base_weight
        
        # Normalize et
        if total_weight > 0:
            for tag in tag_weights:
                tag_weights[tag] /= total_weight
            for cluster in cluster_weights:
                cluster_weights[cluster] /= total_weight
        
        # Kullanıcı profilini kaydet
        self.user_profiles[user_id] = {
            'tag_preferences': dict(tag_weights),
            'cluster_preferences': dict(cluster_weights),
            'total_interactions': len(self.user_interactions[user_id]),
            'last_updated': np.datetime64('now')
        }
    
    async def recommend_for_user(self, user_id: int, top_n: int = 10,
                               exclude_seen: bool = True) -> List[Dict[str, Any]]:
        """
        Kullanıcıya kişiselleştirilmiş öneriler sunar
        """
        # Eğer kullanıcı profili hafızada yoksa, o kullanıcıyı anlık olarak yükle
        if user_id not in self.user_profiles:
            print(f"👤 Kullanıcı {user_id} profili hafızada değil. Veritabanından yükleniyor...")
            await self.load_user_profiles_from_db(user_id=user_id)

        if user_id not in self.user_profiles:
            # Veritabanından da bulunamadıysa yeni kullanıcıdır
            print(f"⚠️ Kullanıcı {user_id} için profil bulunamadı. Popüler gönderiler öneriliyor.")
            return self._get_diversified_popular_posts(top_n)
        
        user_profile = self.user_profiles[user_id]
        tag_preferences = user_profile['tag_preferences']
        
        # Kullanıcının daha önce etkileşimde bulunduğu postları bul
        seen_posts = set()
        if exclude_seen and user_id in self.user_interactions:
            seen_posts = {interaction['post_id'] for interaction in self.user_interactions[user_id]}
        
        # Her post için gelişmiş benzerlik skoru hesapla
        post_scores = []
        
        for i, post in enumerate(self.posts):
            post_id = post['id']
            
            # Daha önce görülen postları atla
            if post_id in seen_posts:
                continue
            
            # 1. KİŞİSELLEŞTİRME SKORU (Etiket ve Küme Bazlı)
            personalization_score = 0.0
            
            # A. Etiket uyumu
            tag_match_score = 0.0
            matched_tags = 0
            unknown_tags = 0
            
            if post_id in self.post_analysis:
                post_tags = self.post_analysis[post_id].get('enhanced_tags', [])
            else:
                post_tags = post.get('tags', [])
                if isinstance(post_tags, str):
                    try:
                        post_tags = json.loads(post_tags)
                    except:
                        post_tags = []
            
            for tag in post_tags:
                if tag in tag_preferences:
                    tag_match_score += tag_preferences[tag]
                    matched_tags += 1
                else:
                    unknown_tags += 1
            
            # Eşleşen etiketlerin ortalama ağırlığı
            if matched_tags > 0:
                personalization_score += (tag_match_score / matched_tags) * 2.0 # Etiket uyumunu 2x ağırlıklandır
            
            # Bilinmeyen etiketler için küçük bir ceza
            personalization_score -= (unknown_tags / len(post_tags)) * 0.1
            
            # B. Küme uyumu (cluster_preferences kaldırıldığı için bu kısım basitleştirildi)
            cluster_id = self.post_analysis.get(post_id, {}).get('cluster_id', -1)
            
            # 2. ÇEŞİTLİLİK BONUSU
            diversity_bonus = 0.0
            
            # Kullanıcının az etkileşimde bulunduğu kümeleri tercih et
            if cluster_id != -1:
                user_cluster_interactions = sum(1 for interaction in self.user_interactions.get(user_id, [])
                                               if self.post_analysis.get(interaction['post_id'], {}).get('cluster_id') == cluster_id)
                
                # Az etkileşimde bulunulan kümelere bonus ver
                if user_cluster_interactions < 2:
                    diversity_bonus += 0.3
                elif user_cluster_interactions < 5:
                    diversity_bonus += 0.1
            
            # 3. ETKİLEŞİM TÜRÜ BONUSU
            interaction_preference_bonus = 0.0
            
            # En yaygın etkileşim türünü bul
            if user_profile['interaction_summary']:
                most_common_interaction = max(user_profile['interaction_summary'], key=user_profile['interaction_summary'].get)
                
                # Bu post türü kullanıcının tercih ettiği etkileşim türüne uygun mu?
                content = post.get('content', '') or ''
                if 'comment' in most_common_interaction and len(content) > 100:
                    interaction_preference_bonus += 0.2
                elif 'like' in most_common_interaction and post.get('likes_count', 0) > 5:
                    interaction_preference_bonus += 0.15
                elif 'share' in most_common_interaction and len(post_tags) > 2:
                    interaction_preference_bonus += 0.1
            
            # 4. ZAMAN BAZLI BONUS (Yeni içeriklere hafif öncelik)
            time_bonus = 0.0
            if hasattr(post, 'created_at') and post.get('created_at'):
                # Yeni postlara küçük bonus ver
                time_bonus = 0.05
            
            # 5. POPÜLERLIK SKORU (Azaltılmış etki)
            popularity_score = 0.0
            if any([post.get('likes_count', 0), post.get('comments_count', 0), 
                   post.get('shares_count', 0), post.get('views_count', 0)]):
                popularity_score = (
                    post.get('likes_count', 0) * 0.2 +
                    post.get('comments_count', 0) * 0.3 +
                    post.get('shares_count', 0) * 0.4 +
                    post.get('views_count', 0) * 0.1
                ) / 50.0  # Daha düşük normalize
            
            # 6. RASTGELE ÇEŞİTLİLİK FAKTÖRÜ
            import random
            randomness_factor = random.uniform(-0.05, 0.05)  # Küçük rastgelelik
            
            # TOPLAM SKOR HESAPLAMA
            final_score = (
                personalization_score * 0.70 +      # Ana kişiselleştirme skoru
                diversity_bonus * 0.15 +             # Çeşitlilik bonusu  
                interaction_preference_bonus * 0.10 + # Etkileşim tercihi
                time_bonus * 0.03 +                  # Zaman bonusu
                popularity_score * 0.02 +            # Popülerlik (çok düşük)
                randomness_factor                    # Rastgelelik
            )
            
            post_scores.append((post_id, final_score, post))
        
        # Skora göre sırala
        post_scores.sort(key=lambda x: x[1], reverse=True)
        
        # ÇEŞİTLİLİK FİLTRELEMESİ - Aynı kümeden çok fazla öneri verme
        recommendations = []
        cluster_counts = {}
        max_per_cluster = max(2, top_n // 3)  # Her kümeden maksimum sayısı
        
        for post_id, score, post_data in post_scores:
            if len(recommendations) >= top_n:
                break
                
            # Bu postun kümesini kontrol et
            cluster_id = self.post_analysis.get(post_id, {}).get('cluster_id', -1)
            
            # Küme limiti kontrolü
            if cluster_id != -1:
                if cluster_counts.get(cluster_id, 0) >= max_per_cluster:
                    continue  # Bu kümeden yeterince öneri var
                cluster_counts[cluster_id] = cluster_counts.get(cluster_id, 0) + 1
            
            post_copy = post_data.copy()
            post_copy['recommendation_score'] = float(score)
            post_copy['recommendation_reason'] = self._generate_recommendation_reason(user_id, post_data, score)
            recommendations.append(post_copy)
        
        # Eğer yeterli öneri yoksa, kalan yerleri en iyi skorlarla doldur
        if len(recommendations) < top_n:
            remaining_posts = [item for item in post_scores if item[0] not in [r['id'] for r in recommendations]]
            for post_id, score, post_data in remaining_posts[:top_n - len(recommendations)]:
                post_copy = post_data.copy()
                post_copy['recommendation_score'] = float(score)
                post_copy['recommendation_reason'] = "Genel öneri"
                recommendations.append(post_copy)
        
        # Buna rağmen hala öneri yoksa, popülerleri ekle
        if not recommendations:
            print(f"ℹ️ Kişiselleştirilmiş öneri bulunamadı, popüler gönderilerle destekleniyor.")
            return self._get_diversified_popular_posts(top_n)
            
        return recommendations
    
    def _generate_recommendation_reason(self, user_id: int, post_data: Dict, score: float) -> str:
        """
        Öneri nedenini açıklar
        """
        if user_id not in self.user_profiles:
            return "Popüler içerik"
        
        user_profile = self.user_profiles[user_id]
        post_id = post_data['id']
        
        # Post etiketlerini al
        if post_id in self.post_analysis:
            post_tags = self.post_analysis[post_id].get('enhanced_tags', [])
        else:
            post_tags = post_data.get('tags', [])
            if isinstance(post_tags, str):
                try:
                    post_tags = json.loads(post_tags)
                except:
                    post_tags = []
        
        # Kullanıcının ilgilendiği etiketlerle eşleşenleri bul
        matching_tags = []
        if post_tags:
            for tag in post_tags:
                if tag in user_profile['tag_preferences']:
                    matching_tags.append(tag)
        
        if matching_tags:
            # En yüksek skorlu eşleşen etiketi bul
            best_match = max(matching_tags, key=lambda t: user_profile['tag_preferences'].get(t, 0))
            return f"'{best_match}' ilgi alanınıza uygun"
        elif score > 0.5:
            return "Yüksek puanlı içerik"
        elif len(post_tags) > 0:
            return f"'{post_tags[0]}' konusunda"
        else:
            return "Sizin için seçildi"
    
    def _get_diversified_popular_posts(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Çeşitlendirilmiş popüler postları döndürür (yeni kullanıcılar için)
        """
        # Popülerlik skoruna göre sırala
        posts_with_scores = []
        for post in self.posts:
            popularity_score = (
                post.get('likes_count', 0) * 0.3 +
                post.get('comments_count', 0) * 0.5 +
                post.get('shares_count', 0) * 0.7 +
                post.get('views_count', 0) * 0.1
            )
            
            # Rastgele çeşitlilik ekle
            import random
            diversity_factor = random.uniform(0.8, 1.2)
            final_score = popularity_score * diversity_factor
            
            posts_with_scores.append((final_score, post))
        
        posts_with_scores.sort(key=lambda x: x[0], reverse=True)
        
        # Çeşitlilik filtresi - farklı kümelerden seç
        popular_posts = []
        used_clusters = set()
        max_per_cluster = max(2, top_n // 4)
        cluster_counts = {}
        
        for score, post in posts_with_scores:
            if len(popular_posts) >= top_n:
                break
                
            # Küme kontrolü
            cluster_id = self.post_analysis.get(post['id'], {}).get('cluster_id', -1)
            
            if cluster_id != -1:
                if cluster_counts.get(cluster_id, 0) >= max_per_cluster:
                    continue
                cluster_counts[cluster_id] = cluster_counts.get(cluster_id, 0) + 1
            
            post_copy = post.copy()
            post_copy['recommendation_score'] = float(score)
            post_copy['recommendation_reason'] = "Popüler içerik"
            popular_posts.append(post_copy)
        
        # Eğer yeterli değilse geri kalanları ekle
        if len(popular_posts) < top_n:
            remaining = [item for item in posts_with_scores if item[1]['id'] not in [p['id'] for p in popular_posts]]
            for score, post in remaining[:top_n - len(popular_posts)]:
                post_copy = post.copy()
                post_copy['recommendation_score'] = float(score)
                post_copy['recommendation_reason'] = "Popüler içerik"
                popular_posts.append(post_copy)
        
        return popular_posts
    
    def _get_popular_posts(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Popüler postları döndürür (yeni kullanıcılar için)
        """
        # Popülerlik skoruna göre sırala
        posts_with_scores = []
        for post in self.posts:
            popularity_score = (
                post.get('likes_count', 0) * 0.3 +
                post.get('comments_count', 0) * 0.5 +
                post.get('shares_count', 0) * 0.7 +
                post.get('views_count', 0) * 0.1
            )
            posts_with_scores.append((popularity_score, post))
        
        posts_with_scores.sort(key=lambda x: x[0], reverse=True)
        
        popular_posts = []
        for score, post in posts_with_scores[:top_n]:
            post_copy = post.copy()
            post_copy['recommendation_score'] = float(score)
            popular_posts.append(post_copy)
        
        return popular_posts
    
    def get_similar_posts(self, post_id: int, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Belirli bir posta benzer postları bulur
        """
        if post_id not in self.post_ids:
            return []
        
        # İçerik analizi varsa küme bazlı benzerlik
        if post_id in self.post_analysis:
            return self.content_analyzer.get_similar_posts(post_id, top_n)
        
        # Yoksa TF-IDF benzerliği
        idx = self.post_ids.index(post_id)
        post_vector = self.feature_matrix[idx]
        similarities = cosine_similarity(post_vector, self.feature_matrix).flatten()
        
        # Kendisi hariç en benzer postları bul
        similar_indices = np.argsort(similarities)[::-1]
        similar_indices = [i for i in similar_indices if i != idx][:top_n]
        
        similar_posts = []
        for i in similar_indices:
            post = self.posts[i].copy()
            post["similarity_score"] = float(similarities[i])
            similar_posts.append(post)
        
        return similar_posts
    
    async def get_user_interest_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Kullanıcının ilgi profiline ilişkin bir özet döndürür.
        Veriyi doğrudan user_tag_interactions tablosundan alır.
        """
        
        # Kullanıcı profilini veritabanından anlık olarak yükle
        await self.load_user_profiles_from_db(user_id=user_id)
        
        if user_id not in self.user_profiles:
            return {
                "user_id": user_id,
                "status": "new_user",
                "message": "Henüz yeterli etkileşim verisi yok"
            }
        
        profile = self.user_profiles[user_id]
        
        # En çok tercih edilen etiketleri sırala
        top_tags = sorted(profile['tag_preferences'].items(), 
                              key=lambda item: item[1], 
                              reverse=True)
        
        # Profil gücünü hesapla
        total_score = sum(profile['tag_preferences'].values())
        profile_strength = min(1.0, total_score / 100.0) # 100 skoru max güç olarak kabul et
        
        return {
            "user_id": user_id,
            "status": "profile_found",
            "total_interactions": profile.get('total_interactions', 0),
            "profile_strength": profile_strength,
            "interaction_summary": profile.get('interaction_summary', {}),
            "top_interests": [
                {"tag": tag, "weight": round(weight, 3)} for tag, weight in top_tags[:15]
            ]
        }
    
    def get_topic_posts(self, cluster_id: int, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Belirli bir konudaki postları döndürür
        """
        return self.content_analyzer.get_posts_by_topic(cluster_id, top_n)
    
    def get_topics_summary(self) -> Dict[str, Any]:
        """
        Tüm konuların özetini döndürür
        """
        if not hasattr(self.content_analyzer, 'cluster_keywords'):
            return {'topics': [], 'message': 'İçerik analizi henüz yapılmadı'}
        
        topics = []
        for cluster_id, keywords in self.content_analyzer.cluster_keywords.items():
            # Bu konudaki post sayısını hesapla
            post_count = sum(1 for analysis in self.post_analysis.values() 
                           if analysis.get('cluster_id') == cluster_id)
            
            topics.append({
                'topic_id': cluster_id,
                'keywords': keywords[:8],
                'post_count': post_count
            })
        
        # Post sayısına göre sırala
        topics.sort(key=lambda x: x['post_count'], reverse=True)
        
        return {
            'topics': topics,
            'total_topics': len(topics),
            'total_posts_analyzed': len(self.post_analysis)
        }
    
    def save_models(self, filepath: str = "models/"):
        """
        Tüm modelleri kaydet
        """
        # İçerik analizörünü kaydet
        self.content_analyzer.save_models(filepath)
        
        # Tag extractor'ı kaydet
        import joblib
        import os
        os.makedirs(filepath, exist_ok=True)
        
        if self.tag_extractor.vectorizer:
            joblib.dump(self.tag_extractor, f"{filepath}/tag_extractor.pkl")
        
        # Kullanıcı profillerini kaydet
        user_data = {
            'user_interactions': self.user_interactions,
            'user_profiles': self.user_profiles,
            'post_analysis': self.post_analysis
        }
        joblib.dump(user_data, f"{filepath}/user_data.pkl")
        
        print(f"✅ Tüm modeller {filepath} klasörüne kaydedildi.")
    
    def load_models(self, filepath: str = "models/"):
        """
        Kaydedilmiş modelleri yükle
        """
        import joblib
        import os
        
        try:
            # İçerik analizörünü yükle
            self.content_analyzer.load_models(filepath)
            
            # Tag extractor'ı yükle
            if os.path.exists(f"{filepath}/tag_extractor.pkl"):
                self.tag_extractor = joblib.load(f"{filepath}/tag_extractor.pkl")
            
            # Kullanıcı verilerini yükle
            if os.path.exists(f"{filepath}/user_data.pkl"):
                user_data = joblib.load(f"{filepath}/user_data.pkl")
                self.user_interactions = user_data.get('user_interactions', {})
                self.user_profiles = user_data.get('user_profiles', {})
                self.post_analysis = user_data.get('post_analysis', {})
            
            print(f"✅ Tüm modeller {filepath} klasöründen yüklendi.")
            return True
        except Exception as e:
            print(f"❌ Model yükleme hatası: {e}")
            return False 