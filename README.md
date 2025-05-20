# Redit Feed Recommendation Microservice

## Kurulum

1. Depoyu klonlayın ve dizine girin:
   ```bash
   git clone <repo-url>
   cd redit-feed
   ```

2. Sanal ortam oluşturun ve bağımlılıkları yükleyin:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. `.env` dosyanızı oluşturun:
   ```bash
   cp .env.example .env
   # .env dosyasını düzenleyin ve veritabanı bilgilerinizi girin
   ```

4. Veritabanı tablolarını oluşturun (örnek SQL):
   ```sql
   CREATE TABLE posts (
       id SERIAL PRIMARY KEY,
       user_id INTEGER NOT NULL,
       content TEXT NOT NULL,
       created_at TIMESTAMP DEFAULT NOW()
   );

   CREATE TABLE user_tag_interactions (
       id SERIAL PRIMARY KEY,
       user_id INTEGER NOT NULL,
       tag VARCHAR(100) NOT NULL,
       interaction_type VARCHAR(50) NOT NULL,
       created_at TIMESTAMP DEFAULT NOW()
   );
   ```

5. Servisi başlatın:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Uç Noktaları

- `POST /interact`: Kullanıcı etkileşimi kaydeder.
- `GET /feed?user_id=...`: Kullanıcıya önerilen gönderileri döner.

---

Geliştirmeye hazır! ML tabanlı öneri mantığı eklemek için `routes.py` ve `models.py` dosyalarını genişletebilirsiniz. 