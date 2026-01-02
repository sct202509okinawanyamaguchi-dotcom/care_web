from flask import Flask, render_template, request, send_file, redirect, url_for
import pandas as pd
import os

app = Flask(__name__)

DATA_FILE = "data/users.csv"
if not os.path.exists("data"):
    os.makedirs("data")

if not os.path.exists(DATA_FILE):
    df_init = pd.DataFrame(columns=["name", "care_manager", "care_level"])
    df_init.to_csv(DATA_FILE, index=False, encoding="utf-8")

# 区分グループの定義
SUPPORT_LEVELS = ["要支援１", "要支援２", "事業"]
CARE_LEVELS = ["要介護１", "要介護２", "要介護３", "要介護４", "要介護５"]

@app.route("/")
def index():
    return render_template("form.html")

@app.route("/dashboard")
def dashboard():
    if not os.path.exists(DATA_FILE):
        return "データファイルがありません。"

    df = pd.read_csv(DATA_FILE)
    managers = sorted(df["care_manager"].unique().tolist())
    all_levels = SUPPORT_LEVELS + CARE_LEVELS

    # 1. マトリックスデータ（名前リスト）の作成
    matrix = {l: {m: [] for m in managers} for l in all_levels}
    # 2. カウントデータ（人数）の作成
    counts = {l: {m: 0 for m in managers} for l in all_levels}
    
    for idx, row in df.iterrows():
        l, m = row["care_level"], row["care_manager"]
        if l in matrix and m in managers:
            matrix[l][m].append({"id": idx, "name": row["name"]})
            counts[l][m] += 1

    # 3. 集計（小計・合計）の計算
    subtotal_support = {m: sum(counts[l][m] for l in SUPPORT_LEVELS) for m in managers}
    subtotal_care = {m: sum(counts[l][m] for l in CARE_LEVELS) for m in managers}
    grand_totals = {m: subtotal_support[m] + subtotal_care[m] for m in managers}

    # 行ごとの合計（一番右の列用）
    row_totals = {l: sum(counts[l].values()) for l in all_levels}
    row_subtotal_support = sum(subtotal_support.values())
    row_subtotal_care = sum(subtotal_care.values())
    row_grand_total = sum(grand_totals.values())

    return render_template(
        "dashboard.html",
        managers=managers,
        matrix=matrix,
        counts=counts,
        support_levels=SUPPORT_LEVELS,
        care_levels=CARE_LEVELS,
        subtotal_support=subtotal_support,
        subtotal_care=subtotal_care,
        grand_totals=grand_totals,
        row_totals=row_totals,
        row_subtotal_support=row_subtotal_support,
        row_subtotal_care=row_subtotal_care,
        row_grand_total=row_grand_total
    )

@app.route("/submit", methods=["POST"])
def submit():
    df = pd.read_csv(DATA_FILE)
    new_row = {
        "name": request.form.get("name"),
        "care_manager": request.form.get("care_manager"),
        "care_level": request.form.get("care_level"),
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False, encoding="utf-8")
    return redirect(url_for('dashboard')) # 保存後はダッシュボードへ

@app.route("/delete/<int:user_id>")
def delete_user(user_id):
    df = pd.read_csv(DATA_FILE)
    df = df.drop(df.index[user_id]).reset_index(drop=True)
    df.to_csv(DATA_FILE, index=False, encoding="utf-8")
    return redirect(url_for('dashboard'))

@app.route("/edit/<int:user_id>")
def edit_page(user_id):
    df = pd.read_csv(DATA_FILE)
    user_data = df.iloc[user_id].to_dict()
    return render_template("edit.html", user=user_data, user_id=user_id)

@app.route("/update/<int:user_id>", methods=["POST"])
def update_user(user_id):
    df = pd.read_csv(DATA_FILE)
    df.at[user_id, "name"] = request.form.get("name")
    df.at[user_id, "care_manager"] = request.form.get("care_manager")
    df.at[user_id, "care_level"] = request.form.get("care_level")
    df.to_csv(DATA_FILE, index=False, encoding="utf-8")
    return redirect(url_for('dashboard'))

@app.route("/rename_manager", methods=["POST"])
def rename_manager():
    old_name = request.form.get("old_name")
    new_name = request.form.get("new_name")
    
    if old_name and new_name:
        df = pd.read_csv(DATA_FILE)
        # 指定されたケアマネ名を一括で書き換え
        df["care_manager"] = df["care_manager"].replace(old_name, new_name)
        df.to_csv(DATA_FILE, index=False, encoding="utf-8")
        
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.run(debug=True)