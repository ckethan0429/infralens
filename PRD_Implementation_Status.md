# InfraLens MVP PRD 대비 구현 현황

기준 문서: `/Users/ckahn/Desktop/infralens/InfraLens_MVP_PRD.md`
검토 시점: 2026-02-20

## 1) 충족된 항목

- Streamlit MVP UI/흐름: 시나리오 선택 → 워크로드 설정 → 분석 → 결과 → PDF 다운로드
  - 근거: `/Users/ckahn/Desktop/infralens/app.py:221`
- Resource Efficiency Score 계산식/등급(A~F)
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/scoring.py:21`
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/scoring.py:29`
- 병목 룰 탐지(NUMA/NVLink/MIG)
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/rules.py:37`
- 룰+LLM 하이브리드 추천(LLM 없으면 fallback)
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/rules.py:121`
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/llm.py:67`
- PDF 리포트 생성
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/report.py:49`
- 샘플 시나리오(H200 8GPU, L40s 4GPU)
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/data.py:18`
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/data.py:99`
- PRD 데모 수치 의도 반영(C 62점, 48→78 개선)
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/data.py:20`
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/rules.py:166`
- 다국어(한/영/중) UI + 분석/추천 문구
  - 근거: `/Users/ckahn/Desktop/infralens/app.py:15`
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/i18n.py:15`

## 2) 부분 충족 항목

- “nvidia-smi/Prometheus 입력” 중 Prometheus는 미연동, nvidia-smi 기반은 구현
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/parsers.py:99`
- “Claude/GPT API” 요구 대비 현재 OpenAI 중심
  - 근거: `/Users/ckahn/Desktop/infralens/infralens/llm.py:85`
- “실행 가능한 명령어/설정 가이드 생성”은 수집 명령 중심이며, 워크로드별 자동 실행 커맨드 생성은 제한적
  - 근거: `/Users/ckahn/Desktop/infralens/app.py:198`

## 3) 미구현 또는 미검증 항목

- Streamlit Cloud 배포(URL)
- 성공지표 검증 루프
  - 응답속도 측정
  - 정확도 테스트케이스
  - 사용자 이해도 테스트
- 데모 영상/리허설 산출물

## 4) 문서-구현 불일치(수정 필요)

- 현재 UI는 텔레메트리 업로드를 `.csv`만 허용
  - 근거: `/Users/ckahn/Desktop/infralens/app.py:232`
- README에는 여전히 “CSV/JSON 업로드 분석” 문구가 있어 일부 불일치
  - 근거: `/Users/ckahn/Desktop/infralens/README.md:11`

## 5) 권장 후속 작업(우선순위)

1. README와 UI 업로드 정책 일치화
2. Prometheus 입력 어댑터 최소 버전 추가
3. Anthropic(Claude) provider 옵션 추가
4. 성공지표 자동 측정 스크립트/체크리스트 추가
5. Streamlit Cloud 배포 및 데모 리허설 문서화
