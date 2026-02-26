# 介護事務所顧客管理システム
Flaskを使用したケアマネの顧客管理システム。GitHubでコードを管理し、Renderで24時間稼働するように設定。

### プレビュー用URL
Render URL [https://care-web-57ot.onrender.com](https://care-web-kio8.onrender.com)
（※無料枠のため読み込みに1分程度かかります。）

### 機能
- ログイン機能（初期設定ID: admin　初期設定PASS: password123）
- 顧客の新規登録
- 顧客情報の編集・削除
- 各ケアマネジャーの担当者数の計算と集計
- CSV出力

### 使用技術
- 言語/フレームワーク: Python / Flask
- データベース: PostgreSQL (Render上のDBを使用。SQLAlchemyで制御)
- Excel出力: Pandas と openpyxl を使用（社内合計・総合計、セル内改行、色分け設定済み）
- インフラ: Render (Web Service + Managed PostgreSQL)

### 実行方法
```bash
flask run app.py
```

### スクリーンショット
<img width="614" height="512" alt="スクリーンショット 2026-02-26 17 28 34" src="https://github.com/user-attachments/assets/ed12879b-7291-407a-a294-3ade8fb06263" />

<img width="973" height="780" alt="スクリーンショット 2026-02-26 17 28 47" src="https://github.com/user-attachments/assets/888de72d-2455-4965-97eb-a95c655f1d9d" />


<img width="705" height="501" alt="スクリーンショット 2026-02-26 17 29 11" src="https://github.com/user-attachments/assets/66a5983e-3ce3-4d98-800b-b4d6c5b1a561" />

