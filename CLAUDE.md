# Fee — 일일 습관 트래커 (개발 규약)

세무사 수험 일지를 모바일에서 기록하는 정적 단일 HTML 앱(`index.html`).
데이터는 전부 폰 브라우저 **localStorage**에 쌓인다. 서버·빌드 없음.

---

## ⭐ 최우선 불변식 — 버전업 시 데이터 연속성

> **버전을 올려도 로컬에 이미 쌓인 기존 JSON 데이터를 그대로 재사용해 이어가야 한다.
> 버전업이 기존 데이터를 초기화하면 절대 안 된다.**

홈화면 웹클립은 service worker(network-first)로 매번 최신 `index.html`을 받아오지만,
**localStorage(일지 데이터)는 코드 교체와 무관하게 같은 저장칸에 그대로 남는다.**
따라서 새 버전 코드는 반드시 그 기존 데이터를 읽어 이어써야 한다.

### 데이터 초기화가 일어나는 유일한 조건
`loadConfig()`에서 **`itemsSignature`(항목 name:weight 조합) 불일치**가 감지될 때만
`day:*` / `legacy:*` / `total_liter` 등을 전부 지운다.
→ **항목(수면의식/저녁공부/케틀벨)·가중치를 바꾸면 = 전 데이터 삭제.** 의도 없이 절대 건드리지 말 것.

### CONFIG_VERSION 올리기는 안전
`CONFIG_VERSION` 문자열만 바꾸는 건 `c.version` 필드만 갱신할 뿐 데이터를 지우지 않는다.
버전업 시 체크리스트:
- ✅ `CONFIG_VERSION` 갱신 (+ `<title>`, `sw.js`의 `CACHE` 이름도 맞춰 올리면 캐시 깔끔)
- ❌ `DEFAULT_CONFIG.items` 배열(이름/가중치)은 건드리지 않기
- ✅ `loadConfig()` 마이그레이션 경로가 기존 데이터를 보존하는지 확인

---

## 절대 변경 금지 (데이터/스키마 호환성)
- localStorage 키 구조: `config` / `day:*` / `legacy:*` / `total_liter` / `legacy_cutoff` / `sync` (접두사 `fee_v10_`)
- JSON 스키마: `fee-record-1` (`collectRecord()` 생성, `applyRecord()` 소비)
- 항목 구성·가중치·통/리터 계산·달력 렌더링·기록 모달의 복사/반영(import) 로직

---

## 동기화 기능 (→ private 레포 CHI_fee_data)
- "동기화" 버튼: `collectRecord()`의 `fee-record-1` JSON을 GitHub Contents API로
  `CHI_fee_data/journal.json`에 PUT(전체 덮어쓰기). GET으로 sha 조회 후 충돌 없이 덮어씀.
- 설정(owner/repo/path/branch/**PAT**)은 localStorage 키 `sync`에만 저장.
  **PAT는 코드에 하드코딩 금지** — `fee` 레포는 public이라 유출 위험.
- 방향: 폰 → repo **한 방향**. 빈-데이터 가드 있음: 폰이 비었는데 repo에 데이터가 있으면 PUT 차단
  (빈 깡통으로 백업을 날리는 사고 방지). 복구는 GitHub의 journal.json을 복사해 "기록 → 반영".

## 제약
- `fetch` / `navigator.clipboard`는 HTTPS(github.io) 또는 localhost에서만 동작. `file://` 테스트 금지.
- 단일 사용자 개인용. 과도한 추상화/프레임워크 금지, 기존 vanilla JS 스타일 유지.
- 동기화 실패가 앱 기본 동작(체크/기록)을 막지 않게 할 것.
