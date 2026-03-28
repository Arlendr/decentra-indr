import pandas as pd
import numpy as np
import random
import json
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

# ─── Легитимные компании ───────────────────────────────────────────────────────
LEGIT_COMPANIES = [
    {"bin": "100000000001", "name": "ТОО «СтройСервис»",       "ip": "192.168.1.10", "phone": "+77011111111"},
    {"bin": "100000000002", "name": "ТОО «АлматыСнаб»",        "ip": "192.168.2.20", "phone": "+77022222222"},
    {"bin": "100000000003", "name": "ТОО «НурСтрой»",          "ip": "192.168.3.30", "phone": "+77033333333"},
    {"bin": "100000000004", "name": "ТОО «АстанаТрейд»",       "ip": "192.168.4.40", "phone": "+77044444444"},
    {"bin": "100000000005", "name": "ТОО «КазСнабжение»",      "ip": "192.168.5.50", "phone": "+77055555555"},
    {"bin": "100000000006", "name": "ТОО «ОптимаСервис»",      "ip": "192.168.6.60", "phone": "+77066666666"},
    {"bin": "100000000007", "name": "ТОО «ЦентрТех»",          "ip": "192.168.7.70", "phone": "+77077777777"},
    {"bin": "100000000008", "name": "ТОО «БизнесПро»",         "ip": "192.168.8.80", "phone": "+77088888888"},
]

# ─── Картельная группа (3 компании, фактически один владелец) ─────────────────
CARTEL = [
    {"bin": "999000000001", "name": "ТОО «АлфаГрупп»",         "ip": "10.0.0.99",  "phone": "+77099999999"},
    {"bin": "999000000002", "name": "ТОО «БетаСнаб»",          "ip": "10.0.0.99",  "phone": "+77099999999"},  # тот же IP и тел!
    {"bin": "999000000003", "name": "ТОО «ГаммаТрейд»",        "ip": "10.0.0.100", "phone": "+77099999990"},  # почти тот же тел
]

SPEC_NORMAL = [
    "Поставка офисной бумаги формата А4, плотность 80 г/м², белизна не менее 146% CIE, 500 листов в пачке.",
    "Поставка компьютерных мышей, оптических, USB-подключение, разрешение не менее 800 DPI.",
    "Предоставление услуг по уборке административных помещений, площадь 500 кв.м., ежедневно.",
    "Поставка шариковых ручек, синяя паста, корпус прозрачный, стержень сменный.",
    "Поставка картриджей для принтера HP LaserJet Pro, оригинальные или совместимые.",
    "Услуги по техническому обслуживанию лифтового оборудования, плановое ТО раз в квартал.",
    "Поставка мебели офисной: столы рабочие 1200×600 мм, стулья с подлокотниками, шкафы-купе.",
    "Услуги по разработке программного обеспечения для автоматизации учёта персонала.",
]

SPEC_TAILORED = [
    # «Заточенная» спецификация — требования под конкретный товар
    "Поставка принтеров: модель строго Canon imageRUNNER ADVANCE DX C3826i, серийная серия 2023-KZ-ONLY, "
    "обязательна сертификация ISO/IEC 24734:2014 и наличие казахстанского патента №KZ20230001, "
    "совместимость только с картриджами серии T12-KZ. Гарантийное обслуживание только через официального дилера ТОО «АлфаГрупп».",

    "Закупка серверного оборудования: CPU Intel Xeon Gold 6258R (строго данная модель), материнская плата "
    "Supermicro X12DPi-N6 rev.2.01 (не ниже), оперативная память Samsung DDR4-3200 ECC RDIMM 32GB (партия 2022 года). "
    "Поставщик обязан иметь сертификат авторизованного партнёра вендора, выданный не ранее 01.01.2023.",

    "Поставка медицинских перчаток: строго нитриловые, производитель Mercator Medical (Польша), "
    "толщина 0.10±0.005 мм (допуск ±0.005), сертификат EN455-2022, упаковка строго по 98 штук. "
    "Поставщик обязан быть аккредитован в реестре МЗ РК за 2022 год под номером MZ-2022-4471.",
]

def generate_tenders(n_normal=40, n_cartel=8, n_price_anomaly=5, n_tailored=3):
    rows = []
    tender_id = 1000

    def make_row(winner, loser, price, median_price, spec, flags):
        nonlocal tender_id
        tender_id += 1
        date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 300))
        return {
            "tender_id":      f"RK-{tender_id}",
            "date":           date.strftime("%Y-%m-%d"),
            "title":          f"Тендер №{tender_id}",
            "price":          round(price, 2),
            "median_price":   round(median_price, 2),
            "winner_bin":     winner["bin"],
            "winner_name":    winner["name"],
            "winner_ip":      winner["ip"],
            "winner_phone":   winner["phone"],
            "loser_bin":      loser["bin"],
            "loser_name":     loser["name"],
            "loser_ip":       loser["ip"],
            "loser_phone":    loser["phone"],
            "specification":  spec,
            "flags":          json.dumps(flags, ensure_ascii=False),
            "risk_score":     0.0,  # будет заполнено моделями
        }

    # 1. Нормальные тендеры
    for _ in range(n_normal):
        w, l = random.sample(LEGIT_COMPANIES, 2)
        med = random.uniform(50_000, 5_000_000)
        price = med * random.uniform(0.85, 1.15)
        spec = random.choice(SPEC_NORMAL)
        rows.append(make_row(w, l, price, med, spec, []))

    # 2. Картельный сговор: компании картеля постоянно участвуют вместе,
    #    проигравший всегда уступает на минимальную сумму
    for i in range(n_cartel):
        winner = CARTEL[i % len(CARTEL)]
        loser  = CARTEL[(i + 1) % len(CARTEL)]
        med    = random.uniform(500_000, 3_000_000)
        price  = med * random.uniform(0.97, 1.03)
        spec   = random.choice(SPEC_NORMAL)
        flags  = ["cartel_ip_match", "cartel_phone_match", "cartel_rotation"]
        rows.append(make_row(winner, loser, price, med, spec, flags))

    # 3. Аномально высокие цены (Isolation Forest поймает)
    for _ in range(n_price_anomaly):
        w, l = random.sample(LEGIT_COMPANIES, 2)
        med = random.uniform(50, 500)          # ручки/скрепки — дешёвый товар
        price = med * random.uniform(50, 200)  # цена завышена в 50–200 раз
        spec = "Поставка шариковых ручек, синяя паста, корпус прозрачный."
        flags = ["price_anomaly"]
        rows.append(make_row(w, l, price, med, spec, flags))

    # 4. «Заточенные» спецификации (NLP поймает)
    for i in range(n_tailored):
        winner = CARTEL[0]
        loser  = random.choice(LEGIT_COMPANIES)
        med    = random.uniform(2_000_000, 10_000_000)
        price  = med * random.uniform(0.98, 1.02)
        spec   = SPEC_TAILORED[i % len(SPEC_TAILORED)]
        flags  = ["tailored_spec"]
        rows.append(make_row(winner, loser, price, med, spec, flags))

    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df


if __name__ == "__main__":
    df = generate_tenders()
    df.to_csv("tenders.csv", index=False)
    print(f"✅ Сгенерировано {len(df)} тендеров")
    print(df[["tender_id", "winner_name", "price", "flags"]].head(10))
