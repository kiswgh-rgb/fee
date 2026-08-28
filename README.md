# fee — 일일 습관 트래커 (정적 단일 HTML PWA)

세무사 수험 일지·일일 루틴을 모바일에서 기록하는 앱. 서버·빌드 없음 — `index.html` 하나.
데이터는 폰 브라우저 **localStorage** 에 쌓이고, 내보내기 JSON 은 짝 repo
**CHI_fee_data**(private)에 적층된다(앱=공개 / 데이터=비공개 분리).

- 개발 규약·불변식 정본: [CLAUDE.md](CLAUDE.md) — 특히 "버전업 시 기존 데이터 연속성"이 최우선.
- 데이터 소비처: inner_data(CHI 보고서) — 계보는 그쪽 소비맵이 갖는다.

(2026-08-28 — 초기 플레이스홀더 README 교체)
