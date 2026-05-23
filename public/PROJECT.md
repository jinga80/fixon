# lander 프로젝트 현황

이 문서는 `/Users/jin/lander` 에서 진행 중인 작업의 연속성을 위한 기록입니다.

---

## 디렉토리 구조

```
/Users/jin/lander/
├── point-shower/          # [메인] Point Shower 3D 조립 뷰어
│   ├── stl_viewer.html    # Three.js 기반 메인 뷰어 (1380줄)
│   ├── splint0306.stl     # 스플린트 3D 모델 (19MB, 388K 삼각형)
│   ├── nozzle0306_bin.stl # 노즐 3D 모델 (4.5MB, 바이너리)
│   ├── tubetip.stl        # 튜브팁 3D 모델 (466KB)
│   ├── point-shower-어댑터.stp    # 어댑터 STEP 파일
│   ├── splint_adapter.json# 현재 부품 배치 데이터 (6개 부품)
│   ├── point-shower-logo.jpg      # Point Shower 로고 (애니메이션 인트로용)
│   ├── point-shower-banner3.jpg   # 배너 이미지
│   ├── point-shower-결합사진.jpg  # 제품 결합 참고사진
│   ├── point-shower-분리사진.jpg  # 제품 분리 참고사진
│   ├── convert_to_mp4.sh  # WebM→MP4 변환 스크립트
│   ├── PointShower동영상.docx # 원본 요구사항 문서
│   └── output/            # 렌더링 결과물
│       ├── assembly-2026-04-16.mp4
│       ├── assembly-2026-04-16.webm
│       └── assembly-2026-04-20.mp4
│
├── mesh-motion/           # 3D 메쉬 모션그래픽 도구
│   ├── mesh_motion.py     # STL/OBJ → MP4 변환 파이썬 스크립트
│   └── output/
│       └── korean_portrait.mp4  # 한국인 테마 결과물
│
├── sidex-2026/            # SIDEX 2026 그래피 부스 강연 준비
│   ├── README.md          # 행사 정보 + 체크리스트
│   ├── booth/             # 부스 시안 PDF
│   ├── lecture/           # 강연 구성안, PPT, 스크립트
│   └── media/             # 영상/이미지 자산
│
├── .venv/                 # Python 3.13 가상환경 (pyvista, trimesh 등)
└── PROJECT.md             # 이 파일
```

---

## 1. Point Shower 조립 뷰어 (`point-shower/`)

### 개요
Aquapick 구강세정기용 **Point Shower 스플린트 어셈블리**를 3D로 시각화하고, 조립 애니메이션 영상을 생성하는 웹 기반 뷰어.

- **의뢰인**: 이중우 대표님
- **제품**: 투명 스플린트 + 노즐 4개 + 어댑터 1개 + 튜브팁 1개

### 기술 스택
- Three.js r170 (3D 렌더링)
- occt-import-js v0.0.23 (STEP 파일 파싱)
- mp4-muxer v5.1.3 (브라우저 내 MP4 생성)
- WebCodecs API + MediaRecorder API (녹화)

### 실행 방법
```bash
cd /Users/jin/lander/point-shower
python3 -m http.server 8080
open http://localhost:8080/stl_viewer.html
```

### 부품 목록 (6개)
| # | 부품 | 파일 | 색상 | 키 |
|---|------|------|------|-----|
| 1 | 노즐 빨강 | nozzle0306_bin.stl | #ff6644 | `1` |
| 2 | 노즐 초록 | nozzle0306_bin.stl | #44cc66 | `2` |
| 3 | 노즐 파랑 | nozzle0306_bin.stl | #4488ff | `3` |
| 4 | 노즐 노랑 | nozzle0306_bin.stl | #ffcc22 | `4` |
| 5 | 어댑터 | point-shower-어댑터.stp | #44aadd | `5` |
| 6 | 튜브팁 | tubetip.stl | #eeeeee (불투명 흰) | `6` |

### 배치 데이터 (`splint_adapter.json`)
- 노즐 4개 + 어댑터 + 튜브팁 = 총 6개 부품의 위치/회전 저장
- 페이지 로드 시 자동으로 읽어서 복원
- "저장" 버튼으로 새 JSON 다운로드 → `splint_adapter.json`으로 덮어쓰면 기본값 갱신

### 조립 애니메이션 타임라인
| 구간 | 내용 |
|------|------|
| 0~2.5s | Point Shower 로고 (페이드 인/아웃) |
| 2.5~4.0s | 스플린트 회전 인트로 |
| 4.0~11.2s | 노즐 1→2→3→4 바깥에서 날아와 결합 |
| 12.2~14.7s | 어댑터 날아와 결합 |
| 15.2~17.2s | 튜브팁 날아와 결합 |
| 17.2~20.2s | 완성품 회전 아웃트로 |

### 키보드 단축키
| 키 | 기능 |
|---|------|
| `1`~`6` | 부품 선택 (한글 입력 모드에서도 동작, `e.code` 기반) |
| `←→` / `↑↓` / `PgUp/Dn` | X/Y/Z 이동 (1mm, +Shift=0.2mm, +Alt=5mm) |
| `R/F` | Z축 회전 |
| `T/G` | X축 회전 |
| `Y/H` | Y축 회전 |
| `X` / `Z` | X축/Z축 90° 회전 |
| `Ctrl+Z` | 되돌리기 (50단계) |
| `ESC` | 애니메이션 중단 |

### 작업 이력
1. **2026-04-16**: 초기 뷰어 제작 (스플린트 + 노즐 4개 + 어댑터)
   - STL/STEP 로딩, 4분할 뷰포트, 클릭 배치, 키보드 미세조정
   - 조립 애니메이션 + MP4 녹화 기능
   - `assembly-2026-04-16.webm/mp4` 첫 결과물 생성
2. **2026-04-20**: 튜브팁 추가 + 로고 인트로
   - `tubetip.stl`을 6번째 부품으로 추가 (인덱스 5, 흰색 불투명)
   - Point Shower 로고를 애니메이션 인트로에 추가 (Three.js 텍스처)
   - 키보드 단축키를 `e.code` 기반으로 변경 (한글 입력 모드 호환)
   - 버튼 `data-idx` 속성으로 선택 UI 버그 수정
   - localStorage 자동저장 제거, `splint_adapter.json` 파일 기반으로 전환
   - `assembly-2026-04-20.mp4` 결과물 생성

### 알려진 이슈 / 추후 작업
- [ ] 로고 인트로 색상 진하게 조정 (톤맵핑 OFF 적용됨, 추가 확인 필요)
- [ ] 어댑터 자동배치 정밀도 개선
- [ ] 조립 애니메이션 카메라 앵글 커스터마이징
- [ ] 분해 애니메이션 (역순)
- [ ] 부품별 색상/투명도 실시간 조절

---

## 2. 3D 메쉬 모션그래픽 도구 (`mesh-motion/`)

### 개요
STL/OBJ 3D 모델을 유튜브용 시네마틱 모션그래픽 MP4로 변환하는 파이썬 스크립트.

### 실행 방법
```bash
cd /Users/jin/lander
.venv/bin/python mesh-motion/mesh_motion.py input.obj -o out.mp4
```

### 기능
- STL/OBJ 자동 로드 (trimesh) + 자동 축 정렬 (Z-up → Y-up)
- 6개 시네마틱 샷 (타이틀/오빗/와이어프레임 리빌/히어로/디졸브/엔드카드)
- PIL 한글 텍스트 오버레이 (AppleSDGothicNeo 폰트)
- 계면조(A 단5음계) 기반 절차 생성 BGM
- ffmpeg 자동 머지 (비디오 + 오디오)

### 옵션
```bash
--title "한국인" --subtitle "肖像 · 2026"   # 타이틀
--bg "#0a0a10" --accent "#c8394a"            # 색상 테마
--resolution 3840 2160 --fps 60              # 4K60
--no-audio                                   # BGM 없이
--rotate 0 180 0                             # 모델 수동 회전
```

### 작업 이력
1. **2026-04-12**: 초기 제작 + 한국인 테마 적용
   - pyvista + trimesh + imageio 기반
   - 한국 전통 색감 (단청 적색 + 청화 청색 + 한지 크림)
   - `korean_portrait.mp4` 결과물 (15초, 1080p30, BGM 포함)

---

## 3. SIDEX 2026 강연 준비 (`sidex-2026/`)

### 개요
SIDEX 2026(서울국제치과기자재전시회)에서 그래피(Graphy) 부스 Lecture Zone 1시간 강연 준비.

- **강연자**: 이중우 원장 / 올리브서울치과
- **행사**: 2026.05.29~31, COEX Hall D
- **부스**: D-601~610, 701~710 (그래피 20부스)
- **내용**: Point Shower 제품 소개 + 디지털 치과 워크플로

### 작업 이력
1. **2026-04-26**: 프로젝트 초기 셋업
   - 폴더 구조 생성, 부스 시안 PDF 정리
   - 강연 구성안 초안 작성 (1시간 시간 배분)
   - 그래피 회사 정보 정리

### 다음 단계
- [ ] 강연 구성안 확정
- [ ] 키노트/PPT 제작
- [ ] 임상 케이스 사진 수집
- [ ] 그래피 측 기술 자료 확보
- [ ] 부스 루프 영상 제작

---

## 원본 파일 위치

정리 전 원본은 아래에 남아 있습니다 (확인 후 삭제 가능):
```
/Users/jin/Downloads/이중우대표님/
```

포함된 것: zip 원본, ASCII STL(nozzle0306.stl, 19MB), 중복 파일들, 이전 레이아웃 JSON들.
바이너리 STL(`nozzle0306_bin.stl`)만 뷰어에서 사용하므로 ASCII 원본은 백업용입니다.
