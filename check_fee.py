# -*- coding: utf-8 -*-
"""check_fee.py — index.html 의 로컬 참조(script/link/img)가 repo 안에 실재하는지 본다.

fee 는 public repo 다. 다른 repo 경로·개인정보·드라이브 문자를 여기 쓰지 않는다.
이름이 `check_*` 글롭 안이라 루트 run_tests.py 에 자동 등재된다(EXTRA 불요)."""
from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent
INDEX = REPO / "index.html"

_LOCAL_ATTRS = {
    "script": "src",
    "link": "href",
    "img": "src",
}
_SKIP_PREFIXES = ("http:", "https:", "//", "data:", "#")


class _RefCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attr_name = _LOCAL_ATTRS.get(tag)
        if attr_name is None:
            return
        for name, value in attrs:
            if name != attr_name or not value:
                continue
            if value.startswith(_SKIP_PREFIXES):
                continue
            self.refs.append(value)


def main() -> int:
    if not INDEX.exists():
        print(f"index.html 없음: {INDEX}")
        print("check_fee FAIL 1건")
        return 1

    html = INDEX.read_text(encoding="utf-8")
    parser = _RefCollector()
    parser.feed(html)

    missing: list[str] = []
    for ref in parser.refs:
        path = urlsplit(ref).path  # 쿼리스트링·프래그먼트 제거
        if not path:
            continue
        target = (REPO / path).resolve()
        try:
            target.relative_to(REPO.resolve())
        except ValueError:
            missing.append(f"{ref} (repo 밖)")
            continue
        if not target.exists():
            missing.append(ref)

    if missing:
        for m in missing:
            print(f"참조 실종: {m}")
        print(f"check_fee FAIL {len(missing)}건")
        return 1

    print("check_fee PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
