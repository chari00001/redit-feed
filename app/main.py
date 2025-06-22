import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import database
from app.routes import router, load_recommender_data
from app.scheduler import recommendation_scheduler

# API uygulama örneği oluştur
app = FastAPI(
    title="Redit Feed Recommendation Service",
    description="Gelişmiş makine öğrenmesi ile kullanıcılara kişiselleştirilmiş içerik önerileri sunan API",
    version="2.0.0"
)

# CORS ayarları (cross-origin talepleri için)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],  # localhost:3000 ve tüm kaynaklara izin ver (üretim için sınırlandırılmalı)
    allow_credentials=True,
    allow_methods=["*"],  # Tüm HTTP metotlarına izin ver
    allow_headers=["*"],  # Tüm başlıklara izin ver
)

# API route'larını ekle
app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    """
    Uygulama başlatıldığında çalışacak görevler
    """
    print("🚀 Redit Feed Recommendation Service başlatılıyor...")
    
    # Veritabanı bağlantısı
    await database.connect()
    print("✅ Veritabanı bağlantısı kuruldu")
    
    # Öneri modelini yükle ve eğit
    try:
        await load_recommender_data()
        print("✅ Öneri modeli başlatıldı ve eğitildi")
    except Exception as e:
        print(f"⚠️ Öneri modeli başlatma hatası: {e}")
        print("📝 İlk çalıştırma olabilir, model ilk API çağrısında yüklenecek")
    
    # Scheduler'ı başlat
    recommendation_scheduler.start()
    print("✅ Otomatik görev scheduler'ı başlatıldı")
    
    print("🎉 Sistem hazır! API endpoint'leri:")
    print("   📊 GET  /api/v1/recommendations?user_id=X - Kişiselleştirilmiş öneriler")
    print("   👤 GET  /api/v1/user-profile/{user_id} - Kullanıcı ilgi profili")
    print("   🎯 GET  /api/v1/topics - Tüm konular")
    print("   📝 GET  /api/v1/post-analysis/{post_id} - Post analizi")
    print("   🔗 GET  /api/v1/similar-posts/{post_id} - Benzer postlar")
    print("   📱 POST /api/v1/track-interaction - Etkileşim kaydetme")
    print("   🔄 POST /api/v1/analyze-new-posts - Yeni post analizi")
    print("   🎓 POST /api/v1/retrain-model - Model yeniden eğitimi")

@app.on_event("shutdown")
async def shutdown():
    """
    Uygulama kapatıldığında çalışacak görevler
    """
    print("🛑 Sistem kapatılıyor...")
    
    # Scheduler'ı durdur
    recommendation_scheduler.stop()
    print("✅ Scheduler durduruldu")
    
    # Veritabanı bağlantısını kapat
    await database.disconnect()
    print("✅ Veritabanı bağlantısı kapatıldı")
    
    print("👋 Sistem güvenli şekilde kapatıldı")

@app.get("/")
async def root():
    """
    Ana sayfa - sistem durumu
    """
    return {
        "service": "Redit Feed Recommendation Service",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Akıllı içerik analizi",
            "Kişiselleştirilmiş öneriler", 
            "Kullanıcı profil analizi",
            "Konu bazlı gruplandırma",
            "Otomatik model eğitimi"
        ],
        "endpoints": {
            "recommendations": "/api/v1/recommendations?user_id=X",
            "user_profile": "/api/v1/user-profile/{user_id}",
            "topics": "/api/v1/topics",
            "post_analysis": "/api/v1/post-analysis/{post_id}",
            "similar_posts": "/api/v1/similar-posts/{post_id}"
        }
    }

@app.get("/health")
async def health_check():
    """
    Sistem sağlık kontrolü
    """
    try:
        # Veritabanı bağlantısını test et
        await database.fetch_one("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "scheduler": "running" if recommendation_scheduler.running else "stopped",
        "timestamp": "2024-01-01T00:00:00Z"  # Gerçek timestamp eklenebilir
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 