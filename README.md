# 585 Золото — CV Retail MVP

Мини-проект для демо мультимодальной retail-аналитики: детекция людей на видео, трекинг, CSV-метрики и Streamlit-дашборд.

## Что внутри

- `pipeline.py` — обработка `data/input.mp4`, YOLOv8 nano, трекинг людей, аннотированное видео и метрики.
- `dashboard.py` — Streamlit-дашборд по `output/retail_metrics.csv`.
- `requirements.txt` — Python-зависимости.
- `scripts/setup.sh` — безопасная установка Python-окружения без `apt upgrade`.
- `docs/plans/2026-06-17-deployment-plan.md` — план разворачивания инфраструктуры на сервере.

## Быстрый старт

```bash
cd /root/projects/585-zoloto-cv-mvp
bash scripts/setup.sh
source .venv/bin/activate
cp /path/to/test-video.mp4 data/input.mp4
python pipeline.py --input data/input.mp4 --output-video output/output_annotated.mp4 --metrics output/retail_metrics.csv
streamlit run dashboard.py --server.address 127.0.0.1 --server.port 8501
```

## Безопасный доступ к дашборду

Не открывать `8501` в интернет. Варианты:

1. SSH tunnel:
   ```bash
   ssh -L 8501:127.0.0.1:8501 user@server
   ```
2. Tailscale/mesh IP:
   ```bash
   streamlit run dashboard.py --server.address <tailscale_ip> --server.port 8501
   ```
3. Внутренний reverse proxy с Basic Auth/VPN-only, если нужен общий доступ.

## Ожидаемые артефакты демо

- `output/output_annotated.mp4` — видео с bounding boxes/track IDs.
- `output/retail_metrics.csv` — метрики по кадрам.
- Streamlit dashboard — график количества людей в кадре.

## Следующий production-вектор

MVP показывает весь путь `кадр → детекция → трекинг → метрика → дашборд`. После демо надо добавить RTSP ingest, хранение событий, очереди задач, API и эксплуатационный мониторинг.
