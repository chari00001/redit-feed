#!/usr/bin/env python3
import asyncio
import json
import sys
from collections import Counter, defaultdict
from app.db import database
from app.enhanced_recommender import EnhancedRecommender

async def analyze_post_tags():
    """
    Postların etiketlerini kapsamlı şekilde analiz eder
    """
    try:
        print("🏷️  POST ETİKET ANALİZİ")
        print("=" * 60)
        
        # Veritabanına bağlan
        await database.connect()
        print("✅ Veritabanı bağlantısı kuruldu")
        
        # Tüm postları çek
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
        
        print(f"📊 Toplam {len(posts_list)} post analiz ediliyor")
        
        # 1. TEMEL ETİKET İSTATİSTİKLERİ
        print("\n1️⃣ TEMEL ETİKET İSTATİSTİKLERİ")
        print("-" * 40)
        
        all_tags = []
        posts_with_tags = 0
        empty_tag_posts = 0
        
        for post in posts_list:
            tags = post.get('tags', [])
            if tags:
                all_tags.extend(tags)
                posts_with_tags += 1
            else:
                empty_tag_posts += 1
        
        tag_counter = Counter(all_tags)
        unique_tags = len(tag_counter)
        
        print(f"📈 Toplam etiket sayısı: {len(all_tags)}")
        print(f"🔢 Benzersiz etiket sayısı: {unique_tags}")
        print(f"📝 Etiketli post sayısı: {posts_with_tags}")
        print(f"📝 Etiketsiz post sayısı: {empty_tag_posts}")
        print(f"📊 Ortalama etiket/post: {len(all_tags)/len(posts_list):.2f}")
        
        # 2. EN POPÜLER ETİKETLER
        print("\n2️⃣ EN POPÜLER ETİKETLER (TOP 20)")
        print("-" * 40)
        
        top_tags = tag_counter.most_common(20)
        for i, (tag, count) in enumerate(top_tags, 1):
            percentage = (count / len(all_tags)) * 100
            print(f"{i:2d}. {tag:<20} : {count:3d} kez ({percentage:.1f}%)")
        
        # 3. GELİŞMİŞ ETİKET ANALİZİ (AI ile)
        print("\n3️⃣ GELİŞMİŞ ETİKET ANALİZİ (AI ile)")
        print("-" * 40)
        
        recommender = EnhancedRecommender()
        await recommender.fit(posts_list, use_content_analysis=True)
        
        # Enhanced tagları topla
        enhanced_tags = []
        enhanced_posts = 0
        
        for post_id, analysis in recommender.post_analysis.items():
            tags = analysis.get('enhanced_tags', [])
            if tags:
                enhanced_tags.extend(tags)
                enhanced_posts += 1
        
        enhanced_counter = Counter(enhanced_tags)
        
        print(f"🤖 AI ile analiz edilen post: {enhanced_posts}")
        print(f"🤖 AI tarafından üretilen etiket: {len(enhanced_tags)}")
        print(f"🤖 Benzersiz AI etiket: {len(enhanced_counter)}")
        
        print("\n🤖 En popüler AI etiketleri:")
        for i, (tag, count) in enumerate(enhanced_counter.most_common(15), 1):
            percentage = (count / len(enhanced_tags)) * 100 if enhanced_tags else 0
            print(f"{i:2d}. {tag:<25} : {count:3d} kez ({percentage:.1f}%)")
        
        # 4. ETİKET KATEGORİLERİ ANALİZİ
        print("\n4️⃣ ETİKET KATEGORİLERİ ANALİZİ")
        print("-" * 40)
        
        # Etiketleri kategorilere ayır
        categories = {
            'teknoloji': ['technology', 'tech', 'ai', 'machine', 'learning', 'programming', 'code', 'software', 'computer', 'digital', 'cyber', 'data', 'algorithm'],
            'bilim': ['science', 'research', 'physics', 'chemistry', 'biology', 'space', 'astronomy', 'quantum', 'scientific', 'experiment'],
            'sanat': ['art', 'design', 'creative', 'music', 'painting', 'drawing', 'photography', 'artist', 'aesthetic', 'culture'],
            'spor': ['sport', 'football', 'basketball', 'fitness', 'exercise', 'health', 'training', 'game', 'match', 'athlete'],
            'oyun': ['game', 'gaming', 'video', 'play', 'indie', 'mobile', 'console', 'esports', 'gamer'],
            'iş': ['business', 'work', 'career', 'job', 'startup', 'company', 'finance', 'money', 'investment', 'market'],
            'eğitim': ['education', 'learn', 'study', 'course', 'tutorial', 'school', 'university', 'knowledge', 'teaching'],
            'yaşam': ['life', 'lifestyle', 'food', 'travel', 'home', 'family', 'relationship', 'personal', 'social']
        }
        
        category_counts = defaultdict(int)
        categorized_tags = defaultdict(list)
        
        # Tüm etiketleri kategorilere ayır
        all_unique_tags = list(tag_counter.keys()) + list(enhanced_counter.keys())
        
        for tag in set(all_unique_tags):
            tag_lower = tag.lower()
            found_category = False
            
            for category, keywords in categories.items():
                if any(keyword in tag_lower for keyword in keywords):
                    category_counts[category] += tag_counter.get(tag, 0) + enhanced_counter.get(tag, 0)
                    categorized_tags[category].append(tag)
                    found_category = True
                    break
            
            if not found_category:
                category_counts['diğer'] += tag_counter.get(tag, 0) + enhanced_counter.get(tag, 0)
                categorized_tags['diğer'].append(tag)
        
        print("📊 Kategori bazında etiket dağılımı:")
        sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        
        for category, count in sorted_categories:
            percentage = (count / (len(all_tags) + len(enhanced_tags))) * 100 if (all_tags or enhanced_tags) else 0
            tag_count = len(categorized_tags[category])
            print(f"🏷️  {category.title():<12}: {count:4d} etiket ({percentage:.1f}%) - {tag_count} çeşit")
        
        # 5. KONU BAZLI ANALİZ
        print("\n5️⃣ KONU BAZLI ANALİZ")
        print("-" * 40)
        
        topics_summary = recommender.get_topics_summary()
        
        print(f"🎯 Toplam {len(topics_summary['topics'])} konu tespit edildi")
        print("\nEn popüler konular:")
        
        for i, topic in enumerate(topics_summary['topics'][:10], 1):
            post_count = len(topic.get('post_ids', []))
            keywords = topic.get('keywords', [])[:5]
            print(f"{i:2d}. Konu {topic['topic_id']:2d}: {', '.join(keywords)}")
            print(f"    📊 {post_count} post")
        
        # 6. ETİKET TREND ANALİZİ
        print("\n6️⃣ ETİKET TREND ANALİZİ (Son 30 Günlük)")
        print("-" * 40)
        
        # Son 30 günlük postları al
        recent_query = """
            SELECT * FROM posts 
            WHERE created_at >= NOW() - INTERVAL '30 days'
            ORDER BY created_at DESC
        """
        recent_posts = await database.fetch_all(recent_query)
        recent_posts_list = [dict(row) for row in recent_posts]
        
        # Etiketleri düzenle
        for post in recent_posts_list:
            if isinstance(post.get("tags"), str):
                try:
                    post["tags"] = json.loads(post["tags"])
                except:
                    post["tags"] = []
        
        recent_tags = []
        for post in recent_posts_list:
            recent_tags.extend(post.get('tags', []))
        
        recent_counter = Counter(recent_tags)
        
        print(f"📅 Son 30 günde {len(recent_posts_list)} post")
        print(f"📈 Son 30 günde {len(recent_tags)} etiket kullanımı")
        print(f"🔥 Son 30 günde {len(recent_counter)} farklı etiket")
        
        print("\n🔥 Son 30 günün trend etiketleri:")
        for i, (tag, count) in enumerate(recent_counter.most_common(10), 1):
            total_usage = tag_counter.get(tag, 0)
            trend_ratio = (count / total_usage * 100) if total_usage > 0 else 0
            print(f"{i:2d}. {tag:<20} : {count:2d} kez (toplam: {total_usage}, trend: {trend_ratio:.1f}%)")
        
        # 7. POST BAZINDA DETAYLI ANALİZ
        print("\n7️⃣ POST BAZINDA DETAYLI ANALİZ")
        print("-" * 40)
        
        print("📊 Etiket sayısına göre post dağılımı:")
        tag_count_distribution = defaultdict(int)
        
        for post in posts_list:
            tag_count = len(post.get('tags', []))
            tag_count_distribution[tag_count] += 1
        
        for tag_count in sorted(tag_count_distribution.keys()):
            post_count = tag_count_distribution[tag_count]
            percentage = (post_count / len(posts_list)) * 100
            print(f"   {tag_count:2d} etiket: {post_count:3d} post ({percentage:.1f}%)")
        
        # En çok etiketli postları göster
        print("\n🏆 En çok etiketli postlar:")
        posts_by_tag_count = sorted(posts_list, key=lambda x: len(x.get('tags', [])), reverse=True)
        
        for i, post in enumerate(posts_by_tag_count[:5], 1):
            tag_count = len(post.get('tags', []))
            title = post.get('title', 'Başlık yok')[:50]
            tags = ', '.join(post.get('tags', [])[:5])
            print(f"{i}. {title}... ({tag_count} etiket)")
            print(f"   🏷️  {tags}{'...' if len(post.get('tags', [])) > 5 else ''}")
        
        # 8. ÖNERİ: ETİKET İYİLEŞTİRME
        print("\n8️⃣ ETİKET İYİLEŞTİRME ÖNERİLERİ")
        print("-" * 40)
        
        improvement_suggestions = []
        
        if empty_tag_posts > len(posts_list) * 0.1:
            improvement_suggestions.append(f"⚠️  {empty_tag_posts} post etiketsiz (%{empty_tag_posts/len(posts_list)*100:.1f}). Otomatik etiketleme önerilir.")
        
        if len(all_tags) / len(posts_list) < 2:
            improvement_suggestions.append("⚠️  Post başına ortalama etiket sayısı düşük. Daha zengin etiketleme önerilir.")
        
        # Çok az kullanılan etiketler
        rare_tags = [tag for tag, count in tag_counter.items() if count == 1]
        if len(rare_tags) > unique_tags * 0.3:
            improvement_suggestions.append(f"⚠️  {len(rare_tags)} etiket sadece 1 kez kullanılmış. Etiket standardizasyonu önerilir.")
        
        # Benzer etiketler
        similar_tags = []
        tag_list = list(tag_counter.keys())
        for i, tag1 in enumerate(tag_list):
            for tag2 in tag_list[i+1:]:
                if tag1.lower() in tag2.lower() or tag2.lower() in tag1.lower():
                    if abs(len(tag1) - len(tag2)) <= 3:
                        similar_tags.append((tag1, tag2))
        
        if similar_tags:
            improvement_suggestions.append(f"⚠️  {len(similar_tags)} benzer etiket çifti bulundu. Birleştirme önerilir.")
        
        if improvement_suggestions:
            for suggestion in improvement_suggestions:
                print(suggestion)
        else:
            print("✅ Etiket kalitesi iyi görünüyor!")
        
        print("\n🎉 ETİKET ANALİZİ TAMAMLANDI!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await database.disconnect()
        print("✅ Veritabanı bağlantısı kapatıldı")

def main():
    """
    Ana fonksiyon
    """
    print("🚀 Post Etiket Analizi Başlıyor...")
    asyncio.run(analyze_post_tags())

if __name__ == "__main__":
    main() 