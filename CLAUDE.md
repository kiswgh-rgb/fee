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

---

# v10.6 — 시험 진도(Study) 기능 설계

습관 트래커에 **세무사 수험 과목별 공부시간 추적**을 추가. 습관 데이터와 **완전 분리**.

## 화면 구조 — 하단 고정 탭바 + 뷰 라우터
- 고정 껍데기: 상단 날짜 헤더 + **공유 달력** + 하단 바 `F  S  Sync  ⚙`
- 교체 영역(달력 위 카드): **F**(습관, 기존 화면 그대로) ⇄ **S**(과목 4줄)
- `viewDate`(선택 날짜) 전역 공유 → 탭 전환해도 같은 날짜 유지, 달력만 뷰별로 재채색
- 라우터: `showView('habit'|'study')` 가 카드영역 토글 + 헤더 보조줄 교체 + 달력 재채색 + 바 활성표시
- 미래 탭(리포트/통계) = 바 버튼1 + 카드블록1 + render함수1 추가로 끝

## Study 데이터 모델 (습관 키와 별개, 접두사 `fee_v10_` 동일)
```
study_config            // { version, subjects[], hours_step:0.5, hours_min:0, hours_max:8,
                        //   density_map:{1:'하',2:'중',3:'상'}, exams:[{name:'1차',date:'2027-04-25'}] }
study:YYYY-MM-DD        // { hours:{ '세법학':2.5, ... }, density: 1|2|3|null }
```
- **시간은 과목 "이름(key)"으로 저장** — 과목 추가/삭제/순서변경에도 과거 기록 안 깨짐.
- 입력: ± 0.5 step, 0~8 clamp. 밀도: 하루 1개(전체), 단일선택.

## Study 마이그레이션 — 습관과 정반대(비파괴)
- 과목(subjects) 변경 시 **`study:*` 일별 기록 절대 삭제 안 함.**
- 빠진 과목의 과거 기록은 남고 화면에서만 숨김 / 새 과목은 빈 값 시작.
- **누적 공부시간은 모든 `study:*` 합산으로 항상 이어짐** (시그니처 기반 초기화 없음).
- 달력 색은 시간합 기반이라 과목이 바뀌어도 연속성 자동 유지.

## Study 달력 색 (습관 달력과 동일 팔레트 `densityStyle` 재사용)
```
농도 = min(1, (그날 시간합 × 밀도계수) / 기준)
  기준     = 평일(월~금) 4h, 주말(토·일) 8h
  밀도계수 = 하 0.8 / 중 1.0 / 상 1.2 / 미선택 1.0   (밀도 높을수록 색 진해짐)
```

## 동기화 — 2파일 (이름 변경)
| 데이터 | 파일 | 스키마 |
|---|---|---|
| 일일습관 | **`daily_routine.json`** (구 journal.json, 내용·스키마 무변경) | `fee-record-1` |
| 스터디 | **`semu_study.json`** | `semu-study-1` |
- 하단 바 **`Sync`** = 즉시 **올리기**(폰→repo, 2파일 각각 GET sha→PUT, 커밋 2개) + **토스트** 피드백.
- **`⚙` 설정 화면**: owner/repo/branch/PAT + 두 경로 + **⬆올리기 / ⬇복구** 두 버튼 + 마지막 동기화시각
  + 고급(원문 JSON 백업/복구, 파일별).
- 가드(양방향 덮어쓰기 보호):
  - 올리기: 폰이 비었는데 repo에 데이터 있으면 차단(파일별 독립).
  - 복구: 폰에 기록이 있는데 repo로 덮으면 확인창(기본 취소).
- `sync` 키 확장: `{ owner, repo, branch, pat, routine_path:'daily_routine.json', study_path:'semu_study.json' }`
  (구 `path:'journal.json'` 저장값은 로드 시 마이그레이션).

## 앱 이름/아이콘 (v10.6)
- `<title>` = `Fee v10.6`, 홈화면 라벨 = `Fee` (`apple-mobile-web-app-title`).
- 아이콘 = `icon-180.png` (파랑 #185FA5 배경 + 흰 `CHI`/`feedback`), `apple-touch-icon`.
- 아이콘·라벨은 **재등록 시점에 캐시** — 새로 보려면 홈화면 1회 재등록 필요.
