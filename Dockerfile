FROM python:3.11-slim

# 1. Устанавливаем системные зависимости и инструменты для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    gcc \
    build-essential \
    pkg-config \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libavfilter-dev \
    libswscale-dev \
    libswresample-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# 2. Сначала копируем только requirements.txt, чтобы использовать кэш Docker слоев
COPY requirements.txt .

# 3. Обновляем pip и устанавливаем зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. Копируем остальной код проекта
COPY . .