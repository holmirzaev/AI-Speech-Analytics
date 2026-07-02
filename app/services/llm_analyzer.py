import httpx
import json
from pydantic import BaseModel, Field
from typing import List
from app.config import settings

class BusinessAnalysisSchema(BaseModel):
    manager_politeness_score: int = Field(..., description="Оценка вежливости менеджера от 1 до 5")
    deal_closed: bool = Field(..., description="Была ли закрыта сделка/договоренность в звонке")
    client_objections: List[str] = Field(..., description="Список возражений, которые высказал клиент")
    summary: str = Field(..., description="Краткое содержание разговора (1-2 предложения)")


class LLMAnalyzer:
    def __init__(self):
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.iam_token = settings.YANDEX_IAM_TOKEN
        self.folder_id = settings.YANDEX_FOLDER_ID

    async def analyze_text(self, transcript_text: str) -> dict:
        """
        Асинхронный анализ текста через YandexGPT API.
        Не блокирует event loop FastAPI.
        """
        if not transcript_text:
            return {"error": "Текст пустой"}

        print("🧠 Отправка транскрипта в YandexGPT для бизнес-анализа...")

        prompt = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt/latest",
            "completionOptions": {"stream": False, "temperature": 0.2, "maxTokens": 2000},
            "messages": [
                {
                    "role": "system",
                    "text": (
                        "Ты — профессиональный речевой аналитик отдела продаж. "
                        "Проанализируй текст звонка и верни ответ СТРОГО в формате JSON со следующими полями:\n"
                        "manager_politeness_score (число от 1 до 5),\n"
                        "deal_closed (true/false),\n"
                        "client_objections (массив строк с возражениями),\n"
                        "summary (краткое содержание звонка).\n"
                        "Никакого другого текста, кроме чистого JSON, не возвращай."
                    )
                },
                {"role": "user", "text": f"Текст звонка для анализа:\n{transcript_text}"}
            ]
        }

        headers = {
            "Authorization": f"Bearer {self.iam_token}",
            "x-folder-id": self.folder_id,
            "Content-Type": "application/json"
        }

        # Используем асинхронный контекстный менеджер httpx.AsyncClient()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.api_url, json=prompt, headers=headers, timeout=30.0)
                response.raise_for_status()
                result = response.json()
            
            raw_json = result['result']['alternatives'][0]['message']['text']
            raw_json = raw_json.strip().strip("`").replace("json", "").strip()
            
            validated_data = json.loads(raw_json)
            return validated_data
        
        except Exception as e:
            print(f"⚠️ Ошибка вызова LLM API, применяем фоллбэк: {str(e)}")
            return {
                "manager_politeness_score": 5 if "добрый день" in transcript_text.lower() else 4,
                "deal_closed": any(w in transcript_text.lower() for w in ["до свидания", "спасибо", "согласен"]),
                "client_objections": ["Требуется ручная проверка (Фоллбэк режим)"],
                "summary": f"Фоллбэк-анализ. Текст звонка: {transcript_text[:50]}..."
            }