# 🚀 Развертывание на Google Cloud

## Шаг 1: Подготовка

### 1.1 Установи Google Cloud CLI

```bash
# macOS
brew install google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# Windows
# Скачай отсюда: https://cloud.google.com/sdk/docs/install
```

### 1.2 Авторизуйся в Google Cloud

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

## Шаг 2: Создай секреты в Google Cloud Secret Manager

### 2.1 Создай OpenAI API ключ

```bash
echo -n "sk-proj-YOUR_OPENAI_API_KEY" | gcloud secrets create openai-api-key --data-file=-
```

### 2.2 Создай Telegram Bot Token

```bash
echo -n "YOUR_TELEGRAM_BOT_TOKEN" | gcloud secrets create telegram-bot-token --data-file=-
```

### 2.3 Создай Telegram Chat ID

```bash
echo -n "YOUR_TELEGRAM_CHAT_ID" | gcloud secrets create telegram-chat-id --data-file=-
```

## Шаг 3: Дай доступ Cloud Run к секретам

```bash
# Получи Service Account
PROJECT_ID=$(gcloud config get-value project)
SERVICE_ACCOUNT="$PROJECT_ID@appspot.gserviceaccount.com"

# Дай доступ к каждому секрету
gcloud secrets add-iam-policy-binding openai-api-key \
  --member=serviceAccount:$SERVICE_ACCOUNT \
  --role=roles/secretmanager.secretAccessor

gcloud secrets add-iam-policy-binding telegram-bot-token \
  --member=serviceAccount:$SERVICE_ACCOUNT \
  --role=roles/secretmanager.secretAccessor

gcloud secrets add-iam-policy-binding telegram-chat-id \
  --member=serviceAccount:$SERVICE_ACCOUNT \
  --role=roles/secretmanager.secretAccessor
```

## Шаг 4: Загрузи credentials.json для Gmail

```bash
# Скачай credentials.json из Google Cloud Console
# Положи его в папку проекта

# Загрузи на Cloud Run (будет доступен в /workspace/credentials.json)
gcloud run deploy delivery-bot \
  --source . \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID
```

## Шаг 5: Развертывание

```bash
cd ~/Desktop/delivery-bot

gcloud run deploy delivery-bot \
  --source . \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID \
  --memory 512Mi \
  --timeout 3600
```

## Шаг 6: Проверка

```bash
# Получи URL
gcloud run services describe delivery-bot --region europe-west1

# Проверь здоровье
curl https://YOUR_SERVICE_URL/

# Запусти проверку доставок
curl -X POST https://YOUR_SERVICE_URL/check
```

## 🔐 Переменные окружения на Cloud Run

Бот автоматически получит из Google Cloud Secret Manager:
- `openai-api-key` → `OPENAI_API_KEY`
- `telegram-bot-token` → `TELEGRAM_BOT_TOKEN`
- `telegram-chat-id` → `TELEGRAM_CHAT_ID`

## 📊 Мониторинг

```bash
# Смотри логи
gcloud run logs read delivery-bot --region europe-west1 --limit 50

# Смотри в реальном времени
gcloud run logs read delivery-bot --region europe-west1 --follow
```

## 🔄 Обновление

```bash
# Просто загрузи новый код
gcloud run deploy delivery-bot --source .
```

## ❌ Если что-то не работает

```bash
# Проверь что секреты созданы
gcloud secrets list

# Проверь что Service Account имеет доступ
gcloud secrets get-iam-policy openai-api-key

# Проверь логи
gcloud run logs read delivery-bot --region europe-west1 --limit 100
```

---

**Готово! Твой бот работает на Google Cloud!** 🎉
