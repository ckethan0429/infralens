# InfraLens — GPU Infrastructure Optimization AI Agent

### MVP Product Requirements Document

**조코딩 AI 해커톤 2026**
Version 1.0 | 2026.02.20 | Author: 안창균 (VirtOn CTO)

---

## 1. Executive Summary

InfraLens는 GPU 서버를 보유한 기업을 위한 **AI 기반 인프라 운영 최적화 에이전트**입니다.

한국 기업들은 수억~수십억 원의 GPU 서버를 구매하지만, 전문 인력 부족으로 GPU 활용률이 30~50%에 머무르고 있습니다. NUMA affinity 미스매치, NVLink 토폴로지 미고려 배치, MIG/vGPU 미활용 등 인프라 전문가가 아니면 파악하기 어려운 비효율이 곳곳에 숨어 있습니다.

InfraLens는 모니터링 데이터를 입력받아 **효율 점수 산출**, **AI 병목 분석**, **최적 배치 제안**의 세 가지 핵심 기능을 제공하여, 전문 컨설턴트 수준의 GPU 인프라 최적화를 자동화합니다.

> **핵심 가치 제안:** 수천만 원짜리 GPU 인프라 컨설팅을 AI로 자동화하여, 비전문가도 전문가 수준의 GPU 운영 최적화를 실현할 수 있게 합니다.

---

## 2. Problem Statement

### 2.1 Target Customer

**Customer A: 중견기업 IT 인프라팀**

H100/H200 서버를 수억 원에 구매했지만, 팀 내에 GPU 가상화 및 최적화 전문 인력이 없습니다. nvidia-smi 출력값을 봐도 숫자만 나올 뿐 "왜 느린지", "어떻게 배치해야 하는지" 판단할 수 없어 비싼 장비가 절반의 성능만 내고 있습니다. 외부 컨설팅을 받자니 건당 수천만 원이고, 상시 모니터링은 불가능합니다.

**Customer B: AI 스타트업 MLOps/DevOps 엔지니어**

제한된 GPU 리소스로 학습과 추론을 동시에 돌려야 하지만, MIG 분할, vGPU 설정, NUMA 최적화 같은 인프라 튜닝에 시간을 쏟을 여유가 없습니다. 모델 개발에 집중하고 싶지만, GPU 배치가 잘못되면 학습 시간이 2배로 늘어나 비용과 일정이 함께 밀립니다.

### 2.2 Pain Points

| 문제 | 현재 상황 | 영향 |
|------|----------|------|
| GPU 활용률 저조 | 평균 30~50% 활용률 | 투자 대비 절반의 성능만 회수 |
| 전문 인력 부재 | GPU 최적화 전문가 한국 내 극소수 | 자체 최적화 불가능 |
| 컨설팅 비용 과다 | 건당 수천만 원, 상시 모니터링 불가 | 일회성 진단 후 다시 비효율 누적 |
| NUMA/NVLink 복잡성 | 수동 확인 필요, 실수 빈발 | 성능 40% 이상 저하 가능 |

---

## 3. Solution Overview

InfraLens는 **Build(구축) → Operate(운영)** 풀사이클 GPU 인프라 최적화를 제공합니다. MVP에서는 Operate Phase의 세 가지 핵심 기능에 집중합니다.

### 3.1 Resource Efficiency Score

> 기술 방식: **룰 기반 계산** (LLM 불필요)

nvidia-smi, Prometheus 등의 모니터링 데이터를 입력받아 GPU 인프라 전체의 효율성을 A~F 등급으로 점수화합니다.

**점수 산출 공식:**

```
GPU 활용률 점수 = (gpu_util / 100) × 0.4 + (vram_used / vram_total) × 0.3
NUMA 정합성 점수 = 1.0 (정상) / 0.5 (미스매치)
전체 효율 = GPU 점수 × 0.6 + NUMA 점수 × 0.2 + Network I/O 점수 × 0.2
```

**등급 체계:**

| 등급 | 점수 범위 | 상태 | 조치 |
|------|----------|------|------|
| A | 90~100 | 최적 운영 중 | 유지 |
| B | 75~89 | 양호, 개선 여지 | 권장사항 확인 |
| C | 60~74 | 비효율 감지 | 병목 분석 필요 |
| D | 40~59 | 심각한 낭비 | 즉시 재배치 권장 |
| F | 0~39 | 위험 수준 | 긴급 최적화 필요 |

### 3.2 AI Bottleneck Analysis

> 기술 방식: **LLM 활용** (Claude/GPT API)

효율 점수가 낮은 원인을 LLM이 자연어로 분석하여 비전문가도 이해할 수 있는 진단 리포트를 생성합니다.

**분석 항목:**

- **NUMA affinity 미스매치 감지:** CPU-GPU 소켓 매핑 불일치로 인한 PCIe 레이턴시 증가
- **NVLink 토폴로지 미활용:** NVLink 미연결 GPU 간 분산학습 할당 감지
- **MIG/vGPU 미활용:** 단일 워크로드에 전체 GPU 할당 시 낭비 분석
- **메모리 병목:** VRAM 과다/과소 할당 워크로드 식별
- **I/O 병목:** 네트워크/스토리지로 인한 GPU idle 시간 감지

**출력 예시:**

> "GPU 3번과 5번이 NVLink로 연결되어 있지 않은 상태에서 동일 분산학습 작업에 할당되어 있습니다. GPU 간 통신이 PCIe를 경유하면서 학습 속도가 약 40% 저하될 수 있습니다. GPU 0-3번 NVLink 그룹으로 재배치를 권장합니다."

### 3.3 Optimal Placement Recommendation

> 기술 방식: **룰 기반 + LLM 조합**

병목 분석 결과를 기반으로 워크로드 재배치 방안을 자동 생성합니다. 룰 엔진이 NUMA/NVLink 제약 조건을 처리하고, LLM이 워크로드 특성을 고려한 최종 배치안과 자연어 설명을 제공합니다.

**제안 로직:**

- NVLink 토폴로지 기반 GPU 그룹핑 (룰)
- NUMA affinity 매칭 (룰)
- 워크로드 유형별 최적 할당 방식 결정: 학습=패스스루, 추론=MIG (룰+LLM)
- 예상 성능 개선 수치 산출 (LLM)
- 실행 가능한 명령어/설정 가이드 생성 (LLM)

**출력 예시:**

> 1. VM-training-01 → GPU 0,1,2,3 (NVLink Group A)으로 이동
> 2. VM-inference-02 → GPU 6 (MIG 1g.20gb)으로 분리
> 3. VM-inference-03 → GPU 6 (MIG 1g.20gb) 공유 배치
>
> **예상 개선: 학습 처리량 +35%, 추론 레이턴시 -20%, 전체 GPU 활용률 48% → 78%**

---

## 4. Technical Architecture

### 4.1 MVP Tech Stack

| 영역 | 기술 | 선택 이유 |
|------|------|----------|
| Frontend | Streamlit | 빠른 프로토타이핑, 대시보드 시각화 내장 |
| LLM | Claude / GPT API | 해커톤 제공 크레딧 활용 |
| 계산 엔진 | Python (pandas, numpy) | 효율 점수 산출, 룰 기반 로직 |
| 데이터 | 샘플 nvidia-smi JSON | 실제 GPU 없이 데모 가능 |
| 배포 | Streamlit Cloud | 무료, 즉시 URL 공유 |
| 리포트 | PDF 자동 생성 | 분석 결과 원클릭 다운로드 |

### 4.2 Data Flow

```
① 사용자: nvidia-smi 출력 또는 샘플 데이터 선택
    ↓
② Python 엔진: Resource Efficiency Score 계산 (A~F 등급)
    ↓
③ GPU 토폴로지 + 워크로드 정보 → LLM 컨텍스트 전달
    ↓
④ LLM: 병목 원인 분석 + 자연어 진단 생성
    ↓
⑤ 룰 엔진: NUMA/NVLink 제약 조건 기반 배치 후보 생성
    ↓
⑥ LLM: 워크로드 특성 고려 최종 배치안 + 예상 개선 수치 산출
    ↓
⑦ Output: 대시보드 시각화 + PDF 리포트 다운로드
```

---

## 5. Demo Scenario

실제 GPU 서버 없이도 샘플 데이터로 풀 데모가 가능합니다.

| 단계 | 사용자 행동 | 시스템 응답 |
|------|-----------|-----------|
| 1 | "H200 8장 서버" 시나리오 선택 | 샘플 nvidia-smi 데이터 로드 |
| 2 | "학습 3개 + 추론 2개" 워크로드 설정 | 워크로드 프로파일 구성 |
| 3 | "분석 시작" 클릭 | 효율 점수: C등급 (62점) 표시 |
| 4 | 병목 분석 결과 확인 | "GPU 2,5 NUMA 미스매치" 등 자연어 진단 |
| 5 | 배치 제안 확인 | MIG 분리 + NUMA 재배치안 + 예상 개선 수치 |
| 6 | "리포트 다운로드" 클릭 | PDF 리포트 자동 생성 및 다운로드 |

---

## 6. Scope Definition

### 6.1 MVP (해커톤)

- 샘플 데이터 기반 데모 (H200 8장, L40s 4장 시나리오)
- Resource Efficiency Score A~F 등급 대시보드
- LLM 기반 병목 분석 자연어 리포트
- 룰+LLM 하이브리드 배치 제안
- PDF 리포트 원클릭 생성
- Streamlit Cloud 배포

### 6.2 Post-Hackathon (v1.0)

- 실시간 nvidia-smi / Prometheus 연동
- Proxmox API 연동 (VM 자동 재배치)
- 히스토리 트래킹 (효율 점수 추이)
- 멀티 서버 지원
- 알림 시스템 (효율 점수 임계값 이하 시)

### 6.3 Out of Scope

- 실제 GPU 서버 제어 (MVP에서는 제안만)
- 빌링/과금 시스템
- 멀티 테넌트 지원

---

## 7. Development Timeline

| Phase | Task | Duration | Output |
|-------|------|----------|--------|
| Day 1 AM | 프로젝트 셋업, 샘플 데이터 구조 설계 | 3h | 데이터 스키마, 프로젝트 구조 |
| Day 1 PM | 효율 점수 계산 엔진 + Streamlit UI | 4h | 대시보드 프로토타입 |
| Day 2 AM | LLM 프롬프트 엔지니어링 + 병목 분석 | 4h | 병목 분석 기능 |
| Day 2 PM | 배치 제안 로직 + PDF 리포트 | 4h | 배치 제안 + 리포트 |
| Day 3 AM | UI 폴리싱 + 데모 시나리오 완성 | 3h | 최종 데모 |
| Day 3 PM | 배포 + 데모 영상 촬영 | 3h | 배포 URL + 영상 |

---

## 8. Success Metrics

| Metric | Target | 측정 방법 |
|--------|--------|----------|
| 데모 완성도 | 풀 시나리오 3분 내 시연 가능 | 데모 영상 촬영 |
| 분석 정확도 | H200 8장 시나리오 NUMA/NVLink 이슈 100% 감지 | 테스트 케이스 |
| 응답 속도 | 효율 점수 1초 이내, LLM 분석 10초 이내 | Streamlit 로그 |
| 사용자 이해도 | 비전문가가 리포트 보고 문제 파악 가능 | 팀원 테스트 |

---

## 9. Competitive Advantage

InfraLens의 핵심 차별점은 **실전 도메인 지식의 AI 내재화**입니다.

- **실제 H200/L40s 구축 경험:** 이론이 아닌 현장에서 검증된 최적화 룰셋
- **Proxmox vGPU/MIG/패스스루 전문 지식:** 한국 내 5명 미만의 전문가 노하우
- **한국 기업 특성 반영:** "GPU 직접 구매 선호" 시장에 최적화된 솔루션
- **Build → Operate 확장 가능:** 견적 → 구축 → 운영 풀사이클 로드맵

> **경쟁 환경:**
> - Run:ai (NVIDIA 인수) → Kubernetes 전제, 한국 시장 미진출
> - VMware vSphere → Broadcom 인수 후 비용 폭등
> - ZStack AIOS → 중국산, 한국 레퍼런스 없음
>
> **Proxmox 기반 GPU 인프라 최적화 AI 도구는 글로벌에도 존재하지 않습니다.**
