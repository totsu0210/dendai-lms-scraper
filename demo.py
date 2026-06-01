"""
デモ用スクリプト
実行するとユーザー名・パスワードを対話入力し（パスワードは画面に表示されない）、
LMS からコース一覧と基礎確率論の内容を取得して表示する。
"""

import getpass
import sys
from scraper import create_session, get_enrolled_courses, get_course_content

DIVIDER = "─" * 48


def step(label: str):
    print(f"\n{'─' * 4} {label} {'─' * (42 - len(label))}")


def main():
    print(DIVIDER)
    print("  東京電機大学 LMS スクレイパー  デモ")
    print(DIVIDER)

    # 認証情報を対話入力（パスワードは getpass で非表示）
    print()
    username = input("ユーザー名: ")
    password = getpass.getpass("パスワード: ")   # ← 入力しても画面に出ない

    # ログイン
    step("1. ログイン")
    try:
        session = create_session(username, password)
    except RuntimeError as e:
        print(f"  エラー: {e}")
        sys.exit(1)
    print("  ✓ ログイン成功")

    # コース一覧
    step("2. 登録コース一覧を取得")
    courses = get_enrolled_courses(session)
    for c in courses:
        print(f"  [{c['course_id']:>4}] {c['name']}")

    # 基礎確率論を探す
    target = next(
        (c for c in courses if "確率" in c["name"] or "Prob" in c["name"]),
        None
    )
    if not target:
        print("\n  基礎確率論コースが見つかりませんでした。")
        sys.exit(0)

    # コース内容
    step(f"3. コース内容を取得: {target['name']}")
    content = get_course_content(session, target["url"])
    print(f"  コース名: {content['course_name']}\n")

    for sec in content["sections"]:
        if not sec["activities"]:
            continue
        print(f"  [{sec['section'] or '無題'}]")
        for act in sec["activities"]:
            icon = {"quiz": "📝", "resource": "📄", "forum": "💬", "hotquestion": "❓"}.get(act["type"], "•")
            print(f"    {icon} {act['name']}")
        print()

    print(DIVIDER)
    print("  デモ終了")
    print(DIVIDER)


if __name__ == "__main__":
    main()
