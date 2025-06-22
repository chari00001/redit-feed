import asyncio
import schedule
import time
from datetime import datetime
from app.db import database
import threading

class RecommendationScheduler:
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
    
    async def analyze_new_posts_job(self):
        """
        3 saatte bir yeni postları analiz eden görev
        """
        try:
            print(f"🔄 {datetime.now()}: Yeni post analizi başlıyor...")
            
            # Veritabanına bağlan
            await database.connect()
            
            # Son 3 saatteki postları analiz et
            # Bu fonksiyon routes.py'den import edilecek
            print(f"✅ Yeni post analizi tamamlandı")
            
        except Exception as e:
            print(f"❌ Yeni post analizi hatası: {e}")
        finally:
            await database.disconnect()
    
    async def daily_model_training_job(self):
        """
        Günlük model eğitimi görevi
        """
        try:
            print(f"🚀 {datetime.now()}: Günlük model eğitimi başlıyor...")
            
            # Veritabanına bağlan
            await database.connect()
            
            # Model eğitimi burada yapılacak
            print(f"✅ Günlük model eğitimi tamamlandı")
            
        except Exception as e:
            print(f"❌ Günlük model eğitimi hatası: {e}")
        finally:
            await database.disconnect()
    
    def run_async_job(self, coro):
        """
        Async fonksiyonları sync scheduler'da çalıştırmak için
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro)
        finally:
            loop.close()
    
    def setup_schedule(self):
        """
        Zamanlanmış görevleri ayarla
        """
        # Her 3 saatte bir yeni post analizi
        schedule.every(3).hours.do(
            lambda: self.run_async_job(self.analyze_new_posts_job())
        )
        
        # Her gün saat 02:00'da model eğitimi
        schedule.every().day.at("02:00").do(
            lambda: self.run_async_job(self.daily_model_training_job())
        )
        
        print("📅 Zamanlanmış görevler ayarlandı:")
        print("   - Yeni post analizi: Her 3 saatte bir")
        print("   - Model eğitimi: Her gün saat 02:00")
    
    def run_scheduler(self):
        """
        Scheduler'ı çalıştır
        """
        self.setup_schedule()
        self.running = True
        
        print("🕐 Scheduler başlatıldı...")
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Her dakika kontrol et
    
    def start(self):
        """
        Scheduler'ı ayrı thread'de başlat
        """
        if not self.running:
            self.scheduler_thread = threading.Thread(target=self.run_scheduler)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()
            print("✅ Scheduler thread'i başlatıldı")
    
    def stop(self):
        """
        Scheduler'ı durdur
        """
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        print("🛑 Scheduler durduruldu")

# Global scheduler instance
recommendation_scheduler = RecommendationScheduler() 