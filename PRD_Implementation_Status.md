# InfraLens MVP PRD 대비 구현 현황 (최신)

기준 문서: `/Users/ckahn/Desktop/infralens/InfraLens_MVP_PRD.md`  
검토 시점: 2026-02-20

## 1) 충족된 항목

- Streamlit MVP 핵심 흐름
  - 시나리오 선택 -> 작업 설정 -> 분석 -> 결과 -> PDF 다운로드
  - 근거: `/Users/ckahn/Desktop/infralens/app.py:307`, `/Users/ckahn/Desktop/infralens/app.py:624`

- Resource Efficiency Score 계산/등급
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/scoring.py`

- 병목 탐지 룰 (NUMA/NVLink/MIG)
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/rules.py`

- LLM 하이브리드 분석/추천 + fallback
  - API 키 없으면 규칙 기반 fallback
  - Provider: OpenAI / Claude(Anthropic) / Google
  - 근거: `/Users/ckahn/Desktop/infralens/app.py:361`
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/llm.py:34`
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/llm.py:211`

- 텔레메트리 업로드 파싱
  - `nvidia-smi` CSV (헤더 포함/미포함 noheader,nounits) 지원
  - 선택 입력: `nvidia-smi topo -m`, `numactl --hardware`로 토폴로지 보정
  - 근거: `/Users/ckahn/Desktop/infralens/app.py:331`
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/parsers.py`

- 실행 명령 템플릿 자동 생성
  - `numactl/taskset/docker` + 실행 설정 주입
  - Docker일 때 host reference 토글 제공
  - MIG 템플릿 개행 표시 처리
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/commands.py:44`
  - 근거: `/Users/ckahn/Desktop/infralens/app.py:575`
  - 근거: `/Users/ckahn/Desktop/infralens/app.py:603`

- 실행 설정 Validation
  - Docker image 필수, Manual CPU set 필수, Env Vars 형식 검증, Entry command 필수
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/validation.py`
  - 근거: `/Users/ckahn/Desktop/infralens/app.py:450`

- 시나리오별 작업 프리셋 자동 적용
  - SMB: 추론 중심, Mid-Market: 학습+추론 혼합
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/data.py:325`
  - 근거: `/Users/ckahn/Desktop/infralens/app.py:424`

- 다국어 UI/분석 문구
  - 한국어/영어/중국어
  - 근거: `/Users/ckahn/Desktop/infralens/app.py:20`

- 초보자 친화 용어 설명(텔레메트리/작업)
  - 캡션 + 물음표 도움말
  - 근거: `/Users/ckahn/Desktop/infralens/app.py:317`
  - 근거: `/Users/ckahn/Desktop/infralens/app.py:412`

- 사이드바 레이아웃 3:7 근사
  - 근거: `/Users/ckahn/Desktop/infralens/app.py:290`

## 2) 테스트 상태

- 템플릿 생성 테스트
  - `ExecutionConfig` 조합(수동 CPU, docker flag, MIG 개행 등)
  - 근거: `/Users/ckahn/Desktop/infralens/tests/test_commands.py`

- 프리셋 데이터 테스트
  - SMB/중견 시나리오 workload 특성 검증
  - 근거: `/Users/ckahn/Desktop/infralens/tests/test_data_presets.py`

- 실행 설정 validation 테스트
  - Docker image/Manual CPU/Entry/Env Vars 라인 검증
  - 근거: `/Users/ckahn/Desktop/infralens/tests/test_validation.py`

- 스모크 테스트
  - 추천 + 템플릿 생성 최소 경로
  - 근거: `/Users/ckahn/Desktop/infralens/tests/test_smoke.py`

## 3) 부분 충족 항목

- 입력 소스
  - `nvidia-smi` 계열은 구현
  - Prometheus 입력 어댑터는 미구현

- 배포/운영
  - 로컬 실행 기준은 완료
  - Streamlit Cloud 실배포 URL은 미확보

## 4) 미구현 또는 미검증 항목

- Streamlit Cloud 배포(URL 공개)
- 성공지표 자동 측정 루프
  - 응답속도 측정 자동화
  - 정확도/회귀 테스트 지표화
  - 사용자 이해도 테스트 프로토콜
- 데모 영상/리허설 산출물

## 5) 문서-구현 정합성 상태

- README와 업로드 정책 정합: 현재 일치 (`.csv` 업로드 + topo/numa 선택 파일)
  - 근거: `/Users/ckahn/Desktop/infralens/README.md:34`
  - 근거: `/Users/ckahn/Desktop/infralens/app.py:331`

- Provider 관련 정합: OpenAI 중심 아님 (Claude/Google 포함)
  - 근거: `/Users/ckahn/Desktop/infralens/app.py:361`
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/llm.py:36`

## 6) 권장 후속 작업(우선순위)

1. Prometheus 입력 어댑터 최소 버전 추가
2. Streamlit Cloud 배포 및 공개 URL 확보
3. 성공지표 자동 측정 스크립트/체크리스트 추가
4. 데모 리허설 문서 + 영상 산출물 작성
