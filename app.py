from flask import Flask, render_template, request
from math import ceil
import os
from datetime import datetime

app = Flask(__name__)

def calculate_mailbox_upgrade(c, d, k, has_luxury, exchange_rate, initial_rubles=0, initial_luna=0):
    a = (d - c) // 10
    paid_expansions = max(0, a - k)
    start_idx = (c - 42) // 10 + 1
    end_idx = start_idx + paid_expansions - 1
    b = 10000 * sum(range(start_idx, end_idx + 1))
    remaining_rubles = max(0, b - initial_rubles)

    bonus_rubles_per_luna = 42 if has_luxury else 0
    ruble_gain_per_luna = exchange_rate * 0.65 + bonus_rubles_per_luna

    total_rubles_from_initial_luna = initial_luna * ruble_gain_per_luna
    effective_ruble_deficit = max(0, remaining_rubles - total_rubles_from_initial_luna)

    safe_required_luna = ceil(effective_ruble_deficit / ruble_gain_per_luna)

    theoretical_luna = 0
    while True:
        expected_rubles = theoretical_luna * ruble_gain_per_luna
        if expected_rubles >= effective_ruble_deficit:
            break
        theoretical_luna += 1

    delta_luna = safe_required_luna - theoretical_luna

    packs = [
        {"name": "A", "luna": 42, "price": 1100},
        {"name": "B", "luna": 142, "price": 3300},
        {"name": "C", "luna": 420, "price": 8500},
        {"name": "D", "luna": 1420, "price": 27000},
        {"name": "E", "luna": 4242, "price": 75000},
    ]

    remaining_luna = safe_required_luna
    pack_purchase = []
    total_cost = 0
    total_luna_bought = 0

    for pack in reversed(packs):
        count = remaining_luna // pack["luna"]
        if count > 0:
            total = count * pack["price"]
            total_cost += total
            total_luna_bought += count * pack["luna"]
            pack_purchase.append((pack["name"], count, total))
            remaining_luna -= count * pack["luna"]

    for pack in packs:
        if remaining_luna > 0:
            count = ceil(remaining_luna / pack["luna"])
            total = count * pack["price"]
            total_cost += total
            total_luna_bought += count * pack["luna"]
            pack_purchase.append((pack["name"], count, total))
            break

    unused_luna = total_luna_bought - safe_required_luna
    total_market_rubles = safe_required_luna * ruble_gain_per_luna

    return {
        "총 필요 루블": b,
        "기존 루블로 차감 후 필요 루블": remaining_rubles,
        "기존 루나 가치 차감 후 추가 루블 필요량": effective_ruble_deficit,
        "추가로 필요한 루나 (보수적 계산)": safe_required_luna,
        "이론상 최소 루나 (누적 환산 기준)": theoretical_luna,
        "보수적 루나 대비 차이": delta_luna,
        "표기 환율 (수수료 전) 루블/루나": exchange_rate,
        "환율 기준 총 거래 루블 (시장 내 거래량)": ceil(total_market_rubles),
        "총 구매 루나 수": total_luna_bought,
        "남는 루나 수": unused_luna,
        "구매 상품 목록": pack_purchase,
        "총 현질 비용 (₩)": total_cost
    }

def log_submission(data):
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] 입력값: {data}\n")

def read_logs():
    if os.path.exists("log.txt"):
        with open("log.txt", "r", encoding="utf-8") as f:
            return f.readlines()
    return []

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        c = int(request.form["current_size"])
        d = int(request.form["target_size"])
        k = int(request.form["hermes"])
        has_luxury = "luxury" in request.form
        exchange_rate = int(request.form["rate"])
        initial_rubles = int(request.form["initial_rubles"])
        initial_luna = int(request.form["initial_luna"])

        # 로그 저장
        log_submission(dict(request.form))

        result = calculate_mailbox_upgrade(c, d, k, has_luxury, exchange_rate, initial_rubles, initial_luna)
        form_data = request.form
    else:
        form_data = {}

    return render_template("index.html", result=result, form_data=form_data)

@app.route("/admin/logs")
def view_logs():
    logs = read_logs()
    return "<h2>로그 기록</h2><pre>{}</pre>".format("".join(logs))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
