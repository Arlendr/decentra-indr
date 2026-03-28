"""
anomaly.py — Детекция аномальных цен через Isolation Forest
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


def compute_price_anomaly_score(df: pd.DataFrame) -> pd.Series:
    """
    Возвращает Series с числовым score аномалии цены (0..1, чем выше — тем подозрительнее).
    Также возвращает human-readable объяснение.
    """
    # Признаки: отношение цены к медиане + абсолютная цена (в лог-масштабе)
    features = pd.DataFrame({
        "price_ratio":     df["price"] / (df["median_price"] + 1),
        "log_price":       np.log1p(df["price"]),
        "log_median":      np.log1p(df["median_price"]),
    }).fillna(0)

    scaler = StandardScaler()
    X = scaler.fit_transform(features)

    clf = IsolationForest(n_estimators=200, contamination=0.08, random_state=42)
    clf.fit(X)

    # decision_function: чем ниже — тем аномальнее; нормируем в [0,1]
    raw_scores = clf.decision_function(X)          # диапазон примерно [-0.5, 0.5]
    normalized  = 1 - (raw_scores - raw_scores.min()) / (raw_scores.max() - raw_scores.min() + 1e-9)

    return pd.Series(normalized, index=df.index, name="price_anomaly_score")


def explain_price(row) -> str:
    ratio = row["price"] / (row["median_price"] + 1)
    if ratio > 10:
        return f"⚠️ Цена превышает среднерыночную в {ratio:.0f} раз (цена: {row['price']:,.0f} ₸, медиана: {row['median_price']:,.0f} ₸)"
    elif ratio > 3:
        return f"⚠️ Цена выше рыночной на {(ratio-1)*100:.0f}% (цена: {row['price']:,.0f} ₸, медиана: {row['median_price']:,.0f} ₸)"
    else:
        return f"✅ Цена в норме (цена: {row['price']:,.0f} ₸, медиана: {row['median_price']:,.0f} ₸)"
