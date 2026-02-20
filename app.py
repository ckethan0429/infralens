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


I18N = {
    "ko": {
        "title": "InfraLens - GPU 인프라 최적화 AI 에이전트",
        "caption": "MVP 데모: 효율 점수 + 병목 분석 + 최적 배치",
        "lang": "언어",
        "source": "텔레메트리 소스",
        "sample": "샘플 데이터",
        "upload": "nvidia-smi 업로드",
        "scenario": "시나리오",
        "upload_label": "텔레메트리 파일 업로드 (.csv)",
        "upload_topo_label": "선택: nvidia-smi topo 파일 업로드 (.txt)",
        "upload_numa_label": "선택: numactl --hardware 파일 업로드 (.txt)",
        "upload_info": "분석을 위해 텔레메트리 파일을 업로드하세요.",
        "upload_ok": "GPU {n}개를 {name}에서 로드했습니다.",
        "upload_topo_ok": "토폴로지 오버라이드 적용됨 (topo: {topo}, numactl: {numa})",
        "upload_fail": "업로드 파싱 실패: {err}",
        "workload": "워크로드 설정",
        "analyze": "분석 시작",
        "score": "효율 점수",
        "grade": "등급",
        "gpu_component": "GPU 구성 점수",
        "numa_component": "NUMA 구성 점수",
        "telemetry": "텔레메트리 스냅샷",
        "findings": "병목 분석 결과",
        "analysis": "AI 병목 분석",
        "placement": "최적 배치 제안",
        "expected": "예상 개선: 활용률 {before}% -> {after}%, 학습 +{train}%, 추론 레이턴시 -{lat}%",
        "narrative": "추천 설명",
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
        "llm_working_detail": "잠시만 기다려주세요. 병목 분석과 배치 설명을 생성하고 있습니다.",
        "report_labels": {
            "scenario": "시나리오",
            "efficiency": "효율 점수",
            "component_scores": "구성 점수",
            "gpu_component": "GPU 구성 점수",
            "numa_component": "NUMA 구성 점수",
            "network_component": "네트워크 I/O 점수",
            "findings": "병목 분석 결과",
            "analysis": "AI 병목 분석",
            "placement": "최적 배치 제안",
            "expected": "예상 개선",
        },
    },
    "en": {
        "title": "InfraLens - GPU Infrastructure Optimization AI Agent",
        "caption": "MVP Demo: Resource Score + Bottleneck Analysis + Optimal Placement",
        "lang": "Language",
        "source": "Telemetry Source",
        "sample": "Sample Data",
        "upload": "Upload nvidia-smi",
        "scenario": "Scenario",
        "upload_label": "Upload telemetry file (.csv)",
        "upload_topo_label": "Optional: Upload nvidia-smi topology file (.txt)",
        "upload_numa_label": "Optional: Upload numactl --hardware file (.txt)",
        "upload_info": "Upload a telemetry file to run analysis.",
        "upload_ok": "Loaded {n} GPUs from {name}.",
        "upload_topo_ok": "Applied topology overrides (topo: {topo}, numactl: {numa})",
        "upload_fail": "Failed to parse upload: {err}",
        "workload": "Workload Configuration",
        "analyze": "Analyze",
        "score": "Efficiency Score",
        "grade": "Grade",
        "gpu_component": "GPU Component",
        "numa_component": "NUMA Component",
        "telemetry": "Telemetry Snapshot",
        "findings": "Bottleneck Findings",
        "analysis": "AI Bottleneck Analysis",
        "placement": "Optimal Placement Recommendation",
        "expected": "Expected improvement: Utilization {before}% -> {after}%, Training +{train}%, Inference Latency -{lat}%",
        "narrative": "Recommendation Narrative",
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
        "llm_working_detail": "Please wait while bottleneck analysis and placement narratives are being prepared.",
        "report_labels": {
            "scenario": "Scenario",
            "efficiency": "Efficiency Score",
            "component_scores": "Component Scores",
            "gpu_component": "GPU Component",
            "numa_component": "NUMA Component",
            "network_component": "Network I/O Component",
            "findings": "Bottleneck Findings",
            "analysis": "AI Bottleneck Analysis",
            "placement": "Optimal Placement Recommendation",
            "expected": "Expected Improvement",
        },
    },
    "zh": {
        "title": "InfraLens - GPU 基础设施优化 AI Agent",
        "caption": "MVP 演示：效率评分 + 瓶颈分析 + 最优部署",
        "lang": "语言",
        "source": "遥测数据来源",
        "sample": "示例数据",
        "upload": "上传 nvidia-smi",
        "scenario": "场景",
        "upload_label": "上传遥测文件（.csv）",
        "upload_topo_label": "可选：上传 nvidia-smi 拓扑文件（.txt）",
        "upload_numa_label": "可选：上传 numactl --hardware 文件（.txt）",
        "upload_info": "请上传遥测文件后再执行分析。",
        "upload_ok": "已从 {name} 加载 {n} 张 GPU。",
        "upload_topo_ok": "已应用拓扑覆盖（topo: {topo}, numactl: {numa}）",
        "upload_fail": "解析上传文件失败: {err}",
        "workload": "工作负载配置",
        "analyze": "开始分析",
        "score": "效率评分",
        "grade": "等级",
        "gpu_component": "GPU 组件分",
        "numa_component": "NUMA 组件分",
        "telemetry": "遥测快照",
        "findings": "瓶颈发现",
        "analysis": "AI 瓶颈分析",
        "placement": "最优部署建议",
        "expected": "预期改善：利用率 {before}% -> {after}%，训练 +{train}%，推理时延 -{lat}%",
        "narrative": "建议说明",
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
        "llm_working_detail": "请稍候，系统正在生成瓶颈分析和部署建议说明。",
        "report_labels": {
            "scenario": "场景",
            "efficiency": "效率评分",
            "component_scores": "组件分数",
            "gpu_component": "GPU 组件分",
            "numa_component": "NUMA 组件分",
            "network_component": "网络 I/O 组件分",
            "findings": "瓶颈发现",
            "analysis": "AI 瓶颈分析",
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
    data_source = st.radio(t["source"], [t["sample"], t["upload"]], horizontal=True)
    if data_source == t["sample"]:
        selected_name = st.selectbox(t["scenario"], list(scenarios.keys()))
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

    st.subheader("Execution Settings")
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


def _parse_env_vars(raw: str) -> tuple[dict[str, str], list[int]]:
    out: dict[str, str] = {}
    invalid_lines: list[int] = []
    for idx, line in enumerate(raw.splitlines(), 1):
        token = line.strip()
        if not token:
            continue
        if "=" not in token:
            invalid_lines.append(idx)
            continue
        k, v = token.split("=", 1)
        key = k.strip()
        if key:
            out[key] = v.strip()
        else:
            invalid_lines.append(idx)
    return out, invalid_lines


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

st.subheader(t["workload"])
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

parsed_env_vars, invalid_env_lines = _parse_env_vars(exec_envvars_raw)
exec_validation_errors: list[str] = []
if not exec_entry.strip():
    exec_validation_errors.append("Entry command is required.")
if exec_env_ui == "Docker" and not exec_image.strip():
    exec_validation_errors.append("Docker image is required in Docker mode.")
if exec_cpumode_ui == "Manual" and not exec_cpumanual.strip():
    exec_validation_errors.append("Manual CPU set is required in Manual mode.")
if invalid_env_lines:
    exec_validation_errors.append(f"Invalid env var line(s): {','.join(str(i) for i in invalid_env_lines)}")
if exec_validation_errors:
    st.warning("Execution settings check: " + " | ".join(exec_validation_errors))

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
    st.dataframe(pd.DataFrame(analyzed_scenario["gpus"]), use_container_width=True)

    st.subheader(t["findings"])
    for f in findings:
        tag = localize_severity(f.severity, lang)
        st.write(f"- **[{tag}] {f.category}**: {f.message}")

    st.subheader(t["analysis"])
    st.caption(t["source_caption"].format(source=analysis_source))
    st.write(analysis_text)

    st.subheader(t["placement"])
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
        show_host_ref = False
        if exec_cfg.environment == "docker":
            show_host_ref = st.toggle("Also show host commands", value=False, key="show_host_ref_toggle")
        for tpl in cmd_templates:
            with st.expander(tpl.workload, expanded=False):
                if exec_cfg.environment == "docker":
                    st.caption(t["exec_docker"])
                    st.code(tpl.docker_cmd, language="bash")
                    if show_host_ref:
                        st.caption(t["exec_numactl"])
                        st.code(tpl.numactl_cmd, language="bash")
                        st.caption(t["exec_taskset"])
                        st.code(tpl.taskset_cmd, language="bash")
                else:
                    st.caption(t["exec_numactl"])
                    st.code(tpl.numactl_cmd, language="bash")
                    st.caption(t["exec_taskset"])
                    st.code(tpl.taskset_cmd, language="bash")

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
