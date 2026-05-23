# Point Shower × Graphy 시스템 연동 가이드

> 그래피 측 의사결정자/엔지니어가 30분 안에 read하고 통합 가능 여부 판단
> 본 문서는 PoC 데모 → 실 운영 환경 이관을 위한 인터페이스 명세

---

## 1. 통합 시나리오 한눈에

```
┌──────────────┐  ① 신규 주문   ┌────────────┐  ② STL 인계   ┌────────────┐
│  Point Shower ERP   │  POST /orders  │ Graphy MES │ ⬇ pull/push  │ Graphy 프린터│
│ (web/SaaS)   │ ──────────────▶│ (생산관리) │ ────────────▶│  (Tera Harz)│
└──────────────┘                └────────────┘               └────────────┘
       ▲                              │                            │
       │  ④ 정산 데이터          ③ 상태 webhook                 ⑤ 완료 ack
       └──────────────────────────────┴────────────────────────────┘
```

| 단계 | Point Shower → Graphy | Graphy → Point Shower |
|---|---|---|
| ① | 주문 발생 (JSON) | — |
| ② | STL Binary (per-order) | — |
| ③ | — | 상태 webhook (printing/qc/shipping) |
| ④ | 정산 명세 PDF | — |
| ⑤ | — | 완료 ack + UDI 확정 |

---

## 2. REST API 명세 (Point Shower 측 제공)

베이스 URL: `https://api.pointshower.example/v1` (예시)

### `POST /orders` — 신규 주문 푸시 (Point Shower → Graphy)
주문 등록 시 Graphy 측 endpoint로 호출. Graphy가 자체 API endpoint를 제공하면 Point Shower이 webhook으로 push.

**Request body**:
```json
{
  "orderId": "ORD-2026-0011",
  "createdAt": "2026-04-27T08:30:00+09:00",
  "clinic": {
    "id": "clinic-001",
    "name": "올리브서울치과",
    "doctor": "이중우",
    "license": "면허번호-XXXXX"
  },
  "patient": {
    "id": "P-003",
    "displayName": "박**",
    "age": 45,
    "sex": "M",
    "consentVersion": "1.0",
    "consentAt": "2026-04-27T08:30:00+09:00"
  },
  "scan": {
    "method": "intraoral",
    "scanner": "Medit i700",
    "arch": "lower",
    "fileFormat": "stl",
    "uploadedAt": "..."
  },
  "design": {
    "nozzleLayout": "standard",
    "nozzleTeeth": [46, 36, 45, 35],
    "stlUrl": "https://api.pointshower.example/v1/orders/ORD-2026-0011/stl",
    "stlSize": 750000,
    "stlChecksum": "sha256:..."
  },
  "tracking": {
    "udi": "(01)08801234567890(11)260427(21)0011",
    "lotNo": "FX-20260427-0011",
    "mfgDate": "2026-04-27",
    "expiryDate": "2031-04-27",
    "deviceClass": "Class 2 의료기기"
  },
  "pricing": {
    "base": 280000,
    "graphyShare": 110000,
    "currency": "KRW"
  },
  "kcdCode": null,
  "coverageType": "비급여"
}
```

### `GET /orders/{orderId}/stl` — 출력용 STL 다운로드
- Auth: Bearer token
- Returns: `application/octet-stream` (binary STL)
- Headers: `X-Point Shower-UDI`, `X-Point Shower-LotNo`, `X-Point Shower-Checksum`

### `POST /orders/{orderId}/status` — 상태 업데이트 (Graphy → Point Shower webhook)
Graphy 측에서 인쇄/조립/QC/배송 단계마다 호출.

**Request**:
```json
{
  "status": "printing|assembling|qc|shipping",
  "at": "2026-04-27T10:00:00+09:00",
  "actor": "graphy",
  "note": "PRN-01 배정",
  "metadata": {
    "printerId": "PRN-01",
    "materialUsedG": 32,
    "qcReport": { "result": "pass", "axes": {...} }
  }
}
```

### `POST /orders/{orderId}/complete` — 완료 + UDI 확정
Graphy가 배송을 완료하면 호출. 실제 측정된 데이터를 Point Shower에 회신.

```json
{
  "trackingNo": "CJ123456789KR",
  "shippedAt": "2026-04-27T16:00:00+09:00",
  "actualLot": "FX-20260427-0011-01",
  "qcCertUrl": "https://...",
  "udiVerified": true
}
```

---

## 3. 인증 / 보안

- **Auth**: OAuth 2.0 client_credentials grant + mTLS 권장
- **Scopes**: `orders:read`, `orders:write`, `stl:download`, `webhook:receive`
- **Rate limit**: 1000 req/min per client
- **PII 정책**:
  - 환자 displayName은 항상 마스킹 (`김**`) — 풀네임 전송 금지
  - 진단 정보(KCD)는 별도 동의 후 전송
  - 모든 요청 로깅: `clientId`, `endpoint`, `timestamp`, `orderId`
  - 개인정보 접속 기록 1년 보관 (개인정보보호법 시행령 Art. 30)

---

## 4. 데이터 모델 매핑

현재 Point Shower ERP의 `localStorage` 스키마 → 향후 RDB 매핑

| Local 객체 | RDB 테이블 | 주요 컬럼 |
|---|---|---|
| `state.orders[]` | `orders` | id, clinic_id, patient_id, status, udi, lot_no, mfg_date, expiry_date, created_at |
| `state.orders[].timeline[]` | `order_events` | id, order_id, status, actor, note, at |
| `state.orders[].pricing` | `order_pricing` | order_id, base, lab_share, graphy_share, pointshower_fee |
| `state.orders[].customNozzles[]` | `nozzle_placements` | order_id, fdi, pos_x/y/z, normal_x/y/z |
| `state.orders[].designSTL` | object storage (S3) | URL referenced from orders.design_stl_url |
| `state.patients[]` | `patients` | id, clinic_id, name (encrypted), age, sex, note (encrypted), consent_version, consent_at |
| `state.clinics[]` | `clinics` | id, name, doctor, license, region |
| `state.labs[]` | `labs` | id, name, region, avg_hours |
| `state.notifications[]` | `notifications` | id, to_role, to_user, message, at, read |

전 컬럼 중 `name`, `note` 등 PII는 **field-level encryption** (AES-256-GCM, KMS 관리 키).

---

## 5. 마이그레이션 계획 (90일)

### D-30 ~ D 0 (계약 ~ kickoff)
- 양사 기술 미팅 1회 (2시간)
- API 명세 합의서 서명
- 그래피 측 staging endpoint 구축
- mTLS 인증서 교환

### D+1 ~ D+30
- Point Shower 백엔드 (Node.js/Postgres) 1차 구축
- localStorage → DB 마이그레이션 스크립트
- 핵심 endpoint 3개 우선 (POST /orders, GET /stl, POST /status)
- staging에서 양사 통합 테스트

### D+31 ~ D+60
- 정산 + UDI verification + 알림 endpoint 추가
- 부하 테스트 (1000 orders/day 가정)
- ISMS-P 사전 진단

### D+61 ~ D+90
- 1개 시범 치과 + 그래피 1개 라인 pilot
- 실 환자 1~2건 (모의 환자) 처리
- 본 launch 결정

---

## 6. SLA 초안

| 항목 | 목표 | 측정 |
|---|---|---|
| API 가용성 | 99.5% | monthly uptime |
| 응답 시간 (p95) | < 500ms | endpoint별 |
| webhook 재시도 | 3회 (exponential backoff) | 최대 1시간 내 전송 보장 |
| 데이터 손실 | 0% | event log + S3 versioning |
| 복구 시간 (RTO) | < 4시간 | DR 시나리오 훈련 분기별 |
| 데이터 보관 | 10년 (의료법) | cold storage 자동 이관 |

---

## 7. 비통합 운영 폴백

만약 실시간 연동이 어려운 경우:
- **반자동 모드**: Point Shower에서 STL+JSON 수동 다운로드 → 그래피 시스템에 수동 import
- **이메일 모드**: 주문 발생 시 자동 이메일 (.zip 첨부) → 그래피 담당자 수동 처리
- 두 모드 모두 현재 시스템에서 즉시 가능 (별도 개발 불요)

---

## 8. 연락 / 후속 일정

- 본 문서 작성: Point Shower × 이중우
- 그래피 답변 요청 항목:
  1. API 수신 endpoint 제공 가능 여부
  2. mTLS 인증서 교환 가능 여부
  3. 자체 PMS/MES와의 연동 부서 연락처
- 협의 마감: 미팅 D+7
- 다음 단계: 양사 기술 ~~kickoff~~ 일정 확정

생성: 2026-04-27
