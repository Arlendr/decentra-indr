"""
app.py — Streamlit-дашборд «AI-Антикартель»
Запуск: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import sys
import os

# Добавляем корневую папку в path для импортов
sys.path.insert(0, os.path.dirname(__file__))

from data_generator import generate_tenders
from anomaly import compute_price_anomaly_score, explain_price
from graph   import build_supplier_graph, compute_graph_risk_scores, detect_cartels, explain_graph
from nlp     import compute_nlp_risk_scores, explain_nlp

# ─── Конфиг страницы ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI-Антикартель | Анализ госзакупок",
    page_icon="🛡️",
    layout="wide",
)

# ─── Стили ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Цвета риска */
.risk-high   { color: #FF4B4B; font-weight: bold; }
.risk-medium { color: #FFA500; font-weight: bold; }
.risk-low    { color: #21C55D; font-weight: bold; }

/* Карточки метрик */
.metric-card {
    background: linear-gradient(135deg, #1E1E2E 0%, #252536 100%);
    border-radius: 12px;
    padding: 16px;
    margin: 8px;
    border: 1px solid #333;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

/* Заголовки секций */
.section-header {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 12px;
    color: #E5E7EB;
}

/* Таблицы */
.stDataFrame {
    border-radius: 8px;
    overflow: hidden;
}

/* Всплывающие подсказки */
.tooltip {
    position: relative;
    display: inline-block;
    cursor: help;
}
.tooltip .tooltiptext {
    visibility: hidden;
    width: 220px;
    background-color: #1F2937;
    color: #E5E7EB;
    text-align: left;
    border-radius: 6px;
    padding: 8px;
    position: absolute;
    z-index: 1;
    bottom: 125%;
    left: 50%;
    margin-left: -110px;
    opacity: 0;
    transition: opacity 0.3s;
    border: 1px solid #374151;
}
.tooltip:hover .tooltiptext {
    visibility: visible;
    opacity: 1;
}

/* Кнопки */
.stButton > button {
    border-radius: 8px;
    border: 1px solid #374151;
    background: #1F2937;
    color: #E5E7EB;
}
.stButton > button:hover {
    background: #374151;
}

/* Фильтры */
.filter-container {
    background: #111827;
    padding: 12px;
    border-radius: 8px;
    border: 1px solid #374151;
}

/* Индикаторы */
.indicator-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
}
.dot-high { background: #FF4B4B; }
.dot-medium { background: #FFA500; }
.dot-low { background: #21C55D; }

/* Анимации */
@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}
.pulse { animation: pulse 2s infinite; }

/* Графики */
.chart-container {
    background: #0B1220;
    border-radius: 8px;
    padding: 8px;
    border: 1px solid #1F2937;
}

/* Навигационная панель */
.nav-tabs {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
}
.nav-tab {
    padding: 10px 16px;
    border-radius: 8px;
    border: 1px solid #374151;
    background: #1F2937;
    color: #E5E7EB;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 8px;
}
.nav-tab:hover {
    background: #374151;
}
.nav-tab.active {
    background: #2563EB;
    border-color: #2563EB;
    color: white;
}

/* Сайдбар */
.sidebar {
    background: #0B1220;
    border-right: 1px solid #1F2937;
    padding: 16px;
    border-radius: 8px;
}

/* Контент */
.content {
    background: #0B1220;
    border-radius: 8px;
    padding: 16px;
    border: 1px solid #1F2937;
}
</style>
""", unsafe_allow_html=True)


# ─── Загрузка и анализ данных ─────────────────────────────────────────────────
@st.cache_data
def load_and_analyze():
    df = generate_tenders()

    # 1. Аномалии цен
    df["price_anomaly_score"] = compute_price_anomaly_score(df)

    # 2. Граф связей
    G = build_supplier_graph(df)
    df["graph_risk_score"] = compute_graph_risk_scores(df, G)

    # 3. NLP
    df["nlp_similarity_score"], df["nlp_tailored_score"] = compute_nlp_risk_scores(df)

    # 4. Итоговый Risk Score (взвешенная сумма)
    df["risk_score"] = (
        df["price_anomaly_score"] * 0.35 +
        df["graph_risk_score"]    * 0.40 +
        df["nlp_similarity_score"] * 0.15 +
        df["nlp_tailored_score"]  * 0.10
    ).round(3)

    df["risk_level"] = pd.cut(
        df["risk_score"],
        bins=[-0.001, 0.35, 0.60, 1.001],
        labels=["🟢 Низкий", "🟡 Средний", "🔴 Высокий"]
    )

    return df, G


df, G = load_and_analyze()

# ─── Хедер ───────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🛡️ AI-Антикартель</div>', unsafe_allow_html=True)
st.markdown("### Система графового и семантического анализа госзакупок для выявления скрытых сговоров")
st.markdown("---")

# ─── Навигационная панель ─────────────────────────────────────────────────────
st.markdown('<div class="nav-tabs">', unsafe_allow_html=True)
col_nav1, col_nav2, col_nav3 = st.columns(3)
with col_nav1:
    st.markdown('<div class="nav-tab active"><span>📊</span> Список тендеров</div>', unsafe_allow_html=True)
with col_nav2:
    st.markdown('<div class="nav-tab"><span>📈</span> Аналитика</div>', unsafe_allow_html=True)
with col_nav3:
    st.markdown('<div class="nav-tab"><span>🕸️</span> Граф связей</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
st.markdown("---")

# ─── Метрики ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Ключевые метрики</div>', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
high_risk = (df["risk_level"] == "🔴 Высокий").sum()
med_risk  = (df["risk_level"] == "🟡 Средний").sum()
cartels   = detect_cartels(G)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("📋 Всего тендеров", len(df))
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("🔴 Высокий риск", high_risk, delta=f"{high_risk/len(df)*100:.0f}% от всех")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("🟡 Средний риск", med_risk)
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("🕸️ Картельных кластеров", len(cartels))
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ─── Боковая панель ───────────────────────────────────────────────────────────
st.sidebar.markdown('<div class="sidebar">', unsafe_allow_html=True)
st.sidebar.markdown('<div class="section-header">⚙️ Фильтры</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="filter-container">', unsafe_allow_html=True)

risk_filter = st.sidebar.multiselect(
    "Уровень риска",
    ["🔴 Высокий", "🟡 Средний", "🟢 Низкий"],
    default=["🔴 Высокий", "🟡 Средний"],
)

show_explain = st.sidebar.checkbox("Показывать объяснения AI", value=True)

sort_by = st.sidebar.selectbox(
    "Сортировать по",
    ["risk_score", "price", "date"],
    format_func=lambda x: {"risk_score": "Risk Score", "price": "Цена", "date": "Дата"}[x]
)

st.sidebar.markdown('</div>', unsafe_allow_html=True)
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# ─── Вкладки ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Список тендеров", "🕸️ Граф связей", "📈 Аналитика"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: Список тендеров
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">📊 Список тендеров</div>', unsafe_allow_html=True)
    df_filtered = df[df["risk_level"].isin(risk_filter)].sort_values(sort_by, ascending=False)
    st.markdown(f"**Найдено {len(df_filtered)} тендеров**")

    for _, row in df_filtered.iterrows():
        risk = str(row["risk_level"])
        score = row["risk_score"]

        # Индикатор риска
        dot_class = "dot-high" if "🔴" in risk else "dot-medium" if "🟡" in risk else "dot-low"
        risk_indicator = f'<span class="indicator-dot {dot_class}"></span>{risk}'

        with st.expander(
            f"{risk_indicator} | **{row['tender_id']}** | {row['winner_name']} | "
            f"{row['price']:,.0f} ₸ | Risk Score: **{score:.2f}**"
        ):
            c1, c2, c3 = st.columns(3)
            c1.metric("Цена тендера",    f"{row['price']:,.0f} ₸")
            c2.metric("Медианная цена",  f"{row['median_price']:,.0f} ₸")
            c3.metric("Risk Score",      f"{score:.3f}")

            st.markdown("**👤 Победитель:**")
            st.markdown(f"- Компания: `{row['winner_name']}` (БИН: `{row['winner_bin']}`)")
            st.markdown(f"- IP: `{row['winner_ip']}` | Тел: `{row['winner_phone']}`")

            st.markdown("**👤 Участник (проигравший):**")
            st.markdown(f"- Компания: `{row['loser_name']}` (БИН: `{row['loser_bin']}`)")
            st.markdown(f"- IP: `{row['loser_ip']}` | Тел: `{row['loser_phone']}`")

            if show_explain:
                st.markdown("---")
                st.markdown("**🤖 Объяснения AI:**")

                price_exp = explain_price(row)
                graph_exp = explain_graph(row, G)
                nlp_exp   = explain_nlp(row)

                st.markdown(f"**💰 Анализ цены:** {price_exp}")
                st.markdown(f"**🕸️ Анализ связей:** {graph_exp}")
                st.markdown(f"**📝 Анализ спецификации:** {nlp_exp}")

            st.markdown("**📄 Техническая спецификация:**")
            st.info(row["specification"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: Граф связей (текстовое представление)
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">🕸️ Граф связей</div>', unsafe_allow_html=True)

    st.markdown("**Обнаруженные картельные кластеры**")
    if not cartels:
        st.success("Подозрительных картельных кластеров не обнаружено")
    else:
        for i, cluster in enumerate(cartels, 1):
            st.error(f"**Кластер #{i} — Подозрительная группа компаний**")
            cols = st.columns(len(cluster["companies"]))
            for col, name in zip(cols, cluster["companies"]):
                col.markdown(f"🏢 **{name}**")

            st.markdown(
                f"- 🔴 Совпадений IP-адресов: **{cluster['ip_matches']}** "
                f"(компании подавали заявки с одного IP)\n"
                f"- 🔴 Совпадений телефонов: **{cluster['tel_matches']}**\n"
                f"- 📌 Вероятный сценарий: **искусственная конкуренция** — "
                f"компании принадлежат одному владельцу и создают иллюзию независимых участников"
            )
            st.markdown("---")

    # Таблица рёбер графа
    st.markdown("**📋 Все связи между поставщиками**")
    edges_data = []
    for u, v, d in G.edges(data=True):
        edges_data.append({
            "Компания А":           G.nodes[u].get("name", u),
            "Компания Б":           G.nodes[v].get("name", v),
            "Совм. тендеров":       d.get("weight", 0),
            "Совпад. IP":           d.get("ip_match", 0),
            "Совпад. телефон":      d.get("tel_match", 0),
        })
    edges_df = pd.DataFrame(edges_data).sort_values("Совпад. IP", ascending=False)
    st.dataframe(edges_df, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: Аналитика
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">📈 Аналитика</div>', unsafe_allow_html=True)

    # Распределение Risk Score
    st.markdown("**Распределение Risk Score**")
    hist_data = pd.cut(df["risk_score"], bins=10).value_counts().sort_index()
    hist_df = pd.DataFrame({
        'Диапазон': hist_data.index.astype(str),
        'Количество': hist_data.values
    })
    st.bar_chart(hist_df.set_index('Диапазон')['Количество'])

    # ТОП-10 самых рискованных тендеров
    st.markdown("**🔴 ТОП-10 самых рискованных тендеров**")
    top10 = df.nlargest(10, "risk_score")[
        ["tender_id", "winner_name", "price", "risk_score", "risk_level"]
    ].rename(columns={
        "tender_id":    "ID тендера",
        "winner_name":  "Победитель",
        "price":        "Цена (₸)",
        "risk_score":   "Risk Score",
        "risk_level":   "Уровень риска",
    })
    st.dataframe(top10, use_container_width=True)

    # Разбивка по уровням риска
    st.markdown("**📊 Разбивка по уровням риска**")
    risk_counts = df["risk_level"].value_counts()
    st.bar_chart(risk_counts)

    # Полная таблица тендеров
    st.markdown("**📋 Полная таблица тендеров**")
    display_df = df[[
        "tender_id", "date", "winner_name", "loser_name",
        "price", "median_price", "risk_score", "risk_level"
    ]].rename(columns={
        "tender_id":   "ID",
        "date":        "Дата",
        "winner_name": "Победитель",
        "loser_name":  "Участник",
        "price":       "Цена",
        "median_price":"Медиана",
        "risk_score":  "Risk",
        "risk_level":  "Уровень",
    })
    st.dataframe(display_df, use_container_width=True)

st.markdown("---")
st.markdown('<div class="section-header">🛡️ AI-Антикартель | Decentrathon 5.0 | Кейс 3: AI for Government</div>', unsafe_allow_html=True)
