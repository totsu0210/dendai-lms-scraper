"""
東京電機大学 LMS スクレイパー
Moodle ベースの LMS にログインし、登録コース一覧・コース内容を取得する。
"""

import os
import json
import argparse
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://lms.rd.dendai.ac.jp"


def create_session(username: str, password: str) -> requests.Session:
    """
    LMS にログインして認証済みセッションを返す。

    Args:
        username: LMS のユーザー名
        password: LMS のパスワード

    Returns:
        ログイン済みの requests.Session

    Raises:
        RuntimeError: ログインに失敗した場合
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    })

    # ログインページから CSRF トークンを取得
    resp = session.get(f"{BASE_URL}/login/index.php", timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    token_input = soup.find("input", {"name": "logintoken"})
    logintoken = token_input["value"] if token_input else ""

    resp = session.post(f"{BASE_URL}/login/index.php", data={
        "username": username,
        "password": password,
        "logintoken": logintoken,
        "anchor": "",
    }, timeout=15)
    resp.raise_for_status()

    if "ログアウト" not in resp.text and "logout" not in resp.text.lower():
        raise RuntimeError("ログイン失敗。ユーザー名・パスワードを確認してください。")

    return session


def get_enrolled_courses(session: requests.Session) -> list:
    """
    /my/courses.php から登録済みコース一覧を取得する。

    Args:
        session: ログイン済みセッション

    Returns:
        コース情報のリスト。各要素は以下のキーを持つ dict:
            - name      (str): コース名
            - url       (str): コースURL
            - course_id (int | None): コース ID
    """
    resp = session.get(f"{BASE_URL}/my/courses.php", timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    seen = set()
    courses = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/course/view.php" not in href:
            continue
        name = a.get_text(strip=True)
        if not name or href in seen:
            continue
        seen.add(href)

        course_id = None
        for part in href.split("?")[-1].split("&"):
            if part.startswith("id="):
                try:
                    course_id = int(part[3:])
                except ValueError:
                    pass

        courses.append({"name": name, "url": href, "course_id": course_id})

    return courses


def get_course_content(session: requests.Session, course_url: str) -> dict:
    """
    コースページからセクション・アクティビティ情報を取得する。

    Args:
        session:    ログイン済みセッション
        course_url: コースページの URL（絶対 or 相対）

    Returns:
        以下のキーを持つ dict:
            - course_name (str): コース名
            - url         (str): コース URL
            - sections    (list): セクションのリスト。各要素:
                - section    (str): セクション名
                - activities (list): アクティビティのリスト。各要素:
                    - type (str): モジュール種別 (quiz / resource / forum など)
                    - name (str): アクティビティ名
                    - url  (str): アクティビティ URL
    """
    if not course_url.startswith("http"):
        course_url = BASE_URL + course_url

    resp = session.get(course_url, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    h1 = soup.find("h1")
    course_name = h1.get_text(strip=True) if h1 else ""

    sections_data = []
    for sec in soup.find_all(["section", "li"], attrs={"data-sectionid": True}):
        heading_el = sec.find(["h3", "h2", "h4"], class_=["sectionname", "section-title"])
        heading = heading_el.get_text(strip=True) if heading_el else ""

        activities = []
        for act in sec.find_all(class_="activity"):
            name_el = act.find(class_="instancename")
            link_el = act.find("a", href=True)
            type_cls = [c for c in act.get("class", []) if c not in ["activity", "modtype_label"]]
            mod_type = type_cls[0].replace("modtype_", "") if type_cls else "unknown"
            name = name_el.get_text(strip=True) if name_el else ""
            url = link_el["href"] if link_el else ""
            if name:
                activities.append({"type": mod_type, "name": name, "url": url})

        sections_data.append({"section": heading, "activities": activities})

    return {"course_name": course_name, "url": course_url, "sections": sections_data}


def main():
    parser = argparse.ArgumentParser(
        description="東京電機大学 LMS のコース情報を取得します。"
    )
    parser.add_argument("--username", default=os.environ.get("LMS_USERNAME"),
                        help="LMS ユーザー名（環境変数 LMS_USERNAME でも可）")
    parser.add_argument("--password", default=os.environ.get("LMS_PASSWORD"),
                        help="LMS パスワード（環境変数 LMS_PASSWORD でも可）")
    parser.add_argument("--course-id", type=int,
                        help="詳細取得するコース ID（省略時はコース一覧のみ表示）")
    parser.add_argument("--output", default="output.json",
                        help="結果の保存先 JSON ファイル（デフォルト: output.json）")
    args = parser.parse_args()

    if not args.username or not args.password:
        parser.error(
            "ユーザー名とパスワードが必要です。\n"
            "  --username / --password オプション、\n"
            "  または環境変数 LMS_USERNAME / LMS_PASSWORD を設定してください。"
        )

    print("ログイン中...")
    session = create_session(args.username, args.password)
    print("ログイン成功\n")

    print("=== 登録コース一覧 ===")
    courses = get_enrolled_courses(session)
    for c in courses:
        print(f"  [{c['course_id']}] {c['name']}")

    result = {"courses": courses}

    if args.course_id:
        target = next((c for c in courses if c["course_id"] == args.course_id), None)
        if not target:
            print(f"\nコース ID {args.course_id} が見つかりませんでした。")
        else:
            print(f"\n=== コース内容: {target['name']} ===")
            content = get_course_content(session, target["url"])
            for sec in content["sections"]:
                if sec["section"] or sec["activities"]:
                    print(f"\n[{sec['section'] or '無題'}]")
                    for act in sec["activities"]:
                        print(f"  ({act['type']}) {act['name']}")
            result["content"] = content

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n結果を {args.output} に保存しました。")


if __name__ == "__main__":
    main()
