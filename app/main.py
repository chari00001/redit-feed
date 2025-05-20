import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import database
from app.routes import router

# API uygulama örneği oluştur
app = FastAPI(
    title="Redit Feed Recommendation Service",
    description="Kullanıcılara kişiselleştirilmiş içerik önerileri sunan bir API",
    version="0.1.0"
)

# CORS ayarları (cross-origin talepleri için)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tüm kaynaklara izin ver (üretim için sınırlandırılmalı)
    allow_credentials=True,
    allow_methods=["*"],  # Tüm HTTP metotlarına izin ver
    allow_headers=["*"],  # Tüm başlıklara izin ver
)

# API route'larını ekle
app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 