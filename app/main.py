from fastapi import FastAPI
from app.api.router import api_router
from app.database import engine, Base

app = FastAPI(
    title="🔱 МОНОЛИТ АНАЛИТИКА",
    description="Высоконагруженный ИИ-сервис анализа аудиозаписей",
    version="1.0.0"
)

# Принудительное создание таблиц в асинхронном режиме при инициализации приложения
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(api_router)

@app.get("/")
def read_root():
    return {"status": "ONLINE", "service": "Monolith Analytics API"}