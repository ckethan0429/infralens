# Execution UI Plan (실환경 변수 입력)

기준: `/Users/ckahn/Desktop/infralens` MVP 현재 상태
작성일: 2026-02-20

## 목표
추천 결과로 생성되는 `numactl/taskset/docker` 명령을 실제 운영 환경에서 바로 실행 가능한 수준으로 만들기 위해, 사용자 입력 변수를 UI에서 수집하고 템플릿에 주입한다.

## 범위 (v1)
- 현재 템플릿 생성기(`infralens/commands.py`)를 유지
- UI에서 환경 변수 입력을 받아 명령어 문자열에 반영
- 지원 대상: `Bare Metal`, `Docker`

## UI 설계

### 1) Runtime Preset
- `Execution Environment`
  - 옵션: `Bare Metal`, `Docker`
- `Entry Command`
  - 예: `python train.py`, `python serve.py`
- `Workdir` (optional)
  - 예: `/workspace`

### 2) Command Variables
- `Image Name` (Docker일 때 필수)
  - 예: `my-registry/infralens:latest`
- `Container Name Prefix`
  - 예: `infralens-job`
- `Extra Args`
  - 예: `--batch-size 64 --epochs 10`
- `Env Vars` (멀티라인)
  - 형식: `KEY=VALUE` 한 줄씩

### 3) CPU/GPU Binding Policy
- `CPU Set Mode`
  - `Auto(socket-based)`
  - `Manual`
- `Manual CPU Set` (Manual일 때)
  - 예: `0-23,48-71`
- `GPU Visibility Style`
  - `CUDA_VISIBLE_DEVICES`
  - `--gpus device=...`

## 명령어 반영 규칙

### 공통
- 워크로드별 추천 GPU 리스트를 `gpu_csv`로 계산
- CPU set은 `Auto`면 기존 socket 기반, `Manual`이면 사용자 입력 사용
- `Extra Args`는 entry command 뒤에 append
- `Env Vars`는 파싱 후 `KEY=VALUE` 형태로 prepend

### numactl
- 기본 형태:
  - `CUDA_VISIBLE_DEVICES={gpu_csv} numactl --cpunodebind={socket} --membind={socket} {entry_command} --workload {name} {extra_args}`

### taskset
- 기본 형태:
  - `CUDA_VISIBLE_DEVICES={gpu_csv} taskset -c {cpu_set} {entry_command} --workload {name} {extra_args}`

### docker
- 기본 형태:
  - `docker run --rm --name {prefix}-{name} --gpus '"device={gpu_csv}"' --cpuset-cpus="{cpu_set}" {env_flags} {image} {entry_command} --workload {name} {extra_args}`
- `GPU Visibility Style`이 `CUDA_VISIBLE_DEVICES`면:
  - `-e CUDA_VISIBLE_DEVICES={gpu_csv}` 추가

## 데이터 모델 (제안)
```python
@dataclass
class ExecutionConfig:
    environment: Literal["bare_metal", "docker"]
    entry_command: str
    workdir: str | None
    image_name: str | None
    container_prefix: str
    extra_args: str
    env_vars: dict[str, str]
    cpu_set_mode: Literal["auto", "manual"]
    manual_cpu_set: str | None
    gpu_visibility_style: Literal["cuda_visible_devices", "docker_gpus_device"]
```

## 구현 포인트
- `app.py`
  - `Execution Settings` expander 추가
  - session_state로 설정 유지
  - 템플릿 출력 시 설정값 주입
- `infralens/commands.py`
  - `build_execution_templates(...)`에 `ExecutionConfig` 인자 추가
  - 문자열 생성 시 policy 반영

## 검증 체크리스트
- `Bare Metal`에서 `numactl/taskset` 출력 정상
- `Docker`에서 `image_name` 미입력 시 경고
- `Manual CPU Set` 비어있을 때 validation
- env var 파싱(`KEY=VALUE`) 실패 라인 에러 처리
- 기존 추천 데이터(학습/추론 혼합)에서 워크로드별 템플릿 정상 생성

## v2 아이디어 (현재 범위 제외)
- K8s Job YAML 템플릿 생성
- Proxmox VM migrate command 템플릿
- MIG profile apply/rollback 스크립트 생성
