import re
import json
import numpy as np
from typing import List, Dict, Any, Set, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter, defaultdict
import joblib
import os
from datetime import datetime

class SmartContentAnalyzer:
    def __init__(self):
        self.vectorizer = None
        self.kmeans_model = None
        self.feature_matrix = None
        self.post_clusters = {}
        self.cluster_keywords = {}
        self.post_keywords = {}
        self.posts_data = []
        
        # Türkçe ve İngilizce stop words
        self.stop_words = {
            # Türkçe
            'bir', 'bu', 've', 'ile', 'için', 'olan', 'olarak', 'de', 'da', 
            'ki', 'mi', 'mu', 'mı', 'mü', 'ne', 'ya', 'yada', 'veya', 'ama',
            'çok', 'daha', 'en', 'şu', 'o', 'ben', 'sen', 'biz', 'siz', 'onlar',
            'her', 'hiç', 'bazı', 'tüm', 'bütün', 'kendi', 'gibi', 'kadar', 'sonra',
            # İngilizce
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
    
    def clean_text(self, text: str) -> str:
        """Türkçe ve İngilizce metinleri temizler"""
        if not text:
            return ""
        
        text = text.lower()
        # URL'leri kaldır
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        # Mention ve hashtag'leri temizle
        text = re.sub(r'[@#]\w+', '', text)
        # Türkçe ve İngilizce karakterler dışındakileri kaldır
        text = re.sub(r'[^\w\sçğıöşüÇĞIİÖŞÜ]', ' ', text)
        # Fazla boşlukları temizle
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_content_keywords(self, posts: List[Dict[str, Any]], 
                               max_features: int = 1000) -> Dict[int, List[str]]:
        """
        Her post için title + content'ten anahtar kelime çıkarır
        """
        print(f"📝 {len(posts)} post için içerik analizi başlıyor...")
        
        documents = []
        post_ids = []
        self.posts_data = posts
        
        for post in posts:
            # Title + content birleştir (title'a 3x ağırlık)
            title = post.get('title', '') or ''
            content = post.get('content', '') or ''
            
            # Title'ı 3 kez tekrarla (daha önemli)
            combined_text = f"{title} {title} {title} {content}"
            cleaned_text = self.clean_text(combined_text)
            
            documents.append(cleaned_text)
            post_ids.append(post['id'])
        
        # TF-IDF ile vektörleştir
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words=list(self.stop_words),
            min_df=2,  # En az 2 dokümanda geçmeli
            max_df=0.8,  # %80'den fazla dokümanda geçmemeli
            ngram_range=(1, 2),  # 1-2 kelimelik gruplar
            sublinear_tf=True,
            token_pattern=r'\b[a-zA-ZçğıöşüÇĞIİÖŞÜ]{2,}\b'  # Türkçe karakterler dahil
        )
        
        self.feature_matrix = self.vectorizer.fit_transform(documents)
        feature_names = self.vectorizer.get_feature_names_out()
        
        # Her post için en önemli kelimeleri çıkar
        post_keywords = {}
        for i, post_id in enumerate(post_ids):
            scores = self.feature_matrix[i].toarray()[0]
            # En yüksek 10 kelimeyi al
            top_indices = scores.argsort()[-10:][::-1]
            keywords = [feature_names[idx] for idx in top_indices if scores[idx] > 0]
            post_keywords[post_id] = keywords
        
        self.post_keywords = post_keywords
        print(f"✅ İçerik analizi tamamlandı. {len(feature_names)} benzersiz kelime bulundu.")
        return post_keywords
    
    def cluster_posts(self, n_clusters: int = None) -> Dict[int, int]:
        """
        Postları benzer içeriklere göre kümeler
        """
        if self.feature_matrix is None:
            raise ValueError("Önce extract_content_keywords çağırın!")
        
        # Otomatik küme sayısı belirleme
        if n_clusters is None:
            n_posts = len(self.posts_data)
            if n_posts < 10:
                n_clusters = 3
            elif n_posts < 50:
                n_clusters = 5
            elif n_posts < 200:
                n_clusters = 8
            else:
                n_clusters = 12
        
        print(f"🎯 {n_clusters} kümeye ayırma işlemi başlıyor...")
        
        # K-Means kümeleme
        self.kmeans_model = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10,
            max_iter=100
        )
        
        cluster_labels = self.kmeans_model.fit_predict(self.feature_matrix)
        
        # Post ID'leri ile küme etiketlerini eşleştir
        post_ids = [post['id'] for post in self.posts_data]
        for i, post_id in enumerate(post_ids):
            self.post_clusters[post_id] = int(cluster_labels[i])
        
        # Her küme için anahtar kelimeleri çıkar
        self._extract_cluster_keywords()
        
        print(f"✅ Kümeleme tamamlandı. {len(set(cluster_labels))} küme oluşturuldu.")
        return self.post_clusters
    
    def _extract_cluster_keywords(self):
        """Her küme için karakteristik anahtar kelimeleri bulur"""
        feature_names = self.vectorizer.get_feature_names_out()
        
        for cluster_id in set(self.post_clusters.values()):
            # Bu kümedeki postları bul
            cluster_post_indices = [
                i for i, post_id in enumerate([post['id'] for post in self.posts_data])
                if self.post_clusters.get(post_id) == cluster_id
            ]
            
            if not cluster_post_indices:
                continue
            
            # Bu kümedeki postların TF-IDF skorlarını topla
            cluster_tfidf = self.feature_matrix[cluster_post_indices].sum(axis=0).A1
            
            # En yüksek skorlu 15 kelimeyi al
            top_indices = cluster_tfidf.argsort()[-15:][::-1]
            cluster_keywords = [feature_names[i] for i in top_indices if cluster_tfidf[i] > 0]
            
            self.cluster_keywords[cluster_id] = cluster_keywords
    
    def analyze_posts(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ana analiz fonksiyonu - tüm postları analiz eder
        """
        print(f"🚀 {len(posts)} post için tam analiz başlıyor...")
        
        # 1. İçerik anahtar kelimeleri
        content_keywords = self.extract_content_keywords(posts)
        
        # 2. Kümeleme
        post_clusters = self.cluster_posts()
        
        # 3. Her post için birleşik sonuç
        results = {}
        for post in posts:
            post_id = post['id']
            
            # Mevcut manuel etiketler
            existing_tags = post.get('tags', []) or []
            if isinstance(existing_tags, str):
                try:
                    existing_tags = json.loads(existing_tags)
                except:
                    existing_tags = []
            
            # İçerik anahtar kelimeleri
            content_keys = content_keywords.get(post_id, [])
            
            # Küme anahtar kelimeleri
            cluster_id = post_clusters.get(post_id, -1)
            cluster_keys = self.cluster_keywords.get(cluster_id, [])[:5]  # En önemli 5'i
            
            # Hepsini birleştir (tekrarları kaldır, sırayı koru)
            all_keywords = existing_tags.copy()
            for keyword in content_keys + cluster_keys:
                if keyword not in all_keywords:
                    all_keywords.append(keyword)
            
            results[post_id] = {
                'post_id': post_id,
                'title': post.get('title', ''),
                'content_preview': (post.get('content', '') or '')[:150] + '...',
                'original_tags': existing_tags,
                'content_keywords': content_keys,
                'cluster_id': cluster_id,
                'cluster_keywords': cluster_keys,
                'enhanced_tags': all_keywords,
                'analysis_timestamp': datetime.now().isoformat()
            }
        
        summary = {
            'post_analysis': results,
            'cluster_summary': self.cluster_keywords,
            'total_posts': len(posts),
            'total_clusters': len(self.cluster_keywords),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ Analiz tamamlandı! {len(results)} post analiz edildi.")
        return summary
    
    def get_similar_posts(self, post_id: int, top_n: int = 5) -> List[Dict[str, Any]]:
        """Belirli bir posta benzer postları bulur"""
        if post_id not in self.post_clusters:
            return []
        
        # Aynı kümedeki postları bul
        target_cluster = self.post_clusters[post_id]
        similar_post_ids = [
            pid for pid, cluster in self.post_clusters.items() 
            if cluster == target_cluster and pid != post_id
        ]
        
        # Post verilerini döndür
        similar_posts = []
        for pid in similar_post_ids[:top_n]:
            post_data = next((p for p in self.posts_data if p['id'] == pid), None)
            if post_data:
                similar_posts.append(post_data)
        
        return similar_posts
    
    def get_posts_by_topic(self, cluster_id: int, top_n: int = 10) -> List[Dict[str, Any]]:
        """Belirli bir konudaki postları döndürür"""
        topic_post_ids = [
            pid for pid, cluster in self.post_clusters.items() 
            if cluster == cluster_id
        ]
        
        topic_posts = []
        for pid in topic_post_ids[:top_n]:
            post_data = next((p for p in self.posts_data if p['id'] == pid), None)
            if post_data:
                topic_posts.append(post_data)
        
        return topic_posts
    
    def save_models(self, filepath: str = "models/"):
        """Eğitilmiş modelleri kaydet"""
        os.makedirs(filepath, exist_ok=True)
        
        if self.vectorizer:
            joblib.dump(self.vectorizer, f"{filepath}/content_vectorizer.pkl")
        if self.kmeans_model:
            joblib.dump(self.kmeans_model, f"{filepath}/content_kmeans.pkl")
        
        # Analiz sonuçlarını kaydet
        analysis_data = {
            'post_clusters': self.post_clusters,
            'cluster_keywords': self.cluster_keywords,
            'post_keywords': self.post_keywords
        }
        joblib.dump(analysis_data, f"{filepath}/analysis_results.pkl")
        
        print(f"✅ Modeller {filepath} klasörüne kaydedildi.")
    
    def load_models(self, filepath: str = "models/"):
        """Kaydedilmiş modelleri yükle"""
        try:
            if os.path.exists(f"{filepath}/content_vectorizer.pkl"):
                self.vectorizer = joblib.load(f"{filepath}/content_vectorizer.pkl")
            if os.path.exists(f"{filepath}/content_kmeans.pkl"):
                self.kmeans_model = joblib.load(f"{filepath}/content_kmeans.pkl")
            if os.path.exists(f"{filepath}/analysis_results.pkl"):
                analysis_data = joblib.load(f"{filepath}/analysis_results.pkl")
                self.post_clusters = analysis_data.get('post_clusters', {})
                self.cluster_keywords = analysis_data.get('cluster_keywords', {})
                self.post_keywords = analysis_data.get('post_keywords', {})
            
            print(f"✅ Modeller {filepath} klasöründen yüklendi.")
            return True
        except Exception as e:
            print(f"❌ Model yükleme hatası: {e}")
            return False 