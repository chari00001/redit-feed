# Redit Feed Recommendation System v2.0

## 🚀 Gelişmiş Makine Öğrenmesi Tabanlı Öneri Sistemi

Bu proje, kullanıcıların etkileşimde bulunduğu gönderilerin içeriklerini analiz ederek, makine öğrenmesi yöntemleriyle kişiselleştirilmiş içerik önerileri sunan gelişmiş bir sistemdir.

## ✨ Özellikler

### 🧠 Akıllı İçerik Analizi
- **TF-IDF Vektörleştirme**: Post başlık ve içeriklerinden anahtar kelime çıkarma
- **K-Means Kümeleme**: Benzer içerikleri otomatik gruplandırma
- **Çok Dilli Destek**: Türkçe ve İngilizce içerik analizi
- **Otomatik Etiket Genişletme**: Manuel etiketleri içerik analiziyle zenginleştirme

### 👤 Kişiselleştirilmiş Öneriler
- **Kullanıcı Profil Analizi**: Etkileşim geçmişinden ilgi alanları çıkarma
- **Ağırlıklı Etkileşimler**: Like (3x), Yorum (4x), Paylaşım (5x), Görüntüleme (1x)
- **Hibrit Öneri Algoritması**: İçerik + İşbirlikçi filtreleme
- **Gerçek Zamanlı Güncelleme**: Anında profil güncelleme

### 🔄 Otomatik Sistem Yönetimi
- **3 Saatlik Analiz**: Yeni postları otomatik analiz etme
- **Günlük Model Eğitimi**: Her gece saat 02:00'da model güncelleme
- **Model Persistence**: Eğitilmiş modelleri kaydetme/yükleme
- **Performans İzleme**: Sistem sağlık kontrolü

## 📊 Sistem Mimarisi

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Post Content  │───▶│  Content Analyzer │───▶│  Enhanced Tags  │
│ (Title + Desc)  │    │   (TF-IDF + KMeans)│    │   + Clusters    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ User Interactions│───▶│ Profile Builder  │◄───┤  Recommendation │
│ (Like,Comment..) │    │                  │    │     Engine      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🛠 Kurulum

### 1. Depoyu Klonlayın
```bash
git clone <repo-url>
cd redit-feed
```

### 2. Sanal Ortam Oluşturun
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate     # Windows
```

### 3. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 4. Çevre Değişkenlerini Ayarlayın
```bash
cp .env.example .env
# .env dosyasını düzenleyin ve veritabanı bilgilerinizi girin
```

### 5. Veritabanını Oluşturun
```bash
# PostgreSQL'de veritabanını oluşturun
psql -U postgres -f db.sql
```

### 6. Sistemi Başlatın
```bash
uvicorn app.main:app --reload
```

## 🔗 API Endpoint'leri

### 📊 Öneriler
```http
GET /api/v1/recommendations?user_id=1&limit=10
```
Kullanıcıya kişiselleştirilmiş içerik önerileri döndürür.

### 👤 Kullanıcı Profili
```http
GET /api/v1/user-profile/1
```
Kullanıcının ilgi alanları ve etkileşim profilini gösterir.

### 🎯 Konular
```http
GET /api/v1/topics
```
Sistem tarafından bulunan tüm konuları listeler.

```http
GET /api/v1/topic-posts/2?limit=10
```
Belirli bir konudaki postları döndürür.

### 📝 Post Analizi
```http
GET /api/v1/post-analysis/123
```
Belirli bir postun detaylı analizini gösterir.

### 🔗 Benzer Postlar
```http
GET /api/v1/similar-posts/123?limit=5
```
Belirli bir posta benzer içerikleri bulur.

### 📱 Etkileşim Takibi
```http
POST /api/v1/track-interaction
Content-Type: application/json

{
  "user_id": 1,
  "post_id": 123,
  "interaction_type": "like"
}
```

### 🔄 Sistem Yönetimi
```http
POST /api/v1/analyze-new-posts
```
Son 3 saatteki yeni postları analiz eder.

```http
POST /api/v1/retrain-model
```
Modeli tüm verilerle yeniden eğitir.

## 🧪 Test Etme

### Sistem Testini Çalıştırın
```bash
python test_enhanced_system.py
```

### API Testleri
```bash
# Sistem durumu
curl http://localhost:8000/health

# Kullanıcı önerileri
curl "http://localhost:8000/api/v1/recommendations?user_id=1"

# Konular
curl http://localhost:8000/api/v1/topics
```

## 📈 Performans Özellikleri

- **Analiz Hızı**: ~0.1 saniye/post
- **Öneri Süresi**: <5 saniye (100+ post için)
- **Bellek Kullanımı**: ~50MB (1000 post için)
- **Ölçeklenebilirlik**: 10,000+ post destekler

## 🔧 Yapılandırma

### Küme Sayısı Ayarlama
Sistem otomatik olarak post sayısına göre küme sayısını belirler:
- <10 post: 3 küme
- 10-50 post: 5 küme  
- 50-200 post: 8 küme
- 200+ post: 12 küme

### Etkileşim Ağırlıkları
```python
interaction_weights = {
    'view': 1.0,
    'like': 3.0,
    'comment': 4.0,
    'share': 5.0
}
```

### Scheduler Ayarları
```python
# Her 3 saatte bir yeni post analizi
schedule.every(3).hours.do(analyze_new_posts)

# Her gün saat 02:00'da model eğitimi  
schedule.every().day.at("02:00").do(retrain_model)
```

## 📁 Proje Yapısı

```
redit-feed/
├── app/
│   ├── content_analyzer.py      # İçerik analiz motoru
│   ├── enhanced_recommender.py  # Gelişmiş öneri sistemi
│   ├── features.py             # TF-IDF özellik çıkarma
│   ├── routes.py               # API endpoint'leri
│   ├── scheduler.py            # Otomatik görevler
│   ├── models.py               # Veri modelleri
│   ├── db.py                   # Veritabanı bağlantısı
│   └── main.py                 # Ana uygulama
├── models/                     # Kaydedilmiş ML modelleri
├── test_enhanced_system.py     # Sistem testleri
├── requirements.txt            # Python bağımlılıkları
├── db.sql                      # Veritabanı şeması
└── README.md                   # Bu dosya
```

## 🚀 Üretim Ortamına Alma

### Docker ile Çalıştırma
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Nginx Konfigürasyonu
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 🆘 Destek

Sorunlar için GitHub Issues kullanın veya [email] ile iletişime geçin.

---

**v2.0.0** - Gelişmiş makine öğrenmesi tabanlı öneri sistemi
**v1.0.0** - Temel TF-IDF tabanlı sistem 


final_score = 0.70·personalization + 0.15·diversity + 0.10·interaction + 0.03·time + 0.02·popularity + randomness

a) Personalization_score (≈ %70)
  • Post etiketleri kullanıcı tag_preferences içinde geçiyorsa ortalama ağırlıkları × 2.
  • Bilinmeyen etiket sayısına küçük ceza.
b) Diversity_bonus (≈ %15)
  • Postun kümesi, kullanıcının az etkileşimde bulunduğu kümelerden ise +0.3 / +0.1.
c) Interaction_preference_bonus (≈ %10)
  • Kullanıcının en sık yaptığı etkileşim türü (like / comment / share) ile postun yapısı uyuşuyorsa +0.1-0.2.
d) Time_bonus (≈ %3)
  • Yeni oluşturulmuş postlara +0.05.
e) Popularity_score (≈ %2)
  • likes, comments, shares, views metriklerinin zayıf normalize kombinasyonu.
f) Randomness_factor (±0.05)
  • Küçük rastgelelik eklenerek sıralamanın tekdüze olması engellenir.
