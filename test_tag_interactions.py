#!/usr/bin/env python3
import asyncio
from app.db import database

async def test_tag_interactions():
    try:
        # Veritabanına bağlan
        print("Veritabanına bağlanılıyor...")
        await database.connect()
        print("Veritabanı bağlantısı başarılı!")

        # User_Tag_Interactions tablosundaki tüm verileri çek
        query = "SELECT * FROM User_Tag_Interactions LIMIT 20"
        results = await database.fetch_all(query)
        
        # Sonuçları yazdır
        print("\nKullanıcı-Etiket Etkileşimleri:")
        if not results:
            print("User_Tag_Interactions tablosunda hiç veri bulunamadı!")
        else:
            print(f"Toplam {len(results)} kayıt bulundu.")
            for row in results:
                print(f"ID: {row['id']}, User ID: {row['user_id']}, Tag: {row['tag']}, " \
                      f"Interaction: {row['interaction_type']}, Count: {row['interaction_count']}, " \
                      f"Last Interaction: {row['last_interacted_at']}")

    except Exception as e:
        print(f"Hata oluştu: {e}")
    finally:
        # Bağlantıyı kapat
        await database.disconnect()
        print("\nVeritabanı bağlantısı kapatıldı.")

if __name__ == "__main__":
    asyncio.run(test_tag_interactions()) 