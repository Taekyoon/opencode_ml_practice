#!/usr/bin/env python3
"""research/wiki/ 건강 검진 도구 (Karpathy LLM Wiki Lint 연산의 로컬 구현).

검사 항목:
  1. index 미등록 페이지 — wiki에 있는데 index.md에 등록되지 않은 페이지
  2. 고아 페이지         — 다른 페이지가 링크하지 않는 페이지 (index/log 제외)
  3. broken 링크         — 내부 파일 링크 경로가 존재하지 않는 경우
  4. 오래된 데이터       — frontmatter `updated`가 7일 이상 지난 페이지

사용법: python scripts/wiki_lint.py [--days 7]
종료 코드: 문제 없으면 0, 1개 이상 발견하면 1
"""

import argparse
import os
import re
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIKI_DIR = os.path.join(PROJECT_ROOT, "research", "wiki")
INDEX_FILE = os.path.join(WIKI_DIR, "index.md")

LINK_RE = re.compile(r"\]\(([^)(]+\.md)\)")


def _all_pages() -> list[str]:
    """wiki/ 기준 상대 경로의 모든 .md 페이지 (index.md 제외)."""
    pages = []
    for root, _dirs, files in os.walk(WIKI_DIR):
        for f in files:
            if f.endswith(".md"):
                rel = os.path.relpath(os.path.join(root, f), WIKI_DIR)
                if rel != "index.md":
                    pages.append(rel)
    return sorted(pages)


def _is_broken_link(from_page: str, link: str) -> bool:
    """from_page (wiki/ 기준)에서의 상대 링크가 실제 존재하는지."""
    if link.startswith(("http://", "https://")):
        return False
    base = os.path.dirname(os.path.join(WIKI_DIR, from_page))
    target = os.path.normpath(os.path.join(base, link))
    return not os.path.exists(target)


def _internal_links(page: str) -> list[str]:
    full = os.path.join(WIKI_DIR, page)
    with open(full, encoding="utf-8") as f:
        content = f.read()
    return [l for l in LINK_RE.findall(content) if not l.startswith(("http://", "https://"))]


def _frontmatter_updated(page: str) -> str | None:
    full = os.path.join(WIKI_DIR, page)
    with open(full, encoding="utf-8") as f:
        head = f.read(2000)
    m = re.search(r"^updated:\s*([\d-]+)", head, re.MULTILINE)
    return m.group(1) if m else None


def main():
    parser = argparse.ArgumentParser(description="research/wiki 린트")
    parser.add_argument("--days", type=int, default=7, help="오래된 페이지 기준(일)")
    args = parser.parse_args()

    pages = _all_pages()
    problems = []

    # 1) index 미등록
    indexed = set()
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, encoding="utf-8") as f:
            indexed = {os.path.normpath(l) for l in LINK_RE.findall(f.read())}

    for p in pages:
        norm = os.path.normpath(p)
        if norm not in indexed:
            problems.append(f"[미등록] index.md 에 없음: {p}")

    # 2) 고아 페이지 (다른 페이지가 링크하지 않음) — index.md도 참조 페이지로 간주
    referenced = set()
    for p in pages + ["index.md"]:
        for link in _internal_links(p):
            base = os.path.dirname(p)
            referenced.add(os.path.normpath(os.path.join(base, link)))
    for p in pages:
        norm = os.path.normpath(p)
        if norm not in referenced:
            problems.append(f"[고아] 어떤 페이지도 링크하지 않음: {p}")

    # 3) broken 링크
    for p in pages:
        for link in _internal_links(p):
            if _is_broken_link(p, link):
                problems.append(f"[broken link] {p} -> {link}")

    # 4) 오래된 데이터
    stale = []
    for p in pages:
        upd = _frontmatter_updated(p)
        if not upd:
            continue
        try:
            d = datetime.strptime(upd, "%Y-%m-%d")
        except ValueError:
            continue
        if (datetime.now().date() - d.date()).days >= args.days:
            stale.append(p)

    if problems:
        print(f"wiki 린트 결과: {len(problems)} 개 문제 발견")
        for p in problems:
            print(f"  - {p}")
    else:
        print("wiki 린트 결과: 문제 없음")

    if stale:
        print(f"\n오래된 데이터 ({args.days}일+ 미갱신):")
        for p in stale:
            print(f"  [!] {p}")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())