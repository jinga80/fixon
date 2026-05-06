# FixOn ERP — 백엔드 이관 청사진

> 현재 localStorage 기반 단일 페이지 데모 → 본 운영 가능한 multi-tenant SaaS로 이관하는 90일 청사진
> 본 문서는 그래피 의사결정자에게 "이미 구체적이다"를 보여주는 자료

---

## 1. 아키텍처 한눈에

```
┌──────────────────────────────────────────────────────────────────────┐
│                            Cloud Edge                                 │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐   │
│  │  치과 PC  │     │ 기공소 PC │     │ 그래피MES│     │ 환자 모바일│   │
│  └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘   │
└───────┼─────────────────┼────────────────┼────────────────┼─────────┘
        │ HTTPS + JWT     │                │ mTLS+OAuth2    │
        └─────────┬───────┴────────────────┴────────────────┘
                  ▼
        ┌─────────────────────────┐
        │   API Gateway (Nginx)   │  rate limit, auth, logging
        └─────────┬───────────────┘
                  │
    ┌─────────────┼─────────────────────────────┐
    │             │                             │
    ▼             ▼                             ▼
┌────────┐  ┌────────┐                    ┌──────────┐
│ Web    │  │  API   │                    │ Webhook  │
│ Static │  │ Server │ (Node.js / Fastify) │ Worker   │
└────────┘  └───┬────┘                    └────┬─────┘
                │                              │
        ┌───────┴────────┐                     │
        ▼                ▼                     ▼
   ┌────────┐    ┌──────────────┐        ┌──────────┐
   │ Postgres│    │ S3 / 객체저장 │        │ Redis    │
   │ (RDB)   │    │ (STL/이미지)  │        │ Queue    │
   └─────────┘    └──────────────┘        └──────────┘
```

---

## 2. 기술 스택

| 레이어 | 선택 | 이유 |
|---|---|---|
| Frontend | 현 HTML/JS 그대로 (SPA 단일 파일) | 이미 작동, 재작성 불필요 |
| Auth | OAuth2 + JWT (RS256) | 표준, 확장 용이 |
| API | Node.js + Fastify (or NestJS) | TypeScript, 빠른 개발 |
| DB | PostgreSQL 16 | JSON 컬럼 + 강한 타입 시스템 |
| File | AWS S3 / Naver Cloud Object Storage | STL 영구 저장, 버전 관리 |
| Cache | Redis | 세션 + webhook queue |
| Realtime | Socket.IO 또는 Server-Sent Events | 알림 / 상태 동기화 |
| Hosting | AWS ap-northeast-2 (서울) 또는 Naver Cloud | 의료 데이터 국내 보관 (의료법 권고) |
| 모니터링 | Datadog 또는 자체 (Grafana+Loki) | SLA 추적 |
| CI/CD | GitHub Actions + ECS/Lambda | 자동 배포 |

---

## 3. 데이터 모델 (PostgreSQL DDL 초안)

```sql
-- 클리닉
CREATE TABLE clinics (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name         TEXT NOT NULL,
  doctor       TEXT,
  license_no   TEXT,
  region       TEXT,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- 환자 (PII 암호화)
CREATE TABLE patients (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id     UUID NOT NULL REFERENCES clinics(id),
  name_enc      BYTEA NOT NULL,           -- AES-256-GCM
  age           SMALLINT,
  sex           CHAR(1),
  note_enc      BYTEA,                    -- AES-256-GCM
  consent_v     TEXT NOT NULL,
  consent_at    TIMESTAMPTZ NOT NULL,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_patients_clinic ON patients(clinic_id);

-- 주문
CREATE TABLE orders (
  id              TEXT PRIMARY KEY,        -- 'ORD-YYYY-NNNN'
  clinic_id       UUID NOT NULL REFERENCES clinics(id),
  patient_id      UUID NOT NULL REFERENCES patients(id),
  status          TEXT NOT NULL,
  assigned_lab    UUID REFERENCES labs(id),
  assigned_graphy UUID REFERENCES graphy_accounts(id),
  -- UDI / Lot tracking (의료기기법)
  udi             TEXT NOT NULL,
  lot_no          TEXT NOT NULL,
  mfg_date        DATE NOT NULL,
  expiry_date     DATE NOT NULL,
  steril_lot      TEXT,
  -- Design
  nozzle_layout   TEXT,
  nozzle_teeth    JSONB,                   -- [46, 36, 45, 35]
  custom_nozzles  JSONB,                   -- [{pos, normal, fdi}]
  scan_data       JSONB,
  design_stl_url  TEXT,                    -- S3 URL
  design_stl_sha  TEXT,                    -- checksum
  -- Pricing
  pricing         JSONB NOT NULL,
  -- Tracking
  printer_id      TEXT,
  material_used   INT,
  qc_result       TEXT,                    -- pass/fail/null
  tracking_no     TEXT,
  -- KCD / coverage
  kcd_code        TEXT,
  coverage_type   TEXT,                    -- 급여/비급여
  -- Audit
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_clinic ON orders(clinic_id);
CREATE INDEX idx_orders_udi ON orders(udi);

-- 주문 이벤트 (timeline)
CREATE TABLE order_events (
  id          BIGSERIAL PRIMARY KEY,
  order_id    TEXT NOT NULL REFERENCES orders(id),
  status      TEXT NOT NULL,
  actor_role  TEXT NOT NULL,               -- clinic/lab/graphy/fixon
  actor_id    UUID,                        -- user
  note        TEXT,
  metadata    JSONB,
  at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_events_order ON order_events(order_id, at);

-- 알림
CREATE TABLE notifications (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  to_role      TEXT,
  to_user      UUID,
  message      TEXT NOT NULL,
  read         BOOLEAN DEFAULT false,
  at           TIMESTAMPTZ DEFAULT NOW()
);

-- QC 보고서
CREATE TABLE qc_reports (
  id             BIGSERIAL PRIMARY KEY,
  order_id       TEXT NOT NULL REFERENCES orders(id),
  inspector_id   UUID,
  result         TEXT NOT NULL,
  axes           JSONB,                    -- 6-axis grades
  notes          TEXT,
  certificate_url TEXT,
  at             TIMESTAMPTZ DEFAULT NOW()
);

-- 재고
CREATE TABLE inventory (
  sku        TEXT PRIMARY KEY,
  stock      INT NOT NULL DEFAULT 0,
  threshold  INT NOT NULL,
  unit       TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE inventory_movements (
  id        BIGSERIAL PRIMARY KEY,
  sku       TEXT REFERENCES inventory(sku),
  type      TEXT,                          -- in/out
  qty       INT NOT NULL,
  reason    TEXT,
  at        TIMESTAMPTZ DEFAULT NOW()
);

-- 접속 로그 (개인정보보호법 시행령 Art. 30, 1년 보관)
CREATE TABLE access_logs (
  id        BIGSERIAL PRIMARY KEY,
  user_id   UUID,
  endpoint  TEXT,
  method    TEXT,
  resource  TEXT,                          -- e.g. patient:UUID
  purpose   TEXT,
  at        TIMESTAMPTZ DEFAULT NOW(),
  ip        INET
);
CREATE INDEX idx_access_at ON access_logs(at);
```

---

## 4. 마이그레이션 스크립트

`localStorage` JSON → PostgreSQL 일괄 import:

```typescript
// scripts/migrate-from-localstorage.ts
import { Pool } from 'pg';
const pool = new Pool({ /* ... */ });

async function migrate(stateJson: string) {
  const state = JSON.parse(stateJson);

  // 1. clinics
  for (const c of state.clinics) {
    await pool.query(
      `INSERT INTO clinics(id,name,doctor,region) VALUES($1,$2,$3,$4) ON CONFLICT(id) DO NOTHING`,
      [c.id, c.name, c.doctor, c.region]
    );
  }

  // 2. patients (encrypt PII)
  for (const p of state.patients) {
    await pool.query(
      `INSERT INTO patients(id,clinic_id,name_enc,age,sex,note_enc,consent_v,consent_at)
       VALUES($1,$2,pgp_sym_encrypt($3,$8),$4,$5,pgp_sym_encrypt($6,$8),$7,NOW())`,
      [p.id, p.clinicId, p.name, p.age, p.sex, p.note || '', '1.0', process.env.PII_KEY]
    );
  }

  // 3. orders
  for (const o of state.orders) {
    await pool.query(`INSERT INTO orders(...) VALUES(...)`, [/* ... */]);
    for (const e of o.timeline) {
      await pool.query(`INSERT INTO order_events(...) VALUES(...)`, [/* ... */]);
    }
  }

  // 4. notifications, qc_reports, inventory
  // ...
}
```

전체 환자 데모 셋(7명) + 주문(13건) 마이그레이션 예상 시간: < 5초

---

## 5. 프론트엔드 변경 (최소화 원칙)

기존 11개 HTML 파일은 그대로 유지. 차이는 데이터 access 함수만 교체:

```js
// Before (localStorage)
function loadState() {
  return JSON.parse(localStorage.getItem('fixon-erp-state-v6'));
}
function saveState() {
  localStorage.setItem('fixon-erp-state-v6', JSON.stringify(state));
}

// After (REST API)
async function loadState() {
  const res = await fetch('/api/v1/state', { headers: { Authorization: `Bearer ${token}` } });
  return await res.json();
}
async function saveState(patch) {
  await fetch('/api/v1/state', { method:'PATCH', headers: {...}, body: JSON.stringify(patch) });
}
```

이 두 함수만 교체하면 ~95% 코드는 그대로 작동. **백엔드 이관 비용 매우 낮음.**

---

## 6. 보안 / 컴플라이언스 체크리스트

| 항목 | 의무 / 권장 | 구현 |
|---|---|---|
| TLS 1.3 (HTTPS) | 의무 | LB 단에서 종단 |
| PII 컬럼 암호화 | 의무 (개인정보보호법 시행령 Art. 30) | AES-256-GCM, AWS KMS / Naver Cloud KMS |
| 접속 로그 1년 보관 | 의무 | access_logs 테이블 + S3 cold |
| 의료기록 10년 보관 | 의무 (의료법 Art. 22) | orders + order_events 영구 보관 + S3 archive |
| 위탁계약 (FixOn↔치과/기공소) | 의무 (개인정보보호법 Art. 26) | 표준 위탁계약서 템플릿 |
| ISMS-P 인증 | 권장 | launch 후 6개월 내 |
| 의료기기 SW 인허가 | 본 ERP는 SW로 분류 안 됨 | 의료기기 자체(스플린트)는 제조 인허가 필요 |
| UDI 등록 (식약처) | 의무 (Class 2, 2024+) | 자체 UDI 발행 + 식약처 등록 |
| 백업 / DR | 권장 | 일일 자동 + 월별 cold + 분기 DR 훈련 |

---

## 7. 비용 추정 (월간, AWS 서울 기준)

| 항목 | 사양 | 월 비용 |
|---|---|---|
| EC2 (API) | t3.medium × 2 | ₩100,000 |
| RDS Postgres | db.t3.small (multi-AZ) | ₩200,000 |
| S3 (STL 보관) | 100GB + 전송 | ₩50,000 |
| ElastiCache Redis | cache.t3.micro | ₩40,000 |
| CloudFront | 100GB 전송 | ₩30,000 |
| Datadog | starter | ₩100,000 |
| **합계** | | **약 ₩520,000/월** |

치과 거래처 100개 + 일 100주문 가정 시 사용량 기준. 초기 (10거래처)는 절반 이하.

---

## 8. 90일 일정 (이관 + launch)

| 주차 | 작업 |
|---|---|
| W1-2 | 인프라 셋업 (AWS 계정 / VPC / RDS / S3 / IAM) |
| W3-4 | DB 스키마 + 핵심 endpoint 3개 (POST /orders, GET /stl, POST /events) |
| W5-6 | 프론트 access 함수 교체 + 인증 통합 |
| W7-8 | 마이그레이션 스크립트 + staging 환경 통합 테스트 |
| W9 | 그래피 webhook 통합 (양사 staging) |
| W10 | 부하 테스트 + 보안 점검 (취약점 스캔) |
| W11 | pilot 치과 1곳 + 그래피 1라인 |
| W12 | 본 launch 결정 + 모니터링 설정 |

---

## 9. 위험 및 완화

| 위험 | 가능성 | 영향 | 완화 |
|---|---|---|---|
| 의료법 해석 변경 | 낮음 | 높음 | 법무 자문 분기 |
| 그래피 측 API 미제공 | 중간 | 중간 | 폴백: 이메일/수동 import |
| 환자 PII 유출 | 매우 낮음 | 매우 높음 | 암호화 + 접속 로그 + ISMS-P |
| AWS 서울 장애 | 낮음 | 높음 | multi-AZ + 일일 백업 |
| 그래피 프린터 다운 | 중간 | 중간 | 상태 알림 자동화 + 외주 협력사 fallback |

---

## 10. 다음 액션

1. **그래피와 미팅 후 본 문서 회신** — API endpoint 제공 가능 여부 + 일정
2. **AWS / Naver Cloud 계정 발급** — D+1
3. **인프라 IaC (Terraform)** — D+7
4. **Postgres DDL 적용** — D+10
5. **첫 endpoint 배포** — D+21

생성: 2026-04-27
다음 갱신: 미팅 후 그래피 응답 반영
