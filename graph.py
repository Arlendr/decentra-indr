"""
graph.py — Анализ графа связей между поставщиками (картельный сговор)
"""

import networkx as nx
import pandas as pd
import numpy as np
from collections import defaultdict


def build_supplier_graph(df: pd.DataFrame) -> nx.Graph:
    """
    Строит граф: узлы = компании, рёбра = совместное участие в тендере.
    Атрибуты рёбер: количество совместных тендеров, совпадения IP/телефона.
    """
    G = nx.Graph()

    # Добавляем все компании как узлы
    for col_bin, col_name in [("winner_bin", "winner_name"), ("loser_bin", "loser_name")]:
        for _, row in df.iterrows():
            G.add_node(row[col_bin], name=row[col_name],
                       ip=row[f"{col_bin.split('_')[0]}_ip"],
                       phone=row[f"{col_bin.split('_')[0]}_phone"])

    # Добавляем рёбра — совместное участие
    for _, row in df.iterrows():
        w, l = row["winner_bin"], row["loser_bin"]
        ip_match  = int(row["winner_ip"] == row["loser_ip"])
        tel_match = int(row["winner_phone"] == row["loser_phone"])

        if G.has_edge(w, l):
            G[w][l]["weight"]    += 1
            G[w][l]["ip_match"]  += ip_match
            G[w][l]["tel_match"] += tel_match
        else:
            G.add_edge(w, l, weight=1, ip_match=ip_match, tel_match=tel_match)

    return G


def compute_graph_risk_scores(df: pd.DataFrame, G: nx.Graph) -> pd.Series:
    """
    Для каждой строки df считает риск на основе графовых признаков победителя.
    """
    # Предварительно считаем признаки для каждого узла
    node_risk = {}
    for node in G.nodes():
        neighbors = list(G.neighbors(node))
        if not neighbors:
            node_risk[node] = 0.0
            continue

        total_co_appearances = sum(G[node][n]["weight"] for n in neighbors)
        total_ip_matches     = sum(G[node][n]["ip_match"] for n in neighbors)
        total_tel_matches    = sum(G[node][n]["tel_match"] for n in neighbors)

        # Насколько часто компания участвует с одними и теми же конкурентами?
        max_w = max(G[node][n]["weight"] for n in neighbors)

        risk = 0.0
        if total_ip_matches > 0:   risk += 0.5
        if total_tel_matches > 0:  risk += 0.3
        if max_w > 3:              risk += min(0.2, max_w * 0.03)  # повторяемость
        node_risk[node] = min(risk, 1.0)

    scores = df["winner_bin"].map(lambda b: node_risk.get(b, 0.0))
    return pd.Series(scores.values, index=df.index, name="graph_risk_score")


def detect_cartels(G: nx.Graph) -> list[dict]:
    """
    Возвращает список подозрительных кластеров (связных компонент с IP/тел-совпадениями).
    """
    suspicious = []
    for component in nx.connected_components(G):
        if len(component) < 2:
            continue
        subG = G.subgraph(component)
        total_ip  = sum(d.get("ip_match", 0)  for _, _, d in subG.edges(data=True))
        total_tel = sum(d.get("tel_match", 0) for _, _, d in subG.edges(data=True))
        if total_ip > 0 or total_tel > 0:
            names = [G.nodes[n].get("name", n) for n in component]
            suspicious.append({
                "companies": names,
                "bins":      list(component),
                "ip_matches":  total_ip,
                "tel_matches": total_tel,
            })
    return suspicious


def explain_graph(row, G: nx.Graph) -> str:
    w_bin = row["winner_bin"]
    l_bin = row["loser_bin"]

    reasons = []
    if G.has_edge(w_bin, l_bin):
        edge = G[w_bin][l_bin]
        if edge.get("ip_match", 0) > 0:
            reasons.append(f"🔴 Совпадение IP-адресов победителя и участника ({row['winner_ip']})")
        if edge.get("tel_match", 0) > 0:
            reasons.append(f"🔴 Совпадение телефонов победителя и участника")
        if edge.get("weight", 0) > 3:
            reasons.append(f"🟡 Эти компании участвовали вместе {edge['weight']} раз — возможная ротация")

    return " | ".join(reasons) if reasons else "✅ Подозрительных связей не обнаружено"
