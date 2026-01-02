from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os
from openpyxl.styles import Alignment, PatternFill, Font, Border, Side

app = Flask(__name__)
app.secret_key = 'care_web_secret_key_123'

# --- データベース設定 ---
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# RenderならPostgreSQL、自分のPC（ローカル）ならSQLiteというファイルに保存されます
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///care_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- データベースのテーブル定義（CSVの列と同じです） ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    care_manager = db.Column(db.String(100), nullable=False)
    care_level = db.Column(db.String(50), nullable=False)

# 起動時にデータベースを作成
with app.app_context():
    db.create_all()

SUPPORT_LEVELS = ["要支援１", "要支援２", "事業"]
CARE_LEVELS = ["要介護１", "要介護２", "要介護３", "要介護４", "要介護５"]

def is_logged_in():
    return session.get('logged_in')

# --- 各ルート機能（中身をSQL用に書き換えています） ---

@app.route('/')
def index():
    if not is_logged_in(): return redirect(url_for('login'))
    return render_template("form.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 固定のID/Passチェック
        if request.form['username'] == "admin" and request.form['password'] == "password123":
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return "ログイン失敗。やり直してください。<a href='/login'>戻る</a>"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route("/dashboard")
def dashboard():
    if not is_logged_in(): return redirect(url_for('login'))
    
    # 全データをデータベースから取得してDataFrameにする
    users = User.query.all()
    df = pd.DataFrame([(u.id, u.name, u.care_manager, u.care_level) for u in users], 
                      columns=["id", "name", "care_manager", "care_level"])

    if df.empty:
        # データが空の場合の表示用
        return render_template("dashboard.html", managers=[], matrix={}, counts={}, 
                               support_levels=SUPPORT_LEVELS, care_levels=CARE_LEVELS, 
                               subtotal_support={}, subtotal_care={}, grand_totals={}, 
                               row_totals={}, row_subtotal_support=0, row_subtotal_care=0, row_grand_total=0)

    managers = sorted(df["care_manager"].unique().tolist())
    all_levels = SUPPORT_LEVELS + CARE_LEVELS
    matrix = {l: {m: [] for m in managers} for l in all_levels}
    counts = {l: {m: 0 for m in managers} for l in all_levels}
    
    for _, row in df.iterrows():
        l, m = row["care_level"], row["care_manager"]
        if l in matrix and m in managers:
            matrix[l][m].append({"id": row["id"], "name": row["name"]})
            counts[l][m] += 1

    subtotal_support = {m: sum(counts[l][m] for l in SUPPORT_LEVELS) for m in managers}
    subtotal_care = {m: sum(counts[l][m] for l in CARE_LEVELS) for m in managers}
    grand_totals = {m: subtotal_support[m] + subtotal_care[m] for m in managers}
    row_totals = {l: sum(counts[l].values()) for l in all_levels}
    row_subtotal_support = sum(subtotal_support.values())
    row_subtotal_care = sum(subtotal_care.values())
    row_grand_total = sum(grand_totals.values())

    return render_template("dashboard.html", managers=managers, matrix=matrix, counts=counts,
                           support_levels=SUPPORT_LEVELS, care_levels=CARE_LEVELS,
                           subtotal_support=subtotal_support, subtotal_care=subtotal_care,
                           grand_totals=grand_totals, row_totals=row_totals,
                           row_subtotal_support=row_subtotal_support, row_subtotal_care=row_subtotal_care,
                           row_grand_total=row_grand_total)

@app.route("/submit", methods=["POST"])
def submit():
    if not is_logged_in(): return redirect(url_for('login'))
    new_user = User(name=request.form.get("name"), 
                    care_manager=request.form.get("care_manager"), 
                    care_level=request.form.get("care_level"))
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route("/delete/<int:user_id>")
def delete_user(user_id):
    if not is_logged_in(): return redirect(url_for('login'))
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route("/edit/<int:user_id>")
def edit_page(user_id):
    if not is_logged_in(): return redirect(url_for('login'))
    user = User.query.get(user_id)
    # idをuser_idとして渡す
    return render_template("edit.html", user=user, user_id=user.id)

@app.route("/update/<int:user_id>", methods=["POST"])
def update_user(user_id):
    if not is_logged_in(): return redirect(url_for('login'))
    user = User.query.get(user_id)
    if user:
        user.name = request.form.get("name")
        user.care_manager = request.form.get("care_manager")
        user.care_level = request.form.get("care_level")
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route("/rename_manager", methods=["POST"])
def rename_manager():
    if not is_logged_in(): return redirect(url_for('login'))
    old_name = request.form.get("old_name")
    new_name = request.form.get("new_name")
    if old_name and new_name:
        # 一括置換
        User.query.filter_by(care_manager=old_name).update({"care_manager": new_name})
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route("/download")
def download_excel():
    if not is_logged_in(): return redirect(url_for('login'))
    users = User.query.all()
    df = pd.DataFrame([(u.name, u.care_manager, u.care_level) for u in users], 
                      columns=["name", "care_manager", "care_level"])
    if df.empty: return "データが空です。"

    all_levels = SUPPORT_LEVELS + CARE_LEVELS
    pivot_names = df.pivot_table(index='care_level', columns='care_manager', values='name', 
                                aggfunc=lambda x: "\n".join(str(v) for v in x), fill_value="").reindex(all_levels).fillna("")
    pivot_counts = df.pivot_table(index='care_level', columns='care_manager', values='name', 
                                 aggfunc='count', fill_value=0).reindex(all_levels).fillna(0)
    
    pivot_names['社内合計'] = pivot_counts.sum(axis=1).astype(int).map(lambda x: f"{x}")
    pivot_counts['社内合計'] = pivot_counts.sum(axis=1)

    output_rows = []
    managers_with_total = pivot_names.columns.tolist()
    for level in all_levels:
        name_row = {m: pivot_names.loc[level, m] for m in managers_with_total}; name_row['区分'] = level
        output_rows.append(name_row)
        count_row = {m: f"{int(pivot_counts.loc[level, m])}名" for m in managers_with_total}; count_row['区分'] = f"{level} 人数"
        output_rows.append(count_row)

    grand_total_row = {'区分': '総合計'}
    for m in managers_with_total:
        total_val = pivot_counts[m].sum()
        grand_total_row[m] = f"{int(total_val)}名"
    output_rows.append(grand_total_row)

    final_df = pd.DataFrame(output_rows)
    final_df = final_df[['区分'] + managers_with_total]
    excel_file = "居宅支援名簿_完全集計版.xlsx"
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        final_df.to_excel(writer, index=False, sheet_name='名簿')
        ws = writer.sheets['名簿']
        header_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
        count_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
        total_fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
        thin = Side(border_style="thin", color="000000")
        border = Border(top=thin, left=thin, right=thin, bottom=thin)
        for row in ws.iter_rows(min_row=1, max_row=ws.max_row):
            for cell in row:
                cell.alignment = Alignment(wrapText=True, vertical='center', horizontal='center')
                cell.border = border
                if cell.row == 1:
                    cell.fill = header_fill; cell.font = Font(bold=True)
                label = str(ws.cell(row=cell.row, column=1).value)
                if "人数" in label: cell.fill = count_fill
                if "総合計" in label:
                    cell.fill = total_fill; cell.font = Font(bold=True)
                if cell.column == ws.max_column: cell.font = Font(bold=True)
    return send_file(excel_file, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)