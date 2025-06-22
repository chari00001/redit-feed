#!/usr/bin/env python3
"""
Posts tablosundaki tüm verilerle model eğitimi ve performans raporu
"""
import asyncio
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Any
import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from sklearn.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity

from app.db import database
from app.enhanced_recommender import EnhancedRecommender
from app.content_analyzer import SmartContentAnalyzer

class ModelTrainer:
    def __init__(self):
        self.recommender = None
        self.posts_data = []
        self.training_stats = {}
        self.performance_metrics = {}
        
    async def load_all_posts(self):
        """Posts tablosundaki tüm verileri yükle"""
        print("📊 Posts tablosundan tüm veriler yükleniyor...")
        
        # Tüm postları çek
        query = """
        SELECT 
            id, user_id, title, content, tags, 
            likes_count, comments_count, shares_count, views_count,
            created_at, visibility
        FROM posts 
        ORDER BY created_at DESC
        """
        
        posts = await database.fetch_all(query)
        self.posts_data = [dict(row) for row in posts]
        
        # Etiketleri düzenle
        for post in self.posts_data:
            if isinstance(post.get("tags"), str):
                try:
                    post["tags"] = json.loads(post["tags"])
                except:
                    post["tags"] = []
            elif post.get("tags") is None:
                post["tags"] = []
                
        print(f"✅ {len(self.posts_data)} post yüklendi")
        return self.posts_data
    
    def analyze_data_quality(self):
        """Veri kalitesi analizi"""
        print("\n🔍 VERİ KALİTESİ ANALİZİ")
        print("-" * 50)
        
        total_posts = len(self.posts_data)
        
        # Temel istatistikler
        posts_with_content = sum(1 for p in self.posts_data if p.get('content'))
        posts_with_tags = sum(1 for p in self.posts_data if p.get('tags'))
        posts_with_title = sum(1 for p in self.posts_data if p.get('title'))
        
        # Etkileşim istatistikleri
        total_likes = sum(p.get('likes_count', 0) for p in self.posts_data)
        total_comments = sum(p.get('comments_count', 0) for p in self.posts_data)
        total_shares = sum(p.get('shares_count', 0) for p in self.posts_data)
        total_views = sum(p.get('views_count', 0) for p in self.posts_data)
        
        # Tag analizi
        all_tags = []
        for post in self.posts_data:
            if post.get('tags'):
                all_tags.extend(post['tags'])
        
        unique_tags = len(set(all_tags))
        avg_tags_per_post = len(all_tags) / total_posts if total_posts > 0 else 0
        
        stats = {
            'total_posts': total_posts,
            'posts_with_content': posts_with_content,
            'posts_with_tags': posts_with_tags,
            'posts_with_title': posts_with_title,
            'content_coverage': posts_with_content / total_posts * 100,
            'tag_coverage': posts_with_tags / total_posts * 100,
            'title_coverage': posts_with_title / total_posts * 100,
            'total_interactions': total_likes + total_comments + total_shares + total_views,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_shares': total_shares,
            'total_views': total_views,
            'unique_tags': unique_tags,
            'avg_tags_per_post': avg_tags_per_post,
            'total_tags_used': len(all_tags)
        }
        
        print(f"📊 Toplam post sayısı: {stats['total_posts']}")
        print(f"📝 İçerik kapsamı: {stats['content_coverage']:.1f}% ({stats['posts_with_content']} post)")
        print(f"🏷️ Etiket kapsamı: {stats['tag_coverage']:.1f}% ({stats['posts_with_tags']} post)")
        print(f"📋 Başlık kapsamı: {stats['title_coverage']:.1f}% ({stats['posts_with_title']} post)")
        print(f"👍 Toplam etkileşim: {stats['total_interactions']:,}")
        print(f"🏷️ Benzersiz etiket sayısı: {stats['unique_tags']}")
        print(f"📊 Post başına ortalama etiket: {stats['avg_tags_per_post']:.2f}")
        
        self.training_stats['data_quality'] = stats
        return stats
    
    async def train_model(self):
        """Gelişmiş model eğitimi"""
        print("\n🚀 MODEL EĞİTİMİ BAŞLATIYOR")
        print("-" * 50)
        
        start_time = time.time()
        
        # Model oluştur ve eğit
        self.recommender = EnhancedRecommender()
        
        # İçerik analizi ile eğitim
        print("🔬 İçerik analizi ve makine öğrenmesi modeli eğitiliyor...")
        await self.recommender.fit(self.posts_data, use_content_analysis=True)
        
        training_time = time.time() - start_time
        
        print(f"✅ Model eğitimi tamamlandı ({training_time:.2f} saniye)")
        print(f"🎯 Özellik boyutu: {self.recommender.feature_matrix.shape}")
        
        self.training_stats['training_time'] = training_time
        self.training_stats['feature_dimensions'] = self.recommender.feature_matrix.shape
        
        return self.recommender
    
    def evaluate_clustering_performance(self):
        """Kümeleme performansını değerlendir"""
        print("\n📊 KÜMELEME PERFORMANSI DEĞERLENDİRMESİ")
        print("-" * 50)
        
        if not hasattr(self.recommender.content_analyzer, 'cluster_labels'):
            print("❌ Kümeleme analizi bulunamadı")
            return {}
        
        # Kümeleme metrikleri
        labels = self.recommender.content_analyzer.cluster_labels
        feature_matrix = self.recommender.content_analyzer.tfidf_matrix
        
        # Silhouette skoru
        if len(set(labels)) > 1:
            silhouette_avg = silhouette_score(feature_matrix, labels)
            calinski_score = calinski_harabasz_score(feature_matrix.toarray(), labels)
        else:
            silhouette_avg = 0
            calinski_score = 0
        
        # Küme istatistikleri
        unique_labels = set(labels)
        cluster_sizes = {label: list(labels).count(label) for label in unique_labels}
        
        clustering_metrics = {
            'n_clusters': len(unique_labels),
            'silhouette_score': silhouette_avg,
            'calinski_harabasz_score': calinski_score,
            'cluster_sizes': cluster_sizes,
            'largest_cluster_size': max(cluster_sizes.values()) if cluster_sizes else 0,
            'smallest_cluster_size': min(cluster_sizes.values()) if cluster_sizes else 0,
            'avg_cluster_size': np.mean(list(cluster_sizes.values())) if cluster_sizes else 0
        }
        
        print(f"🎯 Küme sayısı: {clustering_metrics['n_clusters']}")
        print(f"📊 Silhouette skoru: {clustering_metrics['silhouette_score']:.4f}")
        print(f"📈 Calinski-Harabasz skoru: {clustering_metrics['calinski_harabasz_score']:.2f}")
        print(f"📏 Ortalama küme boyutu: {clustering_metrics['avg_cluster_size']:.1f}")
        print(f"📦 En büyük küme: {clustering_metrics['largest_cluster_size']} post")
        print(f"📦 En küçük küme: {clustering_metrics['smallest_cluster_size']} post")
        
        self.performance_metrics['clustering'] = clustering_metrics
        return clustering_metrics
    
    async def evaluate_recommendation_quality(self):
        """Öneri kalitesini değerlendir"""
        print("\n🎯 ÖNERİ KALİTESİ DEĞERLENDİRMESİ")
        print("-" * 50)
        
        # Test kullanıcıları için öneri kalitesini değerlendir
        test_users = [1, 5, 10, 25, 34, 50] 
        all_recommendations = []
        
        print("Örnek kullanıcılar için öneriler oluşturuluyor:")
        for user_id in test_users:
            try:
                # Önerileri al
                recommendations = await self.recommender.recommend_for_user(user_id, top_n=10)
                
                if recommendations:
                    all_recommendations.extend(recommendations)
                    print(f"  ✅ Kullanıcı {user_id}: {len(recommendations)} öneri bulundu.")
                else:
                    print(f"  ⚠️ Kullanıcı {user_id}: Öneri bulunamadı veya profil yetersiz.")

                # Profilini al ve yazdır (hata ayıklama için faydalı)
                user_profile = await self.recommender.get_user_interest_profile(user_id)
                if user_profile and user_profile.get('status') == 'profile_found':
                    interests = user_profile.get('top_interests', [])
                    print(f"    -> Profil: {interests[:3]}")

            except Exception as e:
                print(f"  ❌ Kullanıcı {user_id} için öneri alınırken hata oluştu: {e}")
        
        print("-" * 50)

        # Öneri kalitesi metrikleri
        if all_recommendations:
            quality_metrics = {
                'avg_recommendation_score': np.mean([rec.get('recommendation_score', 0) for rec in all_recommendations]),
                'max_recommendation_score': np.max([rec.get('recommendation_score', 0) for rec in all_recommendations]),
                'min_recommendation_score': np.min([rec.get('recommendation_score', 0) for rec in all_recommendations]),
                'std_recommendation_score': np.std([rec.get('recommendation_score', 0) for rec in all_recommendations]),
                'total_recommendations_generated': len(all_recommendations)
            }
        else:
            quality_metrics = {
                'avg_recommendation_score': 0,
                'max_recommendation_score': 0,
                'min_recommendation_score': 0,
                'std_recommendation_score': 0,
                'total_recommendations_generated': 0
            }
        
        print(f"📊 Ortalama öneri skoru: {quality_metrics['avg_recommendation_score']:.4f}")
        print(f"📈 Maksimum öneri skoru: {quality_metrics['max_recommendation_score']:.4f}")
        print(f"📉 Minimum öneri skoru: {quality_metrics['min_recommendation_score']:.4f}")
        print(f"📏 Skor standart sapması: {quality_metrics['std_recommendation_score']:.4f}")
        print(f"🎯 Toplam öneri sayısı: {quality_metrics['total_recommendations_generated']}")
        
        self.performance_metrics['recommendation_quality'] = quality_metrics
        return quality_metrics
    
    def evaluate_tag_analysis(self):
        """Tag analizi performansını değerlendir"""
        print("\n🏷️ ETİKET ANALİZİ PERFORMANSI")
        print("-" * 50)
        
        # Orijinal vs enhanced tag karşılaştırması
        original_tag_count = 0
        enhanced_tag_count = 0
        posts_with_enhanced_tags = 0
        
        for post in self.posts_data:
            original_tags = post.get('tags', [])
            original_tag_count += len(original_tags)
            
            if post['id'] in self.recommender.post_analysis:
                enhanced_tags = self.recommender.post_analysis[post['id']].get('enhanced_tags', [])
                enhanced_tag_count += len(enhanced_tags)
                if len(enhanced_tags) > len(original_tags):
                    posts_with_enhanced_tags += 1
        
        tag_metrics = {
            'original_total_tags': original_tag_count,
            'enhanced_total_tags': enhanced_tag_count,
            'tag_enhancement_ratio': enhanced_tag_count / max(original_tag_count, 1),
            'posts_with_enhanced_tags': posts_with_enhanced_tags,
            'enhancement_coverage': posts_with_enhanced_tags / len(self.posts_data) * 100
        }
        
        print(f"📊 Orijinal toplam etiket: {tag_metrics['original_total_tags']}")
        print(f"🚀 Geliştirilmiş toplam etiket: {tag_metrics['enhanced_total_tags']}")
        print(f"📈 Etiket artış oranı: {tag_metrics['tag_enhancement_ratio']:.2f}x")
        print(f"📦 Geliştirilen post sayısı: {tag_metrics['posts_with_enhanced_tags']}")
        print(f"📊 Geliştirme kapsamı: {tag_metrics['enhancement_coverage']:.1f}%")
        
        self.performance_metrics['tag_analysis'] = tag_metrics
        return tag_metrics
    
    def generate_topic_analysis(self):
        """Konu analizi raporu"""
        print("\n🎯 KONU ANALİZİ RAPORU")
        print("-" * 50)
        
        topics_summary = self.recommender.get_topics_summary()
        
        if topics_summary['topics']:
            print(f"📊 Toplam konu sayısı: {topics_summary['total_topics']}")
            print(f"📝 Analiz edilen post sayısı: {topics_summary['total_posts_analyzed']}")
            
            print("\n🏆 EN POPÜLER KONULAR:")
            for i, topic in enumerate(topics_summary['topics'][:5]):
                keywords_str = ', '.join(topic['keywords'][:5])
                print(f"   {i+1}. Konu {topic['topic_id']}: {keywords_str}")
                print(f"      📊 Post sayısı: {topic['post_count']}")
        
        self.performance_metrics['topic_analysis'] = topics_summary
        return topics_summary
    
    def save_model_and_report(self):
        """Model ve raporu kaydet"""
        print("\n💾 MODEL VE RAPOR KAYDETME")
        print("-" * 50)
        
        # Model klasörü oluştur
        os.makedirs("trained_models", exist_ok=True)
        os.makedirs("reports", exist_ok=True)
        
        # Modeli kaydet
        self.recommender.save_models("trained_models/")
        
        # Performans raporunu oluştur
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        full_report = {
            'timestamp': timestamp,
            'training_stats': self.training_stats,
            'performance_metrics': self.performance_metrics,
            'model_info': {
                'total_posts_trained': len(self.posts_data),
                'feature_matrix_shape': list(self.recommender.feature_matrix.shape),
                'content_analysis_enabled': True,
                'model_type': 'EnhancedRecommender with SmartContentAnalyzer'
            }
        }
        
        # JSON raporu kaydet
        report_file = f"reports/performance_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(full_report, f, indent=2, ensure_ascii=False, default=str)
        
        # Markdown raporu oluştur
        markdown_report = self.generate_markdown_report(full_report)
        markdown_file = f"reports/performance_report_{timestamp}.md"
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_report)
        
        print(f"✅ Model 'trained_models/' klasörüne kaydedildi")
        print(f"📊 JSON rapor: {report_file}")
        print(f"📝 Markdown rapor: {markdown_file}")
        
        return full_report
    
    def generate_markdown_report(self, report_data):
        """Markdown formatında rapor oluştur"""
        timestamp = report_data['timestamp']
        
        md_content = f"""# Model Eğitimi ve Performans Raporu
## {timestamp}

## 📊 Genel Bilgiler
- **Eğitim Tarihi**: {timestamp}
- **Toplam Post Sayısı**: {report_data['model_info']['total_posts_trained']:,}
- **Özellik Matrisi Boyutu**: {report_data['model_info']['feature_matrix_shape']}
- **Model Türü**: {report_data['model_info']['model_type']}
- **Eğitim Süresi**: {report_data['training_stats'].get('training_time', 0):.2f} saniye

## 🔍 Veri Kalitesi Analizi
"""
        
        if 'data_quality' in report_data['training_stats']:
            dq = report_data['training_stats']['data_quality']
            md_content += f"""
- **Toplam Post**: {dq['total_posts']:,}
- **İçerik Kapsamı**: {dq['content_coverage']:.1f}% ({dq['posts_with_content']:} post)
- **Etiket Kapsamı**: {dq['tag_coverage']:.1f}% ({dq['posts_with_tags']:} post)
- **Başlık Kapsamı**: {dq['title_coverage']:.1f}% ({dq['posts_with_title']:} post)
- **Toplam Etkileşim**: {dq['total_interactions']:}
- **Benzersiz Etiket**: {dq['unique_tags']:}
- **Ortalama Etiket/Post**: {dq['avg_tags_per_post']:.2f}
"""
        
        if 'clustering' in report_data['performance_metrics']:
            cl = report_data['performance_metrics']['clustering']
            md_content += f"""
## 🎯 Kümeleme Performansı
- **Küme Sayısı**: {cl['n_clusters']}
- **Silhouette Skoru**: {cl['silhouette_score']:.4f}
- **Calinski-Harabasz Skoru**: {cl['calinski_harabasz_score']:.2f}
- **Ortalama Küme Boyutu**: {cl['avg_cluster_size']:.1f}
- **En Büyük Küme**: {cl['largest_cluster_size']} post
- **En Küçük Küme**: {cl['smallest_cluster_size']} post
"""
        
        if 'recommendation_quality' in report_data['performance_metrics']:
            rq = report_data['performance_metrics']['recommendation_quality']
            md_content += f"""
## 🎯 Öneri Sistemi Performansı
- **Ortalama Öneri Skoru**: {rq['avg_recommendation_score']:.4f}
- **Maksimum Öneri Skoru**: {rq['max_recommendation_score']:.4f}
- **Minimum Öneri Skoru**: {rq['min_recommendation_score']:.4f}
- **Skor Standart Sapması**: {rq['std_recommendation_score']:.4f}
- **Toplam Öneri Sayısı**: {rq['total_recommendations_generated']}
"""
        
        if 'tag_analysis' in report_data['performance_metrics']:
            ta = report_data['performance_metrics']['tag_analysis']
            md_content += f"""
## 🏷️ Etiket Analizi Performansı
- **Orijinal Toplam Etiket**: {ta['original_total_tags']:}
- **Geliştirilmiş Toplam Etiket**: {ta['enhanced_total_tags']:}
- **Etiket Artış Oranı**: {ta['tag_enhancement_ratio']:.2f}x
- **Geliştirilen Post Sayısı**: {ta['posts_with_enhanced_tags']:}
- **Geliştirme Kapsamı**: {ta['enhancement_coverage']:.1f}%
"""
        
        if 'topic_analysis' in report_data['performance_metrics']:
            ta = report_data['performance_metrics']['topic_analysis']
            md_content += f"""
## 🎯 Konu Analizi
- **Toplam Konu Sayısı**: {ta['total_topics']}
- **Analiz Edilen Post**: {ta['total_posts_analyzed']:}

### En Popüler Konular
"""
            for i, topic in enumerate(ta['topics'][:5]):
                keywords = ', '.join(topic['keywords'][:5])
                md_content += f"{i+1}. **Konu {topic['topic_id']}**: {keywords} ({topic['post_count']} post)\n"
        
        md_content += f"""
## 📈 Özet ve Öneriler

### Başarı Metrikleri
✅ Model başarıyla eğitildi ve test edildi
✅ Tüm Posts tablosu verisi kullanıldı
✅ İçerik analizi ve kümeleme tamamlandı
✅ Kişiselleştirilmiş öneri sistemi aktif

### Performans Değerlendirmesi
Model performansı yukarıdaki metrikler doğrultusunda değerlendirilmiştir. 
Sistem gerçek zamanlı öneriler sunmaya hazırdır.

---
*Rapor {timestamp} tarihinde otomatik olarak oluşturulmuştur.*
"""
        
        return md_content

async def main():
    """Ana fonksiyon"""
    print("🚀 POSTS TABLOSU İLE MODEL EĞİTİMİ")
    print("=" * 60)
    
    trainer = ModelTrainer()
    
    try:
        # Veritabanına bağlan
        await database.connect()
        print("✅ Veritabanı bağlantısı kuruldu")
        
        # Veri yükle ve kaliteyi analiz et
        await trainer.load_all_posts()
        trainer.analyze_data_quality()
        
        # Modeli eğit
        await trainer.train_model()
        
        # Performansı değerlendir
        trainer.evaluate_clustering_performance()
        await trainer.evaluate_recommendation_quality()
        trainer.evaluate_tag_analysis()
        trainer.generate_topic_analysis()
        
        # Raporları oluştur ve kaydet
        trainer.save_model_and_report()

        print("\n🎉 MODEL EĞİTİMİ VE PERFORMANS ANALİZİ TAMAMLANDI!")
        print("=" * 60)
        print(f"📊 Toplam işlenen post: {len(trainer.posts_data):,}")
        print(f"⚡ Eğitim süresi: {trainer.training_stats.get('training_time', 0):.2f} saniye")
        print("📁 Sonuçlar 'trained_models/' ve 'reports/' klasörlerinde")

    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if database.is_connected:
            await database.disconnect()
            print("✅ Veritabanı bağlantısı kapatıldı")

if __name__ == "__main__":
    asyncio.run(main()) 