from __future__ import annotations

import pandas as pd
import streamlit as st

from infralens.commands import ExecutionConfig, build_execution_templates
from infralens.data import Workload, default_workloads, sample_scenarios, workloads_for_scenario
from infralens.i18n import localize_findings, localize_recommendation, localize_severity
from infralens.llm import (
    generate_bottleneck_analysis,
    generate_recommendation_narrative,
    list_provider_models,
)
from infralens.parsers import parse_uploaded_telemetry
from infralens.report import build_pdf_report
from infralens.rules import build_placement_recommendation, detect_bottlenecks
from infralens.scoring import calculate_efficiency_score, infer_workload_profile
from infralens.metrics import collect_success_metrics, load_recent_metrics
from infralens.validation import validate_execution_settings


I18N = {
    "ko": {
        "title": "InfraLens - GPU 인프라 최적화 AI 에이전트",
        "caption": "MVP 데모: 효율 점수 + 병목/비효율 분석 + 최적 배치",
        "lang": "언어",
        "source": "텔레메트리 소스",
        "source_help": "텔레메트리는 서버 상태를 시간 순서로 모은 측정 기록입니다.",
        "sample": "샘플 데이터",
        "upload": "nvidia-smi 업로드",
        "scenario": "시나리오",
        "scenario_help": "시나리오는 분석 대상 서버 상태 1세트입니다. (GPU 수, 사용률, 메모리, NUMA/NVLink 정보)",
        "sample_scenario_help": "샘플 시나리오는 데모/테스트용으로 미리 준비된 서버 상태 데이터입니다.",
        "upload_label": "텔레메트리 파일 업로드 (.csv)",
        "upload_topo_label": "선택: nvidia-smi topo 파일 업로드 (.txt)",
        "upload_numa_label": "선택: numactl --hardware 파일 업로드 (.txt)",
        "upload_info": "분석을 위해 텔레메트리 파일을 업로드하세요.",
        "upload_ok": "GPU {n}개를 {name}에서 로드했습니다.",
        "upload_topo_ok": "토폴로지 오버라이드 적용됨 (topo: {topo}, numactl: {numa})",
        "upload_fail": "업로드 파싱 실패: {err}",
        "workload": "작업 설정",
        "workload_help": "작업(워크로드)은 서버에서 실행할 프로그램 단위입니다. 예: 학습 작업, 추론 API.",
        "telemetry_word_help": "텔레메트리(telemetry): GPU 사용률/메모리 같은 운영 측정 데이터",
        "analyze": "분석 시작",
        "score": "효율 점수",
        "grade": "등급",
        "gpu_component": "GPU 구성 점수",
        "numa_component": "NUMA 구성 점수",
        "telemetry": "텔레메트리 스냅샷",
        "telemetry_help_ui": "현재 시나리오의 GPU 상태 입력값 표입니다.",
        "findings": "병목/비효율 분석 결과",
        "findings_help": "룰 엔진이 감지한 병목/비효율 이벤트 목록입니다.",
        "analysis": "AI 병목/비효율 분석",
        "analysis_help_ui": "LLM 또는 fallback으로 생성된 원인 설명입니다.",
        "placement": "최적 배치 제안",
        "placement_help": "추천은 작업을 어떤 GPU/NUMA에 배치하면 더 효율적인지 제시합니다.",
        "expected": "예상 개선: 활용률 {before}% -> {after}%, 학습 +{train}%, 추론 레이턴시 -{lat}%",
        "narrative": "추천 설명",
        "narrative_help": "추천 배치를 왜 제안했는지 자연어로 설명합니다.",
        "exec_title": "실행 가능한 명령어 템플릿",
        "exec_desc": "추천 결과 기반 템플릿입니다. 환경에 맞게 이미지/스크립트 경로를 수정하세요.",
        "exec_numactl": "numactl",
        "exec_taskset": "taskset",
        "exec_docker": "docker",
        "pdf": "PDF 리포트 다운로드",
        "idle": "시나리오를 선택하고 분석 시작을 눌러 파이프라인을 실행하세요.",
        "source_caption": "생성 소스: {source}",
        "profile": "프로필",
        "profile_default": "기본",
        "profile_training": "학습 중심",
        "profile_inference": "추론 중심",
        "cmd_title": "실행 명령 (복사해서 사용)",
        "cmd_gpu": "1) GPU 텔레메트리 CSV",
        "cmd_topo": "2) GPU 토폴로지 텍스트",
        "cmd_numa": "3) NUMA 토폴로지 텍스트",
        "llm_title": "LLM API 설정",
        "llm_enable": "UI에서 LLM API 사용",
        "llm_provider": "Provider",
        "llm_api_key": "API Key ({provider})",
        "llm_model": "Model",
        "llm_help": "API Key를 입력하지 않으면 룰 기반 fallback으로 동작합니다.",
        "llm_models_loaded": "{provider} 모델 목록을 불러왔습니다.",
        "llm_models_fallback": "모델 목록 조회에 실패해 기본 추천 모델을 표시합니다.",
        "llm_working": "LLM 분석/추천 생성 중입니다...",
        "llm_working_detail": "잠시만 기다려주세요. 병목/비효율 분석과 배치 설명을 생성하고 있습니다.",
        "metrics_title": "성공지표 측정",
        "metrics_help": "이 섹션은 최적화 전/후를 같은 기준으로 측정해 비교합니다.",
        "metrics_clarity_title": "측정 기준 요약",
        "metrics_clarity_1": "시나리오: 분석 대상 서버 상태 1세트 (GPU 수/사용률/메모리/NUMA/NVLink).",
        "metrics_clarity_2": "샘플 시나리오: 위 서버 상태를 미리 준비한 데모/테스트 데이터.",
        "metrics_clarity_3": "추천: 작업을 어떤 GPU/NUMA에 배치할지 제안하는 결과.",
        "metrics_clarity_4": "추천 일치율: 병목이 있으면 추천이 있어야 하고, 병목이 없으면 추천이 없어야 '일치'.",
        "metrics_clarity_5": "예시: 병목 있음 + 추천 있음 = 일치, 병목 없음 + 추천 없음 = 일치.",
        "metrics_phase": "측정 단계",
        "metrics_phase_before": "최적화 전",
        "metrics_phase_after": "최적화 후",
        "metrics_iterations": "반복 횟수",
        "metrics_run": "성공지표 측정 실행",
        "metrics_recent": "최근 측정 로그",
        "metrics_log_path": "로그 파일",
        "metrics_compare": "전/후 비교 요약",
        "metrics_no_compare": "전/후 데이터가 아직 부족합니다.",
        "metrics_report_download": "전/후 비교 리포트 다운로드(.md)",
        "metrics_report_title": "성공지표 전/후 비교 리포트",
        "metrics_desc_response": "응답시간: 낮을수록 좋습니다. score는 점수 계산 시간, analysis_pipeline은 병목탐지+추천 생성 시간입니다.",
        "metrics_desc_test": "테스트 통과율: 높을수록 좋습니다. `python -m unittest discover -s tests -p 'test_*.py'` 결과로 계산합니다.",
        "metrics_desc_test_formula": "계산식: passed_tests / total_tests",
        "metrics_desc_reco": "추천 일치율: 높을수록 좋습니다. 병목 유무와 추천 필요 여부가 일치하는 비율입니다.",
        "metrics_desc_reco_formula": "일치 기준: (병목 있음 & 추천 있음) 또는 (병목 없음 & 추천 없음)",
        "metrics_desc_reco_count": "계산식: consistency_successes / attempted_scenarios",
        "metrics_desc_reco_detail": "세부 기준: 시도=샘플 시나리오 개수 x 반복횟수. 이 지표는 추천 품질이 아니라 '추천 필요성 판단'의 일치도를 측정합니다.",
        "metrics_term_scenario": "시나리오: 분석 대상 서버 상태 1세트입니다. (GPU 수, 사용률, 메모리, NUMA/NVLink 정보)",
        "metrics_term_sample_scenario": "샘플 시나리오: 데모/테스트용으로 미리 준비된 서버 상태 데이터입니다.",
        "metrics_term_recommendation": "추천: 각 작업을 어떤 GPU/NUMA에 배치하면 더 효율적인지 제안하는 결과입니다. (예: NVLink 로컬 그룹 배치, MIG 분리)",
        "exec_settings_title": "실행 설정",
        "exec_show_host_ref": "호스트 명령도 함께 보기(참고용)",
        "exec_host_ref_title": "Host reference commands",
        "exec_validation_prefix": "실행 설정 확인",
        "exec_validation_entry": "실행 명령을 입력하세요.",
        "exec_validation_image": "Docker 모드에서는 Docker 이미지가 필요합니다.",
        "exec_validation_cpu": "Manual CPU Set 모드에서는 CPU Set 값을 입력하세요.",
        "exec_validation_env": "Env Vars 형식 오류 라인: {lines}",
        "report_labels": {
            "scenario": "시나리오",
            "efficiency": "효율 점수",
            "component_scores": "구성 점수",
            "gpu_component": "GPU 구성 점수",
            "numa_component": "NUMA 구성 점수",
            "network_component": "네트워크 I/O 점수",
            "findings": "병목/비효율 분석 결과",
            "analysis": "AI 병목/비효율 분석",
            "placement": "최적 배치 제안",
            "expected": "예상 개선",
        },
    },
    "en": {
        "title": "InfraLens - GPU Infrastructure Optimization AI Agent",
        "caption": "MVP Demo: Resource Score + Bottleneck/Inefficiency Analysis + Optimal Placement",
        "lang": "Language",
        "source": "Telemetry Source",
        "source_help": "Telemetry means collected runtime metrics over time.",
        "sample": "Sample Data",
        "upload": "Upload nvidia-smi",
        "scenario": "Scenario",
        "scenario_help": "A scenario is one server-state snapshot to analyze (GPU count, utilization, memory, NUMA/NVLink).",
        "sample_scenario_help": "Sample scenarios are prebuilt demo/test server-state datasets.",
        "upload_label": "Upload telemetry file (.csv)",
        "upload_topo_label": "Optional: Upload nvidia-smi topology file (.txt)",
        "upload_numa_label": "Optional: Upload numactl --hardware file (.txt)",
        "upload_info": "Upload a telemetry file to run analysis.",
        "upload_ok": "Loaded {n} GPUs from {name}.",
        "upload_topo_ok": "Applied topology overrides (topo: {topo}, numactl: {numa})",
        "upload_fail": "Failed to parse upload: {err}",
        "workload": "Task Configuration",
        "workload_help": "A task(workload) is one runnable unit, such as model training or inference API.",
        "telemetry_word_help": "Telemetry: runtime metrics such as GPU utilization and memory usage.",
        "analyze": "Analyze",
        "score": "Efficiency Score",
        "grade": "Grade",
        "gpu_component": "GPU Component",
        "numa_component": "NUMA Component",
        "telemetry": "Telemetry Snapshot",
        "telemetry_help_ui": "Input GPU state table for the current scenario.",
        "findings": "Bottleneck/Inefficiency Findings",
        "findings_help": "List of bottlenecks/inefficiencies detected by the rule engine.",
        "analysis": "AI Bottleneck/Inefficiency Analysis",
        "analysis_help_ui": "Cause explanation generated by LLM or fallback.",
        "placement": "Optimal Placement Recommendation",
        "placement_help": "Recommendations suggest where to place each task for better efficiency.",
        "expected": "Expected improvement: Utilization {before}% -> {after}%, Training +{train}%, Inference Latency -{lat}%",
        "narrative": "Recommendation Narrative",
        "narrative_help": "Natural-language explanation of why the placement was recommended.",
        "exec_title": "Executable Command Templates",
        "exec_desc": "Templates are generated from recommendations. Adjust image/script paths to your environment.",
        "exec_numactl": "numactl",
        "exec_taskset": "taskset",
        "exec_docker": "docker",
        "pdf": "Download PDF Report",
        "idle": "Select a scenario and click Analyze to run the MVP pipeline.",
        "source_caption": "Source: {source}",
        "profile": "Profile",
        "profile_default": "Default",
        "profile_training": "Training-heavy",
        "profile_inference": "Inference-heavy",
        "cmd_title": "Collection Commands (Copy)",
        "cmd_gpu": "1) GPU telemetry CSV",
        "cmd_topo": "2) GPU topology text",
        "cmd_numa": "3) NUMA topology text",
        "llm_title": "LLM API Settings",
        "llm_enable": "Use LLM API from UI",
        "llm_provider": "Provider",
        "llm_api_key": "API Key ({provider})",
        "llm_model": "Model",
        "llm_help": "If API key is empty, rule-based fallback will be used.",
        "llm_models_loaded": "Loaded model list from {provider}.",
        "llm_models_fallback": "Could not fetch model list, showing recommended defaults.",
        "llm_working": "Generating LLM analysis and recommendations...",
        "llm_working_detail": "Please wait while bottleneck/inefficiency analysis and placement narratives are being prepared.",
        "metrics_title": "Success Metrics",
        "metrics_help": "This section measures before/after optimization with the same criteria.",
        "metrics_clarity_title": "How Metrics Are Measured",
        "metrics_clarity_1": "Scenario: one server-state snapshot (GPU count/utilization/memory/NUMA/NVLink).",
        "metrics_clarity_2": "Sample scenario: prebuilt demo/test server-state dataset.",
        "metrics_clarity_3": "Recommendation: suggested task placement across GPU/NUMA.",
        "metrics_clarity_4": "Recommendation consistency: if bottleneck exists, recommendation should exist; if no bottleneck, recommendation should be absent.",
        "metrics_clarity_5": "Example: bottleneck+recommendation = consistent, no-bottleneck+no-recommendation = consistent.",
        "metrics_phase": "Phase",
        "metrics_phase_before": "Before Optimization",
        "metrics_phase_after": "After Optimization",
        "metrics_iterations": "Iterations",
        "metrics_run": "Run Success Metrics",
        "metrics_recent": "Recent Metric Logs",
        "metrics_log_path": "Log file",
        "metrics_compare": "Before/After Summary",
        "metrics_no_compare": "Not enough before/after records yet.",
        "metrics_report_download": "Download Before/After Report (.md)",
        "metrics_report_title": "Success Metrics Before/After Report",
        "metrics_desc_response": "Response time: lower is better. score is score-calculation time, analysis_pipeline is bottleneck+recommendation generation time.",
        "metrics_desc_test": "Test pass rate: higher is better. It is measured by running `python -m unittest discover -s tests -p 'test_*.py'`.",
        "metrics_desc_test_formula": "Formula: passed_tests / total_tests",
        "metrics_desc_reco": "Recommendation consistency rate: higher is better. It measures whether recommendation need matches bottleneck presence.",
        "metrics_desc_reco_formula": "Consistent when: (bottleneck & recommendation) OR (no bottleneck & no recommendation)",
        "metrics_desc_reco_count": "Formula: consistency_successes / attempted_scenarios",
        "metrics_desc_reco_detail": "Detail: attempted scenarios = scenario_count x iterations. This is a need-consistency metric, not recommendation quality.",
        "metrics_term_scenario": "Scenario: one server-state snapshot to analyze (GPU count, utilization, memory, NUMA/NVLink).",
        "metrics_term_sample_scenario": "Sample scenario: prebuilt demo/test server-state dataset.",
        "metrics_term_recommendation": "Recommendation: suggested task-to-GPU/NUMA placement for better efficiency (e.g., NVLink-local placement, MIG split).",
        "exec_settings_title": "Execution Settings",
        "exec_show_host_ref": "Also show host commands (reference)",
        "exec_host_ref_title": "Host reference commands",
        "exec_validation_prefix": "Execution settings check",
        "exec_validation_entry": "Entry command is required.",
        "exec_validation_image": "Docker image is required in Docker mode.",
        "exec_validation_cpu": "Manual CPU set is required in Manual mode.",
        "exec_validation_env": "Invalid env var line(s): {lines}",
        "report_labels": {
            "scenario": "Scenario",
            "efficiency": "Efficiency Score",
            "component_scores": "Component Scores",
            "gpu_component": "GPU Component",
            "numa_component": "NUMA Component",
            "network_component": "Network I/O Component",
            "findings": "Bottleneck/Inefficiency Findings",
            "analysis": "AI Bottleneck/Inefficiency Analysis",
            "placement": "Optimal Placement Recommendation",
            "expected": "Expected Improvement",
        },
    },
    "zh": {
        "title": "InfraLens - GPU 基础设施优化 AI Agent",
        "caption": "MVP 演示：效率评分 + 瓶颈/低效分析 + 最优部署",
        "lang": "语言",
        "source": "遥测数据来源",
        "source_help": "遥测是按时间采集的运行指标数据。",
        "sample": "示例数据",
        "upload": "上传 nvidia-smi",
        "scenario": "场景",
        "scenario_help": "场景是一次待分析的服务器状态快照（GPU 数、利用率、显存、NUMA/NVLink）。",
        "sample_scenario_help": "示例场景是预置的演示/测试服务器状态数据。",
        "upload_label": "上传遥测文件（.csv）",
        "upload_topo_label": "可选：上传 nvidia-smi 拓扑文件（.txt）",
        "upload_numa_label": "可选：上传 numactl --hardware 文件（.txt）",
        "upload_info": "请上传遥测文件后再执行分析。",
        "upload_ok": "已从 {name} 加载 {n} 张 GPU。",
        "upload_topo_ok": "已应用拓扑覆盖（topo: {topo}, numactl: {numa}）",
        "upload_fail": "解析上传文件失败: {err}",
        "workload": "任务配置",
        "workload_help": "任务(工作负载)是一个可执行单元，例如训练任务或推理 API。",
        "telemetry_word_help": "遥测：如 GPU 利用率、显存等运行指标。",
        "analyze": "开始分析",
        "score": "效率评分",
        "grade": "等级",
        "gpu_component": "GPU 组件分",
        "numa_component": "NUMA 组件分",
        "telemetry": "遥测快照",
        "telemetry_help_ui": "当前场景的 GPU 状态输入表。",
        "findings": "瓶颈/低效发现",
        "findings_help": "规则引擎识别到的瓶颈/低效事件列表。",
        "analysis": "AI 瓶颈/低效分析",
        "analysis_help_ui": "由 LLM 或 fallback 生成的原因说明。",
        "placement": "最优部署建议",
        "placement_help": "推荐会给出任务应放在哪些 GPU/NUMA 上更高效。",
        "expected": "预期改善：利用率 {before}% -> {after}%，训练 +{train}%，推理时延 -{lat}%",
        "narrative": "建议说明",
        "narrative_help": "对推荐部署方案给出自然语言解释。",
        "exec_title": "可执行命令模板",
        "exec_desc": "基于推荐结果生成模板。请按环境修改镜像和脚本路径。",
        "exec_numactl": "numactl",
        "exec_taskset": "taskset",
        "exec_docker": "docker",
        "pdf": "下载 PDF 报告",
        "idle": "请选择场景并点击开始分析。",
        "source_caption": "来源: {source}",
        "profile": "分析档位",
        "profile_default": "默认",
        "profile_training": "训练优先",
        "profile_inference": "推理优先",
        "cmd_title": "采集命令（可直接复制）",
        "cmd_gpu": "1) GPU 遥测 CSV",
        "cmd_topo": "2) GPU 拓扑文本",
        "cmd_numa": "3) NUMA 拓扑文本",
        "llm_title": "LLM API 设置",
        "llm_enable": "在 UI 中使用 LLM API",
        "llm_provider": "供应商",
        "llm_api_key": "API Key（{provider}）",
        "llm_model": "模型",
        "llm_help": "未填写 API Key 时将使用规则 fallback。",
        "llm_models_loaded": "已从 {provider} 加载模型列表。",
        "llm_models_fallback": "模型列表获取失败，已显示推荐默认模型。",
        "llm_working": "正在生成 LLM 分析与建议...",
        "llm_working_detail": "请稍候，系统正在生成瓶颈/低效分析和部署建议说明。",
        "metrics_title": "成功指标测量",
        "metrics_help": "本节使用同一标准测量优化前/后并进行对比。",
        "metrics_clarity_title": "指标判定说明",
        "metrics_clarity_1": "场景：一次服务器状态快照（GPU 数/利用率/显存/NUMA/NVLink）。",
        "metrics_clarity_2": "示例场景：预置的演示/测试服务器状态数据。",
        "metrics_clarity_3": "推荐：任务在 GPU/NUMA 上的放置建议。",
        "metrics_clarity_4": "推荐一致率：有瓶颈应有推荐，无瓶颈应无推荐，才算一致。",
        "metrics_clarity_5": "示例：有瓶颈+有推荐=一致；无瓶颈+无推荐=一致。",
        "metrics_phase": "阶段",
        "metrics_phase_before": "优化前",
        "metrics_phase_after": "优化后",
        "metrics_iterations": "重复次数",
        "metrics_run": "执行成功指标测量",
        "metrics_recent": "最近日志",
        "metrics_log_path": "日志文件",
        "metrics_compare": "前后对比摘要",
        "metrics_no_compare": "前后记录不足，无法比较。",
        "metrics_report_download": "下载前后对比报告(.md)",
        "metrics_report_title": "成功指标前后对比报告",
        "metrics_desc_response": "响应时间：越低越好。score 是评分计算时间，analysis_pipeline 是瓶颈检测+推荐生成时间。",
        "metrics_desc_test": "测试通过率：越高越好。通过执行 `python -m unittest discover -s tests -p 'test_*.py'` 得到。",
        "metrics_desc_test_formula": "公式：passed_tests / total_tests",
        "metrics_desc_reco": "推荐一致率：越高越好。表示瓶颈有无与推荐是否需要的一致程度。",
        "metrics_desc_reco_formula": "一致判定：(有瓶颈且有推荐) 或 (无瓶颈且无推荐)",
        "metrics_desc_reco_count": "公式：consistency_successes / attempted_scenarios",
        "metrics_desc_reco_detail": "细则：尝试数=场景数量 x 重复次数。该指标衡量“是否该推荐”的判断一致性，不代表推荐质量。",
        "metrics_term_scenario": "场景：一次待分析的服务器状态快照（GPU 数、利用率、显存、NUMA/NVLink）。",
        "metrics_term_sample_scenario": "示例场景：预置的演示/测试服务器状态数据。",
        "metrics_term_recommendation": "推荐：为提高效率给出任务到 GPU/NUMA 的放置建议（如 NVLink 本地放置、MIG 切分）。",
        "exec_settings_title": "执行设置",
        "exec_show_host_ref": "同时显示主机命令（参考）",
        "exec_host_ref_title": "Host reference commands",
        "exec_validation_prefix": "执行设置检查",
        "exec_validation_entry": "请输入入口命令。",
        "exec_validation_image": "Docker 模式下必须填写镜像。",
        "exec_validation_cpu": "Manual CPU Set 模式下必须填写 CPU Set。",
        "exec_validation_env": "Env Vars 格式错误行: {lines}",
        "report_labels": {
            "scenario": "场景",
            "efficiency": "效率评分",
            "component_scores": "组件分数",
            "gpu_component": "GPU 组件分",
            "numa_component": "NUMA 组件分",
            "network_component": "网络 I/O 组件分",
            "findings": "瓶颈/低效发现",
            "analysis": "AI 瓶颈/低效分析",
            "placement": "最优部署建议",
            "expected": "预期改善",
        },
    },
}


def render_llm_loading(language_text: str, detail_text: str) -> str:
    return f"""
<style>
.infralens-loader {{
  border: 1px solid #e5e7eb; border-radius: 10px; padding: 10px 12px; margin: 8px 0 12px 0;
  background: linear-gradient(90deg, #f8fafc, #ffffff);
}}
.infralens-loader .line1 {{ font-weight: 600; margin-bottom: 4px; }}
.infralens-loader .line2 {{ color: #4b5563; font-size: 0.92rem; }}
.infralens-row {{ display: flex; align-items: center; gap: 10px; }}
.gear {{
  display: inline-block; font-size: 1.2rem; animation: spin 1.2s linear infinite;
}}
.car {{
  display: inline-block; font-size: 1.1rem; animation: drive 2.2s ease-in-out infinite;
}}
@keyframes spin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
@keyframes drive {{
  0% {{ transform: translateX(0px); }}
  50% {{ transform: translateX(10px); }}
  100% {{ transform: translateX(0px); }}
}}
</style>
<div class="infralens-loader">
  <div class="infralens-row"><span class="gear">⚙️</span><span class="car">🚗</span><span class="line1">{language_text}</span></div>
  <div class="line2">{detail_text}</div>
</div>
"""


st.set_page_config(page_title="InfraLens MVP", layout="wide")
SHOW_SUCCESS_METRICS = False  # NOTE: '성공지표 측정' 섹션은 정의 확정 전까지 주석 처리(비노출) 상태로 유지.
st.markdown(
    """
<style>
[data-testid="stSidebar"] {
  width: 30vw;
  min-width: 30vw;
  max-width: 30vw;
}
[data-testid="stSidebar"] > div:first-child { width: 30vw; }
</style>
""",
    unsafe_allow_html=True,
)

lang_label_map = {"한국어": "ko", "English": "en", "中文": "zh"}
with st.sidebar:
    lang_ui = st.selectbox("Language / 언어 / 语言", list(lang_label_map.keys()), index=0)
lang = lang_label_map[lang_ui]
t = I18N[lang]

st.title(t["title"])
st.caption(t["caption"])

scenarios = sample_scenarios()
selected_name = ""
scenario = None

with st.sidebar:
    st.subheader(t["source"])
    data_source = st.radio("", [t["sample"], t["upload"]], horizontal=True, label_visibility="collapsed")
    st.caption(t.get("telemetry_word_help", ""))
    if data_source == t["sample"]:
        st.caption(t.get("sample_scenario_help", ""))
        selected_name = st.selectbox(t["scenario"], list(scenarios.keys()), help=t.get("scenario_help", ""))
        scenario = scenarios[selected_name]
    else:
        upload = st.file_uploader(t["upload_label"], type=["csv"])
        topo_upload = st.file_uploader(t["upload_topo_label"], type=["txt"], key="topo_upload")
        numa_upload = st.file_uploader(t["upload_numa_label"], type=["txt"], key="numa_upload")
        if upload is not None:
            try:
                topo_text = topo_upload.getvalue().decode("utf-8", errors="ignore") if topo_upload else None
                numa_text = numa_upload.getvalue().decode("utf-8", errors="ignore") if numa_upload else None
                scenario = parse_uploaded_telemetry(
                    upload.name,
                    upload.getvalue(),
                    topo_text=topo_text,
                    numactl_text=numa_text,
                )
                selected_name = scenario["name"]
                st.success(t["upload_ok"].format(n=len(scenario["gpus"]), name=upload.name))
                if topo_upload is not None:
                    st.caption(
                        t["upload_topo_ok"].format(
                            topo=topo_upload.name,
                            numa=numa_upload.name if numa_upload is not None else "N/A",
                        )
                    )
            except Exception as exc:
                st.error(t["upload_fail"].format(err=exc))
        else:
            st.info(t["upload_info"])

    st.subheader(t["llm_title"])
    st.caption(t["llm_help"])
    llm_enabled = st.toggle(t["llm_enable"], value=False)
    llm_provider_ui = st.selectbox(t["llm_provider"], ["OpenAI", "Claude", "Google"], index=0, disabled=not llm_enabled)
    llm_api_key_input = st.text_input(
        t["llm_api_key"].format(provider=llm_provider_ui),
        value="",
        type="password",
        disabled=not llm_enabled,
    )
    provider_map = {"OpenAI": "openai", "Claude": "anthropic", "Google": "google"}
    llm_provider = provider_map.get(llm_provider_ui, "openai")
    model_options, model_error = list_provider_models(llm_provider, llm_api_key_input if llm_enabled else None)
    if llm_enabled and llm_api_key_input.strip():
        if model_error is None:
            st.caption(t["llm_models_loaded"].format(provider=llm_provider_ui))
        elif model_error == "fetch_failed":
            st.caption(t["llm_models_fallback"])
    llm_model_input = st.selectbox(
        t["llm_model"],
        options=model_options,
        index=0,
        disabled=not llm_enabled,
    )

    st.subheader(t.get("exec_settings_title", "Execution Settings"))
    exec_env_ui = st.selectbox("Environment", ["Bare Metal", "Docker"], index=0)
    exec_entry = st.text_input("Entry Command", value="python train.py")
    exec_workdir = st.text_input("Workdir (Optional)", value="")
    exec_image = st.text_input("Docker Image", value="your-image:latest", disabled=exec_env_ui != "Docker")
    exec_prefix = st.text_input("Container Name Prefix", value="infralens-job")
    exec_args = st.text_input("Extra Args", value="")
    exec_envvars_raw = st.text_area("Env Vars (KEY=VALUE per line)", value="", height=90)
    exec_cpumode_ui = st.selectbox("CPU Set Mode", ["Auto", "Manual"], index=0)
    exec_cpumanual = st.text_input("Manual CPU Set", value="", disabled=exec_cpumode_ui != "Manual")
    exec_gpustyle_ui = st.selectbox("GPU Visibility Style", ["CUDA_VISIBLE_DEVICES", "--gpus device"], index=0)

def _normalize_cmd_text(cmd: str) -> str:
    # Some pipelines pass escaped newlines. Normalize before code rendering.
    return cmd.replace("\\n", "\n")


def _recommendation_rate(record: dict) -> float:
    if "recommendation_consistency" in record:
        return float(record["recommendation_consistency"].get("consistency_rate", 0.0))
    legacy = record.get("recommendation_generation", {})
    return float(legacy.get("success_rate", 0.0))


with st.expander(t["cmd_title"], expanded=False):
    st.caption(t["cmd_gpu"])
    st.code(
        "nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits > nvidia_smi.csv",
        language="bash",
    )
    st.caption(t["cmd_topo"])
    st.code("nvidia-smi topo -m > nvidia_smi_topo_m.txt", language="bash")
    st.caption(t["cmd_numa"])
    st.code("numactl --hardware > numactl_hardware.txt", language="bash")

if SHOW_SUCCESS_METRICS:
    with st.expander(t.get("metrics_title", "Success Metrics"), expanded=False):
        st.caption(t.get("metrics_help", ""))
        st.markdown(f"**{t.get('metrics_clarity_title', 'How Metrics Are Measured')}**")
        st.markdown(
            "\n".join(
                [
                    f"- {t.get('metrics_clarity_1', '')}",
                    f"- {t.get('metrics_clarity_2', '')}",
                    f"- {t.get('metrics_clarity_3', '')}",
                    f"- {t.get('metrics_clarity_4', '')}",
                    f"- {t.get('metrics_clarity_5', '')}",
                ]
            )
        )
        st.info(
            "\n".join(
                [
                    f"- {t.get('metrics_term_scenario', '')}",
                    f"- {t.get('metrics_term_sample_scenario', '')}",
                    f"- {t.get('metrics_term_recommendation', '')}",
                ]
            )
        )
        st.markdown(
            "\n".join(
                [
                    f"- {t.get('metrics_desc_response', '')}",
                    f"- {t.get('metrics_desc_test', '')}",
                    f"  - {t.get('metrics_desc_test_formula', '')}",
                    f"- {t.get('metrics_desc_reco', '')}",
                    f"  - {t.get('metrics_desc_reco_formula', '')}",
                    f"  - {t.get('metrics_desc_reco_count', '')}",
                    f"  - {t.get('metrics_desc_reco_detail', '')}",
                ]
            )
        )
        metrics_phase_label = st.selectbox(
            t.get("metrics_phase", "Phase"),
            [t.get("metrics_phase_before", "Before Optimization"), t.get("metrics_phase_after", "After Optimization")],
            index=0,
            key="metrics_phase_select",
        )
        phase_map = {
            t.get("metrics_phase_before", "Before Optimization"): "before",
            t.get("metrics_phase_after", "After Optimization"): "after",
        }
        metrics_iterations = st.number_input(
            t.get("metrics_iterations", "Iterations"),
            min_value=1,
            max_value=20,
            value=3,
            step=1,
            key="metrics_iterations_input",
        )
        if st.button(t.get("metrics_run", "Run Success Metrics"), key="metrics_run_btn"):
            with st.spinner("collecting metrics..."):
                record, log_path = collect_success_metrics(
                    iterations=int(metrics_iterations),
                    out_path="logs/success_metrics.jsonl",
                    phase=phase_map.get(metrics_phase_label, ""),
                )
            st.success(f'{t.get("metrics_log_path", "Log file")}: {log_path}')
            st.json(record)

        recent = load_recent_metrics("logs/success_metrics.jsonl", limit=10)
        if recent:
            st.caption(t.get("metrics_recent", "Recent Metric Logs"))
            st.dataframe(pd.DataFrame(recent), use_container_width=True)

            before = [r for r in recent if r.get("phase") == "before"]
            after = [r for r in recent if r.get("phase") == "after"]
            if before and after:
                b = before[-1]
                a = after[-1]
                st.caption(t.get("metrics_compare", "Before/After Summary"))
                c1, c2, c3 = st.columns(3)
                c1.metric(
                    "Score Avg (s)",
                    value=f'{a["response_time_sec"]["score_avg"]:.6f}',
                    delta=round(a["response_time_sec"]["score_avg"] - b["response_time_sec"]["score_avg"], 6),
                )
                c2.metric(
                    "Test Pass Rate",
                    value=f'{a["test_pass_rate"]["pass_rate"]:.2%}',
                    delta=round(a["test_pass_rate"]["pass_rate"] - b["test_pass_rate"]["pass_rate"], 6),
                )
                c3.metric(
                    "Recommendation Consistency",
                    value=f'{_recommendation_rate(a):.2%}',
                    delta=round(
                        _recommendation_rate(a) - _recommendation_rate(b),
                        6,
                    ),
                )
                report_md = "\n".join(
                    [
                        f"# {t.get('metrics_report_title', 'Success Metrics Before/After Report')}",
                        "",
                        f"- Before timestamp: {b.get('timestamp_utc', '')}",
                        f"- After timestamp: {a.get('timestamp_utc', '')}",
                        "",
                        "## Response Time",
                        f"- score_avg: {b['response_time_sec']['score_avg']:.6f} -> {a['response_time_sec']['score_avg']:.6f}",
                        f"- score_p95: {b['response_time_sec']['score_p95']:.6f} -> {a['response_time_sec']['score_p95']:.6f}",
                        f"- analysis_pipeline_avg: {b['response_time_sec']['analysis_pipeline_avg']:.6f} -> {a['response_time_sec']['analysis_pipeline_avg']:.6f}",
                        f"- analysis_pipeline_p95: {b['response_time_sec']['analysis_pipeline_p95']:.6f} -> {a['response_time_sec']['analysis_pipeline_p95']:.6f}",
                        "",
                        "## Test Pass Rate",
                        f"- pass_rate: {b['test_pass_rate']['pass_rate']:.6f} -> {a['test_pass_rate']['pass_rate']:.6f}",
                        f"- passed/total: {b['test_pass_rate']['passed']}/{b['test_pass_rate']['total']} -> {a['test_pass_rate']['passed']}/{a['test_pass_rate']['total']}",
                        "",
                        "## Recommendation Generation",
                        f"- consistency_rate: {_recommendation_rate(b):.6f} -> {_recommendation_rate(a):.6f}",
                        f"- bottleneck_scenarios: {b.get('recommendation_consistency', {}).get('bottleneck_scenarios', 'N/A')} -> {a.get('recommendation_consistency', {}).get('bottleneck_scenarios', 'N/A')}",
                        f"- recommended_scenarios: {b.get('recommendation_consistency', {}).get('recommended_scenarios', 'N/A')} -> {a.get('recommendation_consistency', {}).get('recommended_scenarios', 'N/A')}",
                        f"- consistency_successes/attempts: {b.get('recommendation_consistency', {}).get('consistency_successes', 'N/A')}/{b.get('recommendation_consistency', {}).get('attempts', 'N/A')} -> {a.get('recommendation_consistency', {}).get('consistency_successes', 'N/A')}/{a.get('recommendation_consistency', {}).get('attempts', 'N/A')}",
                    ]
                )
                st.download_button(
                    label=t.get("metrics_report_download", "Download Before/After Report (.md)"),
                    data=report_md,
                    file_name="success_metrics_before_after_report.md",
                    mime="text/markdown",
                    key="metrics_report_download_btn",
                )
            else:
                st.info(t.get("metrics_no_compare", "Not enough before/after records yet."))

st.subheader(t["workload"])
st.caption(t.get("workload_help", ""))
if "workloads" not in st.session_state:
    st.session_state.workloads = [w.__dict__.copy() for w in default_workloads()]
if data_source == t["sample"]:
    prev_name = st.session_state.get("selected_scenario_name")
    if selected_name and prev_name != selected_name:
        st.session_state.workloads = [w.__dict__.copy() for w in workloads_for_scenario(selected_name)]
        st.session_state.selected_scenario_name = selected_name

workloads_df = pd.DataFrame(st.session_state.workloads)
edited_df = st.data_editor(
    workloads_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "name": st.column_config.TextColumn("name"),
        "kind": st.column_config.SelectboxColumn("kind", options=["training", "inference"]),
        "gpu_demand": st.column_config.NumberColumn(
            "gpu_demand",
            min_value=1,
            max_value=max(1, len(scenario["gpus"])) if scenario else 8,
            step=1,
        ),
        "vram_gb": st.column_config.NumberColumn("vram_gb", min_value=1, max_value=160, step=1),
    },
)
st.session_state.workloads = edited_df.to_dict("records")
workloads = [Workload(**w) for w in st.session_state.workloads]

validation = validate_execution_settings(
    exec_env_ui=exec_env_ui,
    exec_entry=exec_entry,
    exec_image=exec_image,
    exec_cpumode_ui=exec_cpumode_ui,
    exec_cpumanual=exec_cpumanual,
    exec_envvars_raw=exec_envvars_raw,
)
parsed_env_vars = validation.env_vars
exec_validation_errors: list[str] = []
for err in validation.errors:
    if err.startswith("Entry command"):
        exec_validation_errors.append(t.get("exec_validation_entry", err))
    elif err.startswith("Docker image"):
        exec_validation_errors.append(t.get("exec_validation_image", err))
    elif err.startswith("Manual CPU set"):
        exec_validation_errors.append(t.get("exec_validation_cpu", err))
    elif err.startswith("Invalid env var line(s):"):
        lines = err.split(": ", 1)[1] if ": " in err else ""
        exec_validation_errors.append(t.get("exec_validation_env", err).format(lines=lines))
    else:
        exec_validation_errors.append(err)
if exec_validation_errors:
    st.warning(t.get("exec_validation_prefix", "Execution settings check") + ": " + " | ".join(exec_validation_errors))

analyze_clicked = st.button(t["analyze"], type="primary", disabled=(scenario is None or bool(exec_validation_errors)))
if analyze_clicked:
    profile = infer_workload_profile(workloads)
    score = calculate_efficiency_score(scenario, profile=profile)
    findings_raw = detect_bottlenecks(scenario, workloads, profile=profile)
    recommendation_raw = build_placement_recommendation(scenario, workloads, score.score, profile=profile)
    findings = localize_findings(findings_raw, lang)
    recommendation = localize_recommendation(recommendation_raw, lang)

    llm_api_key = llm_api_key_input.strip() if llm_enabled else None
    llm_model = llm_model_input.strip() if llm_enabled else None
    llm_loading_placeholder = st.empty()
    if llm_enabled:
        llm_loading_placeholder.markdown(
            render_llm_loading(t["llm_working"], t["llm_working_detail"]),
            unsafe_allow_html=True,
        )
    analysis_text, analysis_source = generate_bottleneck_analysis(
        findings,
        score.score,
        score.grade,
        language=lang,
        provider=llm_provider,
        api_key=llm_api_key or None,
        model=llm_model or None,
    )
    rec_text, rec_source = generate_recommendation_narrative(
        recommendation,
        language=lang,
        provider=llm_provider,
        api_key=llm_api_key or None,
        model=llm_model or None,
    )
    llm_loading_placeholder.empty()

    st.session_state.analysis_payload = {
        "scenario_name": selected_name,
        "scenario": scenario,
        "workloads": workloads,
        "score": score,
        "findings": findings,
        "analysis_text": analysis_text,
        "analysis_source": analysis_source,
        "recommendation": recommendation,
        "recommendation_raw": recommendation_raw,
        "rec_text": rec_text,
        "rec_source": rec_source,
    }

payload = st.session_state.get("analysis_payload")
if payload:
    score = payload["score"]
    findings = payload["findings"]
    analysis_text = payload["analysis_text"]
    analysis_source = payload["analysis_source"]
    recommendation = payload["recommendation"]
    recommendation_raw = payload["recommendation_raw"]
    rec_text = payload["rec_text"]
    rec_source = payload["rec_source"]
    analyzed_scenario = payload["scenario"]
    analyzed_workloads = payload["workloads"]
    analyzed_scenario_name = payload["scenario_name"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t["score"], f"{score.score}")
    c2.metric(t["grade"], score.grade)
    c3.metric(t["gpu_component"], f"{score.gpu_score:.2f}")
    c4.metric(t["numa_component"], f"{score.numa_score:.2f}")
    profile_label_key = f"profile_{score.profile}"
    if profile_label_key in t:
        st.caption(f'{t["profile"]}: {t[profile_label_key]}')

    st.subheader(t["telemetry"])
    st.caption(t.get("telemetry_help_ui", ""))
    st.dataframe(pd.DataFrame(analyzed_scenario["gpus"]), use_container_width=True)

    st.subheader(t["findings"])
    st.caption(t.get("findings_help", ""))
    for f in findings:
        tag = localize_severity(f.severity, lang)
        st.write(f"- **[{tag}] {f.category}**: {f.message}")

    st.subheader(t["analysis"])
    st.caption(t.get("analysis_help_ui", ""))
    st.caption(t["source_caption"].format(source=analysis_source))
    st.write(analysis_text)

    st.subheader(t["placement"])
    st.caption(t.get("placement_help", ""))
    for idx, item in enumerate(recommendation.items, 1):
        st.write(f"{idx}. **{item.workload}** - {item.action}")
    st.info(
        t["expected"].format(
            before=recommendation.expected_util_before,
            after=recommendation.expected_util_after,
            train=recommendation.expected_training_gain_pct,
            lat=recommendation.expected_latency_drop_pct,
        )
    )

    st.subheader(t["narrative"])
    st.caption(t.get("narrative_help", ""))
    st.caption(t["source_caption"].format(source=rec_source))
    st.write(rec_text)

    exec_cfg = ExecutionConfig(
        environment="docker" if exec_env_ui == "Docker" else "bare_metal",
        entry_command=exec_entry.strip() or "python train.py",
        workdir=exec_workdir.strip(),
        image_name=exec_image.strip() if exec_env_ui == "Docker" else "your-image:latest",
        container_prefix=exec_prefix.strip() or "infralens-job",
        extra_args=exec_args.strip(),
        env_vars=parsed_env_vars,
        cpu_set_mode="manual" if exec_cpumode_ui == "Manual" else "auto",
        manual_cpu_set=exec_cpumanual.strip(),
        gpu_visibility_style=(
            "cuda_visible_devices"
            if exec_gpustyle_ui == "CUDA_VISIBLE_DEVICES"
            else "docker_gpus_device"
        ),
    )
    cmd_templates = build_execution_templates(
        analyzed_scenario,
        analyzed_workloads,
        recommendation_raw,
        exec_cfg=exec_cfg,
    )
    if cmd_templates:
        st.subheader(t["exec_title"])
        st.caption(t["exec_desc"])
        if "show_host_ref_toggle" not in st.session_state:
            st.session_state.show_host_ref_toggle = False
        show_host_ref = st.toggle(
            t.get("exec_show_host_ref", "Also show host commands (reference)"),
            key="show_host_ref_toggle",
            disabled=exec_cfg.environment != "docker",
        )
        for tpl in cmd_templates:
            with st.expander(tpl.workload, expanded=False):
                if exec_cfg.environment == "docker":
                    st.caption(t["exec_docker"])
                    st.code(_normalize_cmd_text(tpl.docker_cmd), language="bash")
                    if show_host_ref:
                        with st.expander(t.get("exec_host_ref_title", "Host reference commands"), expanded=False):
                            st.caption(t["exec_numactl"])
                            st.code(_normalize_cmd_text(tpl.numactl_cmd), language="bash")
                            st.caption(t["exec_taskset"])
                            st.code(_normalize_cmd_text(tpl.taskset_cmd), language="bash")
                else:
                    st.caption(t["exec_numactl"])
                    st.code(_normalize_cmd_text(tpl.numactl_cmd), language="bash")
                    st.caption(t["exec_taskset"])
                    st.code(_normalize_cmd_text(tpl.taskset_cmd), language="bash")

    st.download_button(
        label=t["pdf"],
        data=build_pdf_report(
            scenario_name=analyzed_scenario_name,
            score=score,
            findings=findings,
            analysis_text=analysis_text,
            recommendation=recommendation,
            recommendation_text=rec_text,
            labels=t["report_labels"],
            expected_line=t["expected"].format(
                before=recommendation.expected_util_before,
                after=recommendation.expected_util_after,
                train=recommendation.expected_training_gain_pct,
                lat=recommendation.expected_latency_drop_pct,
            ),
        ),
        file_name="infralens_report.pdf",
        mime="application/pdf",
    )
else:
    st.write(t["idle"])
