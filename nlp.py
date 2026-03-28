"""
nlp.py — NLP-анализ технических спецификаций (обнаружение «заточки»)
"""

import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ─── Эталонные «коммерческие предложения» компаний картеля ───────────────────
# В реальной системе они загружались бы из базы документов
CARTEL_COMMERCIAL_OFFERS = [
    # Коммерческое предложение ТОО «АлфаГрупп»
    "Canon imageRUNNER ADVANCE DX C3826i серийная серия 2023-KZ-ONLY сертификация ISO/IEC 24734:2014 "
    "казахстанский патент KZ20230001 картриджи T12-KZ гарантийное обслуживание АлфаГрупп",

    # Коммерческое предложение по серверам
    "Intel Xeon Gold 6258R Supermicro X12DPi-N6 rev.2.01 Samsung DDR4-3200 ECC RDIMM 32GB партия 2022 "
    "авторизованный партнёр вендора сертификат 2023",

    # Коммерческое предложение по медицинским перчаткам
    "Mercator Medical Польша нитриловые 0.10 мм EN455-2022 упаковка 98 штук реестр МЗ РК MZ-2022-4471",
]

TAILORED_KEYWORDS = [
    r"строго\s+(данн[аяое]?\s+модел[ьи]|эт[аоу]\s+марк[аоу]|указанн)",
    r"не\s+ниже\s+rev\.",
    r"партия\s+\d{4}\s+года",
    r"реестр.*?под\s+номером",
    r"сертификат.*?серии.*?KZ",
    r"только\s+через\s+официального\s+дилера",
    r"гарантийное\s+обслуживание\s+только",
    r"аккредитован\s+в\s+реестре",
    r"упаковка\s+строго\s+по\s+\d+\s+штук",
]


def preprocess_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compute_nlp_risk_scores(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """
    Возвращает:
      - nlp_similarity_score: 0..1, схожесть с коммерческими предложениями картеля
      - nlp_tailored_score:   0..1, количество «стоп-паттернов» в спецификации
    """
    specs_clean = df["specification"].fillna("").apply(preprocess_text)
    offers_clean = [preprocess_text(o) for o in CARTEL_COMMERCIAL_OFFERS]

    # TF-IDF + cosine similarity
    all_texts = list(specs_clean) + offers_clean
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    spec_matrix  = tfidf_matrix[:len(specs_clean)]
    offer_matrix = tfidf_matrix[len(specs_clean):]

    sim_matrix = cosine_similarity(spec_matrix, offer_matrix)   # (n_tenders, n_offers)
    max_similarity = sim_matrix.max(axis=1)                      # макс. схожесть с любым КП

    # Подсчёт «стоп-паттернов»
    tailored_scores = []
    for spec in df["specification"].fillna(""):
        hits = sum(1 for pattern in TAILORED_KEYWORDS if re.search(pattern, spec, re.IGNORECASE))
        tailored_scores.append(min(hits / len(TAILORED_KEYWORDS), 1.0))

    return (
        pd.Series(max_similarity, index=df.index, name="nlp_similarity_score"),
        pd.Series(tailored_scores, index=df.index, name="nlp_tailored_score"),
    )


def explain_nlp(row) -> str:
    spec = row.get("specification", "")
    reasons = []

    sim = row.get("nlp_similarity_score", 0)
    if sim > 0.5:
        reasons.append(f"🔴 Текст спецификации на {sim*100:.0f}% совпадает с коммерческим предложением ТОО «АлфаГрупп»")
    elif sim > 0.25:
        reasons.append(f"🟡 Умеренное сходство ({sim*100:.0f}%) с известными коммерческими предложениями")

    hits = [p for p in TAILORED_KEYWORDS if re.search(p, spec, re.IGNORECASE)]
    if hits:
        reasons.append(f"🔴 Обнаружены {len(hits)} признака «заточки» спецификации (избыточная специфичность требований)")

    # Кириллица/латиница подмена
    cyrillic_latin_subs = re.findall(r"[аеосрхАЕОСРХ][a-zA-Z]|[a-zA-Z][аеосрхАЕОСРХ]", spec)
    if cyrillic_latin_subs:
        reasons.append(f"🔴 Замена кириллических букв латинскими ({len(cyrillic_latin_subs)} вхождений) — вероятно скрытие тендера от поиска")

    return " | ".join(reasons) if reasons else "✅ Спецификация не содержит признаков заточки"
