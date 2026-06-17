from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

METRICS_PATH = Path("output/retail_metrics.csv")
VIDEO_PATH = Path("output/output_annotated.mp4")

st.set_page_config(page_title="585 Золото — Retail CV Analytics", layout="wide")
st.title("585 Золото — CV аналитика трафика")
st.caption("MVP: детекция людей, трекинг, метрики по кадрам, демо-дэшборд")


@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame | None:
    metrics_file = Path(path)
    if not metrics_file.exists():
        return None
    return pd.read_csv(metrics_file)


df = load_data(str(METRICS_PATH))

if df is None or df.empty:
    st.warning("Сначала запустите pipeline.py: метрики output/retail_metrics.csv пока не найдены.")
    st.code(
        "python pipeline.py --input data/input.mp4 --output-video output/output_annotated.mp4 --metrics output/retail_metrics.csv",
        language="bash",
    )
    st.stop()

summary_cols = st.columns(4)
summary_cols[0].metric("Кадров обработано", len(df))
summary_cols[1].metric("Макс. людей в кадре", int(df["people_count"].max()))
summary_cols[2].metric("Среднее людей", round(float(df["people_count"].mean()), 2))
summary_cols[3].metric("Макс. детекций", int(df.get("detections", df["people_count"]).max()))

st.subheader("Динамика присутствия посетителей")
x_axis = "second" if "second" in df.columns else "frame"
fig = px.line(df, x=x_axis, y="people_count", markers=False, title="People count over time")
fig.update_layout(xaxis_title=x_axis, yaxis_title="people_count")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Аннотированное видео")
if VIDEO_PATH.exists():
    st.video(str(VIDEO_PATH))
else:
    st.info("Видео output/output_annotated.mp4 пока не найдено.")

st.subheader("Сырые метрики")
st.dataframe(df, use_container_width=True)

st.download_button(
    "Скачать CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="retail_metrics.csv",
    mime="text/csv",
)
