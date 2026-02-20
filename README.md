# InfraLens MVP

Streamlit 기반 GPU 인프라 최적화 데모입니다.

## 기능
- Resource Efficiency Score 계산 (A~F)
- 룰 기반 병목 탐지 (NUMA/NVLink/MIG)
- LLM 기반 자연어 분석 (API 키 없으면 폴백)
- 최적 배치 제안 및 예상 개선치
- 워크로드별 실행 템플릿 자동 생성 (`numactl` / `taskset` / `docker`)
- 실행 설정 UI (환경/엔트리/CPU/GPU policy) 기반 템플릿 주입
- PDF 리포트 다운로드
- `nvidia-smi` CSV 업로드 분석
- 다국어 UI/분석 지원 (한국어/영어/중국어)
- 워크로드 프로필별 가중치/임계값 튜닝 (`training`/`inference`/`default`)
- 시나리오별 워크로드 프리셋 자동 적용 (SMB/중견)

## 실행
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## LLM 사용 (선택)
```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-4o-mini"
```

API 키가 없으면 자동으로 룰 기반 텍스트를 사용합니다.

## 업로드 포맷
앱에서 `Telemetry Source -> Upload nvidia-smi` 선택 후 `.csv` 업로드:

- CSV 예시 컬럼:
`index,utilization.gpu,memory.used,memory.total,numa_node,cpu_socket,nvlink_group`
- `--format=csv,noheader,nounits` 형식도 자동 인식:
`0,88,70200,81920,0,0,A`

선택 업로드(정밀도 향상):
- `nvidia-smi topo -m` 파일 (`.txt`)
- `numactl --hardware` 파일 (`.txt`)

두 파일을 함께 넣으면 GPU별 `NUMA`/`CPU socket`/`NVLink group`을 실제 토폴로지 기반으로 덮어씁니다.

예제 파일:
- `/Users/ckahn/Desktop/infralens/examples/nvidia_smi_sample.csv`
- `/Users/ckahn/Desktop/infralens/examples/nvidia_smi_sample_noheader.csv`
- `/Users/ckahn/Desktop/infralens/examples/nvidia_smi_sample.json`
- `/Users/ckahn/Desktop/infralens/examples/nvidia_smi_topo_m_sample.txt`
- `/Users/ckahn/Desktop/infralens/examples/nvidia_smi_topo_m_sample.csv`
- `/Users/ckahn/Desktop/infralens/examples/nvidia_smi_topo_m_sample.json`
- `/Users/ckahn/Desktop/infralens/examples/numactl_hardware_sample.txt`
- `/Users/ckahn/Desktop/infralens/examples/numactl_hardware_sample.csv`
- `/Users/ckahn/Desktop/infralens/examples/numactl_hardware_sample.json`

## 실제 nvidia-smi 수집 명령 (복붙용)
헤더 포함 CSV:
```bash
nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv > nvidia_smi.csv
```

헤더 없는 CSV (`csv,noheader,nounits`):
```bash
nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits > nvidia_smi_noheader.csv
```

NUMA/소켓/NVLink 그룹까지 같이 넣고 싶을 때(수동 보강용):
```bash
nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits > nvidia_smi_ext.csv
# 이후 각 행 뒤에 numa_node,cpu_socket,nvlink_group 값을 추가
# 예: 0,88,70200,81920,0,0,A
```

토폴로지 텍스트 추출:
```bash
nvidia-smi topo -m > nvidia_smi_topo_m.txt
numactl --hardware > numactl_hardware.txt
```

## 튜닝 설정
점수 가중치/룰 임계값은 아래 파일에서 조정:
- `/Users/ckahn/Desktop/infralens/config/optimization_profiles.json`

## 실행 템플릿 설정
사이드바의 `Execution Settings`에서 아래 항목을 조정하면 `numactl/taskset/docker` 명령 템플릿에 즉시 반영됩니다.

- Execution Environment (`Bare Metal` / `Docker`)
- Entry Command / Workdir
- Docker Image / Container Prefix
- Extra Args / Env Vars (`KEY=VALUE` 줄단위)
- CPU Set Mode (`Auto` / `Manual`) + Manual CPU Set
- GPU Visibility Style
  - `CUDA_VISIBLE_DEVICES`
  - `--gpus "device=..."`

Validation:
- Docker 환경에서 이미지 미입력 시 경고
- Manual CPU 모드에서 CPU 세트 미입력 시 경고
- 잘못된 Env Vars 라인 번호 경고
- Entry Command 미입력 시 경고

출력 필터링:
- `Bare Metal` 선택 시 `numactl/taskset` 중심으로 표시 (docker 템플릿 숨김)
- `Docker` 선택 시 docker 명령을 기본 표시
- `Docker`에서 `호스트 명령도 함께 보기`를 켜면 `numactl/taskset`을 참고용으로 축소(expander) 표시

개행 표시:
- MIG 관련 템플릿은 `# MIG profile ...` 다음 줄에 실제 실행 명령이 개행되어 표시됩니다.

## UI에서 LLM API 연동
앱 상단의 `LLM API 설정`에서 바로 연결할 수 있습니다.

1. `Use LLM API from UI` 활성화
2. `Provider` 선택 (`OpenAI` / `Claude` / `Google`)
3. 해당 Provider의 API Key 입력
4. `Model` 선택
5. `분석 시작` 클릭

API Key를 입력하지 않으면 자동으로 룰 기반 fallback 분석을 사용합니다.

모델 선택은 `LLM API 설정`에서 API Key 입력 시 Provider별 모델 목록을 자동으로 불러와 드롭다운으로 선택할 수 있습니다.

## 쉬운 용어
- 텔레메트리(Telemetry): GPU 사용률/메모리 같은 운영 측정 데이터
- 작업(Task, Workload): 서버에서 실행할 프로그램 단위 (예: 학습 작업, 추론 API)

## 성공지표 자동 측정
최소 지표(응답시간, 테스트 통과율, 추천 일치율)를 JSON 로그로 수집합니다.

```bash
python3 scripts/collect_success_metrics.py --iterations 3 --out logs/success_metrics.jsonl
```

수집 항목:
- `response_time_sec`: 점수 계산/분석 파이프라인 평균 및 p95
- `test_pass_rate`: 단위테스트 통과율
- `recommendation_consistency`: 추천 필요성 판단 일치율

UI에서도 동일 기능 사용 가능:
- `성공지표 측정` 섹션에서 `최적화 전/후` 선택 후 실행
- 앱에서 최근 로그와 전/후 비교 요약을 바로 확인
- 전/후 데이터가 있으면 비교 리포트(`.md`)를 다운로드 가능

지표 해석:
- 응답시간(`score_avg/p95`, `analysis_pipeline_avg/p95`): 낮을수록 좋음
- 테스트 통과율(`pass_rate`): 높을수록 좋음
  - 실행 테스트: `python -m unittest discover -s tests -p 'test_*.py'`
  - 계산식: `passed_tests / total_tests`
- 추천 일치율(`consistency_rate`): 높을수록 좋음
  - 일치 기준: `(병목 있음 & 추천 있음) 또는 (병목 없음 & 추천 없음)`
  - 계산식: `consistency_successes / attempted_scenarios`
