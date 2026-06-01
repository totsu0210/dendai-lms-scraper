# dendai-lms-scraper

東京電機大学 LMS（Moodle）にログインし、登録コース一覧とコース内容を取得するスクレイパーです。

## 機能

- 登録済みコース一覧の取得（`/my/courses.php`）
- コースのセクション・アクティビティ情報の取得
- 結果を JSON ファイルに出力

## セットアップ

```bash
# 依存パッケージのインストール
pip install -r requirements.txt
```

## 使い方

### 環境変数で認証情報を渡す（推奨）

```bash
# .env.example をコピーして認証情報を記入
cp .env.example .env

# .env を読み込んで実行
export $(cat .env | xargs) && python scraper.py
```

### コマンドライン引数で渡す

```bash
python scraper.py --username YOUR_USERNAME --password YOUR_PASSWORD
```

### 特定コースの詳細も取得する

```bash
# --course-id にコース ID を指定（コース一覧表示後に確認可能）
python scraper.py --username YOUR_USERNAME --password YOUR_PASSWORD --course-id 333
```

### 出力ファイルを指定する

```bash
python scraper.py --username YOUR_USERNAME --password YOUR_PASSWORD --output result.json
```

## 出力形式

```json
{
  "courses": [
    { "name": "Prob2026", "url": "https://...", "course_id": 333 }
  ],
  "content": {
    "course_name": "基礎確率論",
    "url": "https://...",
    "sections": [
      {
        "section": "第8回",
        "activities": [
          { "type": "quiz", "name": "予習課題：期待値小テスト", "url": "https://..." }
        ]
      }
    ]
  }
}
```

## ライブラリとして使う

```python
from scraper import create_session, get_enrolled_courses, get_course_content

session = create_session("username", "password")

# コース一覧
courses = get_enrolled_courses(session)

# 特定コースの内容
content = get_course_content(session, "https://lms.rd.dendai.ac.jp/course/view.php?id=333")
```
