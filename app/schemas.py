from pydantic import BaseModel
from typing import Optional, Any

class TaskCreateResponse(BaseModel):
    task_id: str
    status: str
    detail: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    transcript: Optional[str] = None
    analysis_result: Optional[Any] = None