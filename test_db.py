#!/usr/bin/env python3
import asyncio
from app.db import database

async def test_connection():
    try:
        # Veritabanına bağlan
        print("Veritabanına bağlanılıyor...")
        await database.connect()
        print("Veritabanı bağlantısı başarılı!")

        # Posts tablosundaki tüm verileri çek
        query = "SELECT * FROM posts"
        results = await database.fetch_all(query)
        
        # Sonuçları yazdır
        print("\nPosts tablosundaki veriler:")
        if not results:
            print("Posts tablosunda hiç veri bulunamadı!")
        else:
            print(f"Toplam {len(results)} kayıt bulundu.")
            for row in results:
                print(f"ID: {row['id']}, User ID: {row['user_id']}, Content: {row['content']}, Created At: {row['created_at']}")
                
    except Exception as e:
        print(f"Hata oluştu: {e}")
    finally:
        # Bağlantıyı kapat
        await database.disconnect()
        print("\nVeritabanı bağlantısı kapatıldı.")

if __name__ == "__main__":
    asyncio.run(test_connection()) 