from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from app.config import settings
from app.models import AnalysisTask
from app.services.whisper_engine import WhisperEngine
from app.services.llm_analyzer import LLMAnalyzer

celery_app = Celery(
    "monolith_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Создаем синхронный движок чисто для Celery воркера
# Заменяем асинхронный драйвер +asyncpg на синхронный psycopg
SYNC_DB_URL = settings.DATABASE_URL.replace("+asyncpg", "+psycopg")
engine = create_engine(SYNC_DB_URL)
SessionLocal = sessionmaker(bind=engine)

@celery_app.task(name="process_audio_pipeline")
def process_audio_pipeline(task_id: str, file_path: str):
    print(f"🔥 Монолит переходит в состояние ВОЙНЫ: зачистка таски {task_id}")
    
    db = SessionLocal()
    try:
        # 1. Меняем статус на PROCESSING
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if not task:
            # Если база еще не успела создать запись, создаем её принудительно
            task = AnalysisTask(id=task_id, status="PROCESSING", audio_path=file_path)
            db.add(task)
        else:
            task.status = "PROCESSING"
        db.commit()

        # 2. Шаг ИИ-1: Локальный Whisper (Транскрибация)
        whisper = WhisperEngine() # Подгрузит веса один раз (Singleton)
        transcript = whisper.transcribe(file_path)
        
        # 3. Шаг ИИ-2: Структурированный анализ
        analyzer = LLMAnalyzer()
        analysis_result = analyzer.analyze_text(transcript)
        
        # 4. Фиксация триумфа в БД
        task.status = "COMPLETED"
        task.transcript = transcript
        task.analysis_result = analysis_result
        db.commit()
        print(f"🎯 Задача {task_id} уничтожена результатом. Статус: COMPLETED")

    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка в ИИ-конвейере: {str(e)}")
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if task:
            task.status = "FAILED"
            db.commit()
    finally:
        db.close()
        # Зачистка территории от временных файлов
        if os.path.exists(file_path):
            os.remove(file_path)