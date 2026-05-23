# Point Shower ERP — 시연 준비 구현 로그

> 기준 문서: `GRAPHY_DEMO_PLAN.md`
> 시작: 2026-04-27
> **모든 9개 항목 완료 ✅**

---

## 진행 상태 요약

| ID | 항목 | 상태 | 핵심 변경 |
|---|---|---|---|
| **§0 Demo-Blocking** |
| 0-① | `rescan_requested` 정식 편입 | ✅ | `STATUS_FLOW` + `STATUS_SIDETRACK` 분리, `statusProgressIdx()` 헬퍼, 모든 sub-page 확장 |
| 0-② | STATUS_LABEL 단일 source 통일 | ✅ | erp-mobile/analytics/quality 모두 main과 동일 12+1 라벨 |
| 0-③ | 디자이너 → 그래피 STL 자동 인계 | ✅ | `designerSave`가 통합 STL을 base64로 order에 첨부 + `downloadOrderSTL()` 그래피용 다운로드 버튼 |
| 0-④ | 시연용 시드 데이터 정비 | ✅ | 13번째 주문 추가(`rescan_requested`) + STORAGE_KEY v6 bump |
| **§4 Post-demo 30일** |
| 4-A | PII 마스킹 | ✅ | `patientName()`이 role+clinic 매칭 검사 후 `김OO → 김**` 마스킹. clinic 본인만 풀네임. PIPA Art. 28 대응 |
| 4-B | UDI/Lot 추적성 | ✅ | `genUDI()` 자동 생성 (GS1 format) + 주문 모달에 추적 카드 표시. 의료기기법 Class 2 대응 |
| 4-C | 그래피 연동 인터페이스 | ✅ | `INTEGRATION_GUIDE.md` 작성 — REST API 명세, OAuth/mTLS, webhook, 90일 마이그레이션 |
| 4-D | 백엔드 이관 청사진 | ✅ | `BACKEND_BLUEPRINT.md` — 아키텍처/스택/DDL/보안/비용/일정 |
| **§2 시연 전 체크** |
| 2 | 30분 체크리스트 자동화 | ✅ | `DEMO_CHECKLIST.html` — 자동 점검 (데이터/파일/성능/브라우저/환경) + prewarm + 데이터 초기화 |

---

## 구현 노트 (실시간)

### 2026-04-27

**0-①, 0-②** — 한 번에 처리:
- `STATUS_FLOW`(linear 12) + `STATUS_SIDETRACK`(rescan_requested) + `ALL_STATUSES` 분리
- `STATUS_PROGRESS = { rescan_requested: 1 }`로 진행률 매핑
- `statusProgressIdx(s)` 헬퍼: linear에 있으면 그대로, sidetrack은 매핑값 사용
- `window.STATUS_FLOW`, `window.STATUS_LABEL`, `window.statusProgressIdx` 노출 → onclick 핸들러 호환
- 모바일/분석/QC 페이지의 STATUS_LABEL 동일하게 통일
- 모바일 `advanceOrder`가 sidetrack 상태 진입 시 alert로 차단 ("데스크탑에서 처리하세요")

**0-③** — STL 자동 인계:
- `designerSave`에서 `THREE.Group` 생성 → splint + 모든 nozzle peg → `stlExporter.parse(binary)`
- ArrayBuffer → base64 (btoa) 변환해 `order.designSTL = {base64, sizeBytes, generatedAt, nozzleCount}` 저장
- 주문 모달에 `📦 출력용 STL 첨부됨 — XX KB · N분 전` 카드 + `⬇ 그래피 다운로드` 버튼
- `downloadOrderSTL(orderId)` 함수: base64 → Uint8Array → Blob → download

**0-④** — 시드 정비:
- 12개 주문이 12개 linear status에 1:1 분포 (이미 정렬됨)
- `ORD-2026-0013` 추가 → `rescan_requested` 상태 시연용
- `STORAGE_KEY 'pointshower-erp-state-v6'`로 bump (모든 sub-page에 sed로 일괄 적용)

**4-A** — PII 마스킹:
- `maskName(name)`: 한글/영문 첫 글자만 남기고 나머지 `*` 변환 (`김OO` → `김**`)
- `patientName(id)`: clinic role 본인 거래처 환자만 풀네임, 다른 모든 역할은 마스킹
- `state.currentRole` + `state.currentClinic` 조합 검사
- 환자 포털(erp-portal.html)도 동일 마스킹 정책 (이미 적용되어 있었음)

**4-B** — UDI/Lot:
- `genUDI(orderId, createdAt)`: GS1 형식 (`(01)08801234567890(11)YYMMDD(21)NNNN`) + lotNo `FX-YYYYMMDD-NNNN` + mfgDate + expiryDate(+5년) + sterilizationLot
- `mkOrder()` 자동 부여 — 모든 시드 주문이 UDI 보유
- `consentVersion`, `consentAt` 필드 추가 (PIPA 동의 메타)
- 주문 모달 `<od-block>` 추가: UDI / Lot / 제조일 / 유효기한 / 멸균 Lot 5행 카드
- 의료기기법 Art. 31 (Class 2 추적관리) 대응

**4-C, 4-D** — 문서화:
- `INTEGRATION_GUIDE.md`: 양사 통합 명세, REST API 4개, 보안/SLA, 90일 마이그 일정, 비통합 폴백
- `BACKEND_BLUEPRINT.md`: 아키텍처 다이어그램, 기술 스택, Postgres DDL, 마이그레이션 스크립트, 보안 체크리스트, 비용 추정, 12주 일정

**§2 자동 점검 + file:// 호환 패치** — `DEMO_CHECKLIST.html`:
- 초기 fetch HEAD 방식이 file:// 환경에서 CORS로 차단되는 문제 해결
- `checkFileExists()` — `<iframe>` 의 onload/onerror 활용 (file:// OK), 3초 timeout
- `<script src="samples/stl-data.js">` 를 HEAD에 사전 로드 (window.__SAMPLE_STL 즉시 사용)
- localStorage 미로드 시 친절한 안내 + "🔄 자동 수정 시도" 버튼
- `resetAndOpenERP()` — 초기화 → erp.html auto-open → storage 이벤트로 자동 재점검 (3.5s fallback)
- 환경 감지 배너 + 진행률 바
- 자동 검증 항목 ~16개:
  - 데이터: localStorage v6, 12+1 상태 분포, rescan_requested 시드, UDI, 환자/거래처
  - 파일: 12개 sub-page (iframe load — file:// 호환)
  - 성능: localStorage 사이즈
  - 자산: STL 인라인 데이터 (samples/stl-data.js)
  - 브라우저: importmap, clipboard, WebGL
  - 환경: 화면 해상도, 네트워크
- 점수 표시 (100% 시 "시연 시작 →" 버튼 활성)
- "🔄 시연용 데이터 초기화 + ERP 열기" — storage key 정리 → erp.html 자동 오픈 → storage 이벤트 감지 후 자동 재점검
- "🔥 prewarm" — file:// 환경에선 iframe, HTTP에선 fetch로 사전 로드
- erp.html 사이드바에 "🚦 시연 점검" 진입점 추가
- 실패 항목에 "🔄 자동 수정 시도" 버튼 (fixAction='reset' 항목)
- 환경 감지 배너 (file:// vs HTTP) + 진행률 바

---

## 파일 인벤토리 (최종)

| 파일 | 사이즈 | 용도 |
|---|---|---|
| `erp.html` | 196KB | 메인 ERP (역할 4개, 페이지 21개+) |
| `erp-analytics.html` | 17KB | 분석 대시보드 |
| `erp-messages.html` | 14KB | 메시지 hub |
| `erp-reports.html` | 20KB | 리포트 생성기 |
| `erp-quality.html` | 19KB | QC 센터 |
| `erp-mobile.html` | 17KB | 모바일 컴패니언 |
| `erp-help.html` | 25KB | 도움말 / 가이드 |
| `erp-inventory.html` | 9.7KB | 재고 관리 |
| `erp-calendar.html` | 9.6KB | 캘린더 |
| `erp-portal.html` | 10KB | 환자 포털 |
| `erp-search.html` | 9.5KB | 통합 검색 |
| `erp-workflow.html` | 11KB | 자동화 규칙 |
| `DEMO_CHECKLIST.html` | 11KB | **시연 전 자동 점검 (신규)** |
| `point-shower-patient.html` | ~30KB | **환자용 제품 브로셔 — STL 3D 렌더 + SVG 도식 + 새 카테고리 정의** |
| `BRAND_DEFINITION.md` | ~6KB | **제품 정의 / 브랜딩 워킹 도큐먼트 (살아있는 문서)** |
| `GRAPHY_DEMO_PLAN.md` | 10KB | 시연 준비 마스터 문서 |
| `INTEGRATION_GUIDE.md` | 7.4KB | **그래피 연동 명세 (신규)** |
| `BACKEND_BLUEPRINT.md` | 12.8KB | **백엔드 청사진 (신규)** |
| `IMPLEMENTATION_LOG.md` | 이 문서 | 작업 연속성 추적 |

---

## 시연 D-day 권장 흐름

```
T-30분  →  DEMO_CHECKLIST.html 실행 → 100% 통과 확인
            ↓
T-25분  →  prewarm 클릭 → 12개 페이지 사전 로드 (폰트/STL 캐시)
            ↓
T-20분  →  데이터 초기화 → erp.html 1회 열어 시드 생성
            ↓
T-15분  →  GRAPHY_DEMO_PLAN.md 시나리오 5장면 마지막 리허설
            ↓
T-5분   →  관계자 자리 정리, 화면 미러링 점검
            ↓
T = 0   →  미팅 시작 → 시나리오 1~5 실행 (10분)
            ↓
T+10분  →  Q&A → 답변 골격 활용 → INTEGRATION_GUIDE.md 양도
            ↓
T+30분  →  마무리 → BACKEND_BLUEPRINT.md 후속 자료로 전달
```

---

## 2026-04-28 갱신 — 제품 카테고리 재정의

**핵심 인사이트** (사용자 제공):
- Point Shower ≠ 워터픽 (수동 분사기) ≠ 일반 마우스피스 (정적 보호)
- Point Shower = "맞춤 트레이 + 카트리지 + 정밀 도포" 의 새로운 카테고리
- 3-tier 모드: Daily(세척) / Wellness(잇몸 케어) / Medical(약제 처방)

**새로 만들/갱신된 자료**:
- `BRAND_DEFINITION.md` — 제품 정의/포지셔닝/브랜드 톤/3-tier 모드/열린 질문 정리. 살아있는 문서로 계속 갱신.
- `point-shower-patient.html` 전면 재작성:
  - Hero 섹션에 실제 STL(splint_base) **Three.js 3D 렌더링** (자동 회전)
  - Definition 섹션 (다크) — 워터픽 vs 마우스피스 vs Point Shower 3카드
  - 작동 원리 섹션 — SVG 치아+노즐 도식 (FDI 표기) + 4단계
  - 3-tier 모드 카드 (Daily/Wellness/Medical) — 카트리지/처방/분류/시간 비교
  - **STL 갤러리** — 8종 splint variants (실제 환자 데이터 기반) 모두 인라인 3D 렌더
  - 4-way 비교표 (워터픽 / 마우스피스 / Point Shower)
  - 안전 정보를 모드별 분류 (Medical만 Class 2)
- 기존 file:// 환경 호환 — `samples/stl-data.js` 사전 로드로 fetch 없이 STL 렌더 가능

**열린 질문** (계속 결정해 가야):
- 카트리지 일회용 vs 리필
- 작동 시간 표준화
- 모드별 가격 정책
- 의약품 카트리지 = 누가 공급?

---

## 후속 액션 (미팅 후)

1. 그래피 응답 수신 시 `INTEGRATION_GUIDE.md` §8 항목 채우기
2. 본 계약 시 `BACKEND_BLUEPRINT.md` §8 일정 적용 → 90일 launch 추진
3. 미해결 백로그 (선택적, 본 계약 후):
   - ARIA 키보드 접근성 전면 개편
   - 공통 utility 추출 (`erp-shared.js`)
   - URL deep-linking 통합 (`?order=XXX`)
   - 프린트 품질 보강 (erp-quality KPI dark bg fix)
   - i18n 준비 (인벤토리 키 영문화)
   - WebGL context leak 수정 (인라인 미리보기 dispose)

---

생성: 2026-04-27
모든 demo-blocking + post-demo 30일 항목 완료
다음 갱신: 그래피 미팅 D+1
