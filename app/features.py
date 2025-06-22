import json
import numpy as np
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer

class TagFeatureExtractor:
    def __init__(self):
        """
        Etiket vektörleştirme işlemi için sınıf - Sadece TF-IDF kullanır
        """
        self.vectorizer = None
        self.all_tags = []
        self.tag_indices = {}
        self.feature_names = []
        
    def _prepare_tag_documents(self, posts: List[Dict[str, Any]]) -> List[str]:
        """
        Her gönderinin etiketlerini boşlukla ayrılmış bir metne dönüştürür.
        TF-IDF Vectorizer'ın beklediği format budur.
        """
        tag_documents = []
        
        for post in posts:
            # Etiketleri JSON'dan çıkart
            tags = []
            if isinstance(post.get("tags"), list):
                tags = post["tags"]
            elif isinstance(post.get("tags"), str):
                try:
                    tags = json.loads(post["tags"])
                except:
                    tags = []
            
            # Boşlukla ayrılmış metne dönüştür
            tag_document = " ".join(tags) if tags else ""
            tag_documents.append(tag_document)
            
            # Tüm benzersiz etiketleri topla
            self.all_tags.extend(tags)
            
        self.all_tags = sorted(list(set(self.all_tags)))
        self.tag_indices = {tag: i for i, tag in enumerate(self.all_tags)}
        
        return tag_documents
    
    def fit_transform(self, posts: List[Dict[str, Any]]) -> np.ndarray:
        """
        Gönderilerdeki etiketleri TF-IDF vektörleştirir ve model eğitir
        
        Args:
            posts: Etiket içeren gönderiler listesi
            
        Returns:
            Vektörleştirilmiş etiket matrisi
        """
        tag_documents = self._prepare_tag_documents(posts)
        
        # TF-IDF vektörleştirir
        self.vectorizer = TfidfVectorizer(min_df=1)
        X = self.vectorizer.fit_transform(tag_documents)
        self.feature_names = self.vectorizer.get_feature_names_out()
        
        return X
    
    def transform(self, posts: List[Dict[str, Any]]) -> np.ndarray:
        """
        Yeni gönderileri önceden eğitilmiş TF-IDF modeliyle vektörleştirir
        """
        if not self.vectorizer:
            raise ValueError("Önce fit_transform metodunu çağırmalısınız!")
            
        tag_documents = []
        for post in posts:
            tags = []
            if isinstance(post.get("tags"), list):
                tags = post["tags"]
            elif isinstance(post.get("tags"), str):
                try:
                    tags = json.loads(post["tags"])
                except:
                    tags = []
            
            tag_document = " ".join(tags) if tags else ""
            tag_documents.append(tag_document)
        
        return self.vectorizer.transform(tag_documents) 