from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, Boolean, JSON
from app.database import Base
import uuid

class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status: Mapped[str] = mapped_column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    audio_path: Mapped[str] = mapped_column(String, nullable=True)
    transcript: Mapped[str] = mapped_column(Text, nullable=True)
    analysis_result: Mapped[dict] = mapped_column(JSON, nullable=True)