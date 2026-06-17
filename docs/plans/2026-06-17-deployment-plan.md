# 585 Золото CV MVP — Deployment Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** За 3–5 дней развернуть на Linux-сервере рабочее демо retail video analytics для «585 Золото»: загрузка тестового видео, детекция людей YOLOv8n, трекинг, CSV-метрики, аннотированное видео и простой dashboard.

**Architecture:** MVP работает как single-node pipeline: Python CLI обрабатывает видеофайл, пишет артефакты в `output/`, Streamlit читает CSV и показывает метрики. Для безопасного демо dashboard слушает `127.0.0.1` или mesh/VPN IP, не публичный интернет.

**Tech Stack:** Ubuntu/Debian, Python 3.10+, venv, Ultralytics YOLOv8n, OpenCV headless, pandas, Plotly, Streamlit, FFmpeg, systemd/tmux для демо-запуска.

---

## 0. Текущее состояние проекта

**Каталог на сервере:** `/root/projects/585-zoloto-cv-mvp`

**Созданные файлы:**
- `pipeline.py` — CLI pipeline для видеоаналитики.
- `dashboard.py` — Streamlit dashboard.
- `requirements.txt` — pinned Python-зависимости.
- `scripts/setup.sh` — установка системных пакетов и `.venv`.
- `README.md` — быстрый старт и эксплуатационные заметки.
- `.gitignore`, `.env.example`, `data/.gitkeep`, `output/.gitkeep`.

## 1. Acceptance criteria для демо

Демо считается готовым, если:

1. На сервере есть рабочий venv с зависимостями.
2. Команда `python pipeline.py --input data/input.mp4 ...` завершает обработку тестового ролика.
3. Создаются:
   - `output/output_annotated.mp4`
   - `output/retail_metrics.csv`
4. Dashboard запускается на закрытом интерфейсе:
   - `streamlit run dashboard.py --server.address 127.0.0.1 --server.port 8501`
5. Через SSH tunnel или Tailscale доступен график `people_count` и предпросмотр видео.
6. Код и README готовы к публикации на GitHub.

---

## Phase 1 — День 1: сервер и Python-окружение

### Task 1: Проверить ОС, ресурсы и Python

**Objective:** Убедиться, что сервер подходит для CPU edge-инференса.

**Files:** нет.

**Commands:**

```bash
uname -a
lsb_release -a || cat /etc/os-release
python3 --version
nproc
free -h
df -h
ffmpeg -version | head -n 3 || true
```

**Expected:** Ubuntu/Debian, Python 3.10+, минимум 2 CPU / 4 GB RAM для короткого демо, достаточно места под видео.

### Task 2: Установить системные зависимости

**Objective:** Поставить библиотеки, нужные OpenCV/FFmpeg.

**Files:** нет.

**Commands:**

```bash
sudo apt-get update
sudo apt-get install -y libgl1 libglib2.0-0 ffmpeg python3-pip python3-venv git
```

**Note:** Не делать `apt upgrade -y` без отдельного окна обслуживания, чтобы не сломать работающие сервисы.

### Task 3: Создать venv и поставить Python-пакеты

**Objective:** Изолировать зависимости проекта.

**Files:**
- Read: `requirements.txt`
- Run: `scripts/setup.sh`

**Commands:**

```bash
cd /root/projects/585-zoloto-cv-mvp
bash scripts/setup.sh
source .venv/bin/activate
python -m pip check
```

**Expected:** `No broken requirements found.`

### Task 4: Прогреть модель YOLOv8n

**Objective:** Скачать модель заранее, чтобы демо не зависело от сети в момент показа.

**Commands:**

```bash
cd /root/projects/585-zoloto-cv-mvp
source .venv/bin/activate
python - <<'PY'
from ultralytics import YOLO
YOLO('yolov8n.pt')
print('model ready')
PY
```

**Expected:** `model ready`, файл модели закеширован локально.

---

## Phase 2 — День 1–2: тестовое видео и pipeline

### Task 5: Загрузить тестовое видео

**Objective:** Положить короткий ролик с людьми в проект.

**Files:**
- Create: `data/input.mp4`

**Commands:**

```bash
cd /root/projects/585-zoloto-cv-mvp
cp /path/to/test-video.mp4 data/input.mp4
ffprobe -hide_banner data/input.mp4
```

**Expected:** Видео 30–60 секунд, нормальный FPS, разрешение желательно 720p/1080p.

### Task 6: Запустить базовую обработку

**Objective:** Получить CSV и аннотированное видео.

**Files:**
- Read: `pipeline.py`
- Create: `output/output_annotated.mp4`
- Create: `output/retail_metrics.csv`

**Commands:**

```bash
cd /root/projects/585-zoloto-cv-mvp
source .venv/bin/activate
python pipeline.py \
  --input data/input.mp4 \
  --output-video output/output_annotated.mp4 \
  --metrics output/retail_metrics.csv \
  --model yolov8n.pt \
  --confidence 0.35
```

**Expected:** Console output includes `Pipeline completed`, both output files exist.

### Task 7: Проверить метрики

**Objective:** Убедиться, что CSV читается и содержит трафик.

**Commands:**

```bash
cd /root/projects/585-zoloto-cv-mvp
source .venv/bin/activate
python - <<'PY'
import pandas as pd
p='output/retail_metrics.csv'
df=pd.read_csv(p)
print(df.head())
print(df[['people_count','detections']].describe())
assert len(df) > 0
assert 'people_count' in df.columns
PY
```

**Expected:** Ненулевое количество строк; `people_count` есть. Если все нули — проверить качество видео/угол камеры/confidence.

---

## Phase 3 — День 2: dashboard и безопасный доступ

### Task 8: Запустить Streamlit локально

**Objective:** Поднять dashboard без публичного порта.

**Files:**
- Read: `dashboard.py`

**Commands:**

```bash
cd /root/projects/585-zoloto-cv-mvp
source .venv/bin/activate
streamlit run dashboard.py --server.address 127.0.0.1 --server.port 8501
```

**Expected:** Streamlit слушает только localhost.

### Task 9: Открыть доступ через SSH tunnel

**Objective:** Посмотреть dashboard с локальной машины без открытия firewall.

**Commands from local machine:**

```bash
ssh -L 8501:127.0.0.1:8501 user@server
```

Then open: `http://127.0.0.1:8501`

**Expected:** Видны метрики, график, таблица и видео.

### Task 10: Альтернатива через Tailscale/mesh

**Objective:** Дать закрытый доступ внутри mesh-сети.

**Commands:**

```bash
TAILSCALE_IP=$(tailscale ip -4 | head -n1)
streamlit run dashboard.py --server.address "$TAILSCALE_IP" --server.port 8501
```

**Security:** Разрешать доступ только внутри Tailscale/VPN; не открывать порт `8501` на `0.0.0.0` без auth.

---

## Phase 4 — День 3: упаковка демо

### Task 11: Экспортировать демо-артефакты

**Objective:** Подготовить материалы для показа оффлайн.

**Files:**
- Read: `output/output_annotated.mp4`
- Read: `output/retail_metrics.csv`

**Commands:**

```bash
cd /root/projects/585-zoloto-cv-mvp
ls -lh output/output_annotated.mp4 output/retail_metrics.csv
sha256sum output/output_annotated.mp4 output/retail_metrics.csv > output/SHA256SUMS
```

**Expected:** Можно скачать `output/output_annotated.mp4` и показать без сервера.

### Task 12: Подготовить GitHub публикацию

**Objective:** Показать практический опыт и воспроизводимость.

**Commands:**

```bash
cd /root/projects/585-zoloto-cv-mvp
git status
git add README.md requirements.txt pipeline.py dashboard.py scripts/setup.sh docs/plans/2026-06-17-deployment-plan.md .gitignore .env.example data/.gitkeep output/.gitkeep
git commit -m "feat: add 585 zoloto cv retail mvp"
```

**Do not commit:** реальные видео, CSV с чувствительными данными, ключи, `.env`, внутренние IP/логины.

---

## Phase 5 — День 4–5: расширение до архитектурного разговора

### Task 13: Добавить RTSP ingest в план production-версии

**Objective:** Показать переход от MVP-файла к реальным камерам.

**Design:**
- Источник: RTSP camera / NVR.
- Ingest: FFmpeg/OpenCV reader.
- Processing: YOLOv8n или YOLOv8s при наличии GPU.
- Events: `track_id`, timestamp, zone, confidence.
- Storage: PostgreSQL/Timescale для метрик, S3/MinIO для клипов.
- API: FastAPI для выдачи агрегатов.
- Dashboard: Streamlit/Superset/Grafana.

### Task 14: Добавить зоны интереса

**Objective:** Перевести `people_count` в бизнес-метрики.

**Metrics:**
- входящий/исходящий поток;
- посещаемость зоны витрины;
- dwell time у зоны;
- heatmap по кадру;
- очередь/скопление у кассы.

### Task 15: Добавить эксплуатационные ограничения

**Objective:** Подготовить ответ на вопросы безопасности и edge-инференса.

**Requirements:**
- не хранить лица без необходимости;
- блюр лиц при сохранении клипов;
- хранить только агрегированные метрики по умолчанию;
- закрытый VPN-доступ к dashboard;
- health checks, logs, alerting;
- CPU fallback: `--sample-every 2/3/5`, меньший input resolution, batching off.

---

## Риски и mitigation

- **CPU медленно обрабатывает видео:** уменьшить FPS/resolution, использовать `--sample-every`, оставить YOLOv8n.
- **Модель ошибается на ракурсах магазина:** собрать 5–10 примеров с реальной камеры, подобрать confidence, при необходимости дообучить.
- **Dashboard случайно открыт наружу:** bind только на `127.0.0.1` или Tailscale IP, firewall deny public `8501`.
- **Плохой демо-ролик:** заранее прогнать 2–3 видео и выбрать самое наглядное.
- **Интернет недоступен на показе:** заранее скачать `yolov8n.pt`, подготовить `output_annotated.mp4` оффлайн.

## Команды финальной проверки

```bash
cd /root/projects/585-zoloto-cv-mvp
python3 -m py_compile pipeline.py dashboard.py
test -f README.md && test -f requirements.txt && test -f scripts/setup.sh
test -d data && test -d output && test -d docs/plans
git status --short
```
