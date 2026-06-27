import os
from faster_whisper import WhisperModel
import threading

class WhisperEngine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(WhisperEngine, cls).__new__(cls)
                print("🔱 Загрузка улучшенной ИИ-модели для русского языка...")
                
                
                cls._instance.model = WhisperModel(
                    "small", 
                    device="cpu", 
                    compute_type="float32"
                )
                print(" Улучшенная модель Faster-Whisper готова.")
        return cls._instance

    def transcribe(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Аудиофайл не найден: {file_path}")
            
        # initial_prompt задает ИИ контекст, чтобы он правильно расставлял знаки препинания, 
        # понимал аббревиатуры, ИТ-термины, названия компаний (Касперский, 1С) и деловой стиль.
        segments, info = self.model.transcribe(
            file_path, 
            beam_size=5,
            language="ru",  # Жестко фиксируем русский язык, чтобы не тратить время на автоопределение
            initial_prompt="Разговор менеджера поддержки и клиента. Обсуждение работы в базе данных, обновление 1С, администрирование, Лаборатория Касперского, продление лицензии, счета и закрытие сделки."
        )
        
        text_blocks = [segment.text for segment in segments]
        return " ".join(text_blocks).strip()