from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import uuid
import os
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import TaskStatusResponse
from app.schemas import TaskCreateResponse
from app.tasks import process_audio_pipeline
from app.database import get_db
from app.models import AnalysisTask

api_router = APIRouter(prefix="/api/v1")
UPLOAD_DIR = "/tmp/audio_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@api_router.post("/analyze", response_model=TaskCreateResponse, status_code=202)
async def upload_audio(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename.lower().endswith(('.mp3', '.wav', '.m4a', '.ogg')):
        raise HTTPException(status_code=400, detail="Недопустимый формат аудио.")
    
    task_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    saved_file_path = os.path.join(UPLOAD_DIR, f"{task_id}{file_extension}")
    
    try:
        with open(saved_file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 64):
                buffer.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения файла: {str(e)}")
        
    # Записываем в БД со статусом PENDING
    new_task = AnalysisTask(id=task_id, status="PENDING", audio_path=saved_file_path)
    db.add(new_task)
    await db.commit()
    
    # Публикуем в очередь
    process_audio_pipeline.delay(task_id, saved_file_path)
    
    return TaskCreateResponse(
        task_id=task_id,
        status="QUEUED",
        detail="Файл принят. Анализ запущен в фоновом режиме."
    )


@api_router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, db: AsyncSession = Depends(get_db)):
    # Ленивая загрузка задачи из асинхронной сессии
    from sqlalchemy import select
    result = await db.execute(select(AnalysisTask).where(AnalysisTask.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
        
    return TaskStatusResponse(
        task_id=task.id,
        status=task.status,
        transcript=task.transcript,
        analysis_result=task.analysis_result
    )