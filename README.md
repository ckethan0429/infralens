# InfraLens MVP

Streamlit 기반 GPU 인프라 최적화 데모입니다.

## 기능
- Resource Efficiency Score 계산 (A~F)
- 룰 기반 병목 탐지 (NUMA/NVLink/MIG)
- LLM 기반 자연어 분석 (API 키 없으면 폴백)
- 최적 배치 제안 및 예상 개선치
- 워크로드별 실행 템플릿 자동 생성 (`numactl` / `taskset` / `docker`)
- PDF 리포트 다운로드
- `nvidia-smi` CSV 업로드 분석
- 다국어 UI/분석 지원 (한국어/영어/중국어)
- 워크로드 프로필별 가중치/임계값 튜닝 (`training`/`inference`/`default`)

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

## UI에서 LLM API 연동
앱 상단의 `LLM API 설정`에서 바로 연결할 수 있습니다.

1. `Use LLM API from UI` 활성화
2. `Provider` 선택 (`OpenAI` / `Claude` / `Google`)
3. 해당 Provider의 API Key 입력
4. `Model` 선택
5. `분석 시작` 클릭

API Key를 입력하지 않으면 자동으로 룰 기반 fallback 분석을 사용합니다.

모델 선택은 `LLM API 설정`에서 API Key 입력 시 Provider별 모델 목록을 자동으로 불러와 드롭다운으로 선택할 수 있습니다.
