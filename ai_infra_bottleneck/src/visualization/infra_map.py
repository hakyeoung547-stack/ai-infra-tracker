"""
AI 인프라 동적 맵 시각화 + 섹터 트래커 대시보드

실행:
    streamlit run src/visualization/infra_map.py
"""

from pathlib import Path
import pandas as pd
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

try:
    import networkx as nx
except ImportError:
    nx = None

try:
    from pyvis.network import Network
except ImportError:
    Network = None

try:
    import streamlit as st
except ImportError:
    st = None

try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    px = None
    go = None

DATA_DIR = ROOT / "data"
COMPANIES_CSV = DATA_DIR / "reference" / "companies.csv"

# ---------------------------------------------------------------------------
# 공급망 엣지 정의
# ---------------------------------------------------------------------------

SUPPLY_EDGES = [
    ("AMAT", "TSM",  "반도체 장비"),
    ("LRCX", "TSM",  "반도체 장비"),
    ("TSM",  "NVDA", "칩 제조"),
    ("TSM",  "AMD",  "칩 제조"),
    ("ETN",  "SMCI", "전력 장비"),
    ("VRT",  "SMCI", "냉각"),
    ("NEE",  "SMCI", "전력 공급"),
    ("CEG",  "SMCI", "전력 공급"),
    ("ETR",  "SMCI", "전력 공급"),
    ("PWR",  "NEE",  "송전망 시공"),
    ("PWR",  "CEG",  "송전망 시공"),
    ("MOD",  "SMCI", "열관리"),
]

SECTOR_COLOR = {
    "semiconductor":   "#7B61FF",
    "power_equipment": "#FF9900",
    "power_utility":   "#00B4D8",
    "cooling":         "#06D6A0",
    "network":         "#EF476F",
    "cloud":           "#118AB2",
    "datacenter_reit": "#FFD166",
}

# ---------------------------------------------------------------------------
# 데이터 로딩
# ---------------------------------------------------------------------------

def load_companies() -> pd.DataFrame:
    return pd.read_csv(COMPANIES_CSV)


def load_returns() -> pd.DataFrame:
    from src.analysis.returns import build_returns_table
    return build_returns_table()


def load_bottleneck(df_returns: pd.DataFrame) -> pd.DataFrame:
    from src.analysis.bottleneck_score import calc_bottleneck_score
    return calc_bottleneck_score(df_returns)


# ---------------------------------------------------------------------------
# 그래프 빌드
# ---------------------------------------------------------------------------

def build_graph(df_companies: pd.DataFrame):
    if nx is None:
        return None
    G = nx.DiGraph()
    for _, row in df_companies.iterrows():
        G.add_node(
            row["ticker"],
            label=row["ticker"],
            sector=row["sector"],
            color=SECTOR_COLOR.get(row["sector"], "#AAAAAA"),
            size=20,
            ret_3m=None,
            title=f"{row['company']} ({row['sector']})",
        )
    for src, dst, rel in SUPPLY_EDGES:
        if src in G.nodes and dst in G.nodes:
            G.add_edge(src, dst, title=rel)
    return G


def apply_momentum(G, df_returns: pd.DataFrame):
    if df_returns is None or df_returns.empty or G is None:
        return G
    ret_map = df_returns.set_index("ticker")["ret_3m"].to_dict()
    for ticker in G.nodes:
        ret = ret_map.get(ticker)
        if ret is None:
            continue
        G.nodes[ticker]["ret_3m"] = ret
        G.nodes[ticker]["size"] = max(15, min(60, 20 + abs(ret) * 1.5))
        G.nodes[ticker]["title"] += f"\n3개월 수익률: {ret:+.1f}%"
        if ret > 10:
            G.nodes[ticker]["color"] = "#FF3333"
        elif ret > 5:
            G.nodes[ticker]["color"] = "#FF8C00"
        elif ret > 0:
            G.nodes[ticker]["color"] = "#FFD700"
        elif ret > -5:
            G.nodes[ticker]["color"] = "#A0C4FF"
        else:
            G.nodes[ticker]["color"] = "#3366FF"
    return G


def render_pyvis(G, output_path: Path = None) -> str:
    if Network is None:
        return None
    net = Network(height="700px", width="100%", directed=True, bgcolor="#1a1a2e")
    net.from_nx(G)
    net.set_options("""
    {
      "nodes": {"font": {"color": "white", "size": 14}},
      "edges": {"color": {"color": "#888888"}, "arrows": {"to": {"enabled": true}}},
      "physics": {"enabled": true, "stabilization": {"iterations": 100}}
    }
    """)
    if output_path is None:
        output_path = ROOT / "reports" / "infra_map.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    net.save_graph(str(output_path))
    return str(output_path)


# ---------------------------------------------------------------------------
# 색상 헬퍼
# ---------------------------------------------------------------------------

def ret_color(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "background-color: #2a2a2a"
    if val > 10:
        return "background-color: #7f1d1d; color: white"
    elif val > 5:
        return "background-color: #92400e; color: white"
    elif val > 0:
        return "background-color: #365314; color: white"
    elif val > -5:
        return "background-color: #1e3a5f; color: white"
    else:
        return "background-color: #1e1b4b; color: white"


# ---------------------------------------------------------------------------
# Streamlit 대시보드
# ---------------------------------------------------------------------------

def run_dashboard():
    if st is None:
        print("streamlit이 설치되지 않았습니다: pip install streamlit")
        return

    st.set_page_config(
        page_title="AI 인프라 섹터 트래커",
        page_icon="📡",
        layout="wide",
    )

    st.title("📡 AI 인프라 섹터 트래커")

    with st.spinner("데이터 로딩 중..."):
        try:
            df_returns = load_returns()
            df_bottleneck = load_bottleneck(df_returns)
            df_companies = load_companies()
            data_ok = True
        except Exception as e:
            st.error(f"데이터 로딩 실패: {e}")
            data_ok = False

    if not data_ok:
        st.stop()

    from datetime import datetime
    st.caption(f"마지막 업데이트: {datetime.today().strftime('%Y-%m-%d')}")

    # ── KPI 카드 ──────────────────────────────────────────
    ai_avg_3m = df_returns["ret_3m"].mean()
    top_row = df_bottleneck.iloc[0]
    bot_row = df_bottleneck.iloc[-1]
    strong_count = int((df_bottleneck["bottleneck_score"] > 10).sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AI 인프라 평균 3M", f"{ai_avg_3m:+.1f}%")
    c2.metric("최고 섹터 (3M)", top_row["sector"], f"{top_row['avg_ret_3m']:+.1f}%")
    c3.metric("최저 섹터 (3M)", bot_row["sector"], f"{bot_row['avg_ret_3m']:+.1f}%", delta_color="inverse")
    c4.metric("강한 병목 신호", f"{strong_count}개 섹터")

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 섹터 모멘텀",
        "🔥 병목 점수",
        "🏢 기업별 모멘텀",
        "🗺️ 인프라 맵",
    ])

    # ════════════════════════════════════════════════════
    # TAB 1 — 섹터 모멘텀
    # ════════════════════════════════════════════════════
    with tab1:
        st.subheader("섹터별 수익률 비교")

        df_sector_ret = (
            df_returns.groupby("sector")[["ret_1w", "ret_1m", "ret_3m", "ret_6m", "ret_ytd"]]
            .mean()
            .round(2)
            .reset_index()
            .sort_values("ret_3m", ascending=False)
        )

        if px:
            col_a, col_b = st.columns(2)
            with col_a:
                fig = px.bar(
                    df_sector_ret,
                    x="sector", y="ret_3m",
                    color="ret_3m",
                    color_continuous_scale=["#3366FF", "#FFFFFF", "#FF3333"],
                    color_continuous_midpoint=0,
                    title="섹터별 3개월 수익률",
                    labels={"ret_3m": "3M 수익률 (%)", "sector": "섹터"},
                    text="ret_3m",
                )
                fig.update_traces(texttemplate="%{text:+.1f}%", textposition="outside")
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)

            with col_b:
                df_melt = df_sector_ret.melt(
                    id_vars="sector",
                    value_vars=["ret_1w", "ret_1m", "ret_3m", "ret_6m"],
                    var_name="기간", value_name="수익률"
                )
                fig2 = px.line(
                    df_melt, x="기간", y="수익률", color="sector",
                    title="섹터별 기간별 수익률 추이", markers=True,
                )
                fig2.update_layout(height=400)
                st.plotly_chart(fig2, use_container_width=True)

        st.subheader("섹터 수익률 테이블")
        st.dataframe(
            df_sector_ret.style.map(
                ret_color, subset=["ret_1w", "ret_1m", "ret_3m", "ret_6m", "ret_ytd"]
            ),
            use_container_width=True,
            height=300,
        )

    # ════════════════════════════════════════════════════
    # TAB 2 — 병목 점수
    # ════════════════════════════════════════════════════
    with tab2:
        st.subheader("섹터별 병목 점수")
        st.caption("병목 점수 = 섹터 평균 3M 수익률 − 전체 AI인프라 평균 3M 수익률")

        if px:
            fig3 = px.bar(
                df_bottleneck.sort_values("bottleneck_score"),
                x="bottleneck_score", y="sector",
                orientation="h",
                color="bottleneck_score",
                color_continuous_scale=["#3366FF", "#FFFFFF", "#FF3333"],
                color_continuous_midpoint=0,
                title="병목 점수 (섹터별)",
                labels={"bottleneck_score": "병목 점수 (%p)", "sector": "섹터"},
                text="bottleneck_score",
            )
            fig3.update_traces(texttemplate="%{text:+.1f}", textposition="outside")
            fig3.update_layout(height=450, showlegend=False)
            st.plotly_chart(fig3, use_container_width=True)

        signal_emoji = {"강한 병목": "🔴", "중간 병목": "🟠", "중립": "⚪", "병목 약화": "🔵"}
        df_sig = df_bottleneck.copy()
        df_sig["신호"] = df_sig["signal"].map(lambda x: f"{signal_emoji.get(x, '')} {x}")
        st.subheader("신호 테이블")
        st.dataframe(
            df_sig[["sector", "avg_ret_3m", "bottleneck_score", "신호", "company_count"]],
            use_container_width=True,
        )

    # ════════════════════════════════════════════════════
    # TAB 3 — 기업별 모멘텀
    # ════════════════════════════════════════════════════
    with tab3:
        st.subheader("기업별 수익률")

        sectors = ["전체"] + sorted(df_returns["sector"].unique().tolist())
        selected = st.selectbox("섹터 필터", sectors)
        df_filt = df_returns if selected == "전체" else df_returns[df_returns["sector"] == selected]
        df_filt = df_filt.sort_values("ret_3m", ascending=False)

        st.dataframe(
            df_filt[["ticker", "company", "sector", "ret_1w", "ret_1m", "ret_3m", "ret_6m", "ret_ytd"]]
            .style.map(ret_color, subset=["ret_1w", "ret_1m", "ret_3m", "ret_6m", "ret_ytd"]),
            use_container_width=True,
            height=450,
        )

        if px and selected != "전체":
            fig4 = px.bar(
                df_filt.sort_values("ret_3m"),
                x="ret_3m", y="ticker", orientation="h",
                color="ret_3m",
                color_continuous_scale=["#3366FF", "#FFFFFF", "#FF3333"],
                color_continuous_midpoint=0,
                title=f"{selected} — 기업별 3M 수익률",
                text="ret_3m",
            )
            fig4.update_traces(texttemplate="%{text:+.1f}%", textposition="outside")
            fig4.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig4, use_container_width=True)

    # ════════════════════════════════════════════════════
    # TAB 4 — 인프라 맵
    # ════════════════════════════════════════════════════
    with tab4:
        st.subheader("AI 인프라 공급망 맵")
        st.caption("노드 크기 = 3M 모멘텀 강도 | 빨강 = 강한 상승 | 파랑 = 약세 | 화살표 = 공급 방향")

        if nx is None or Network is None:
            st.warning("pip install networkx pyvis 를 실행하세요.")
            st.dataframe(df_companies[["ticker", "company", "sector"]], use_container_width=True)
        else:
            G = build_graph(df_companies)
            G = apply_momentum(G, df_returns)
            html_path = render_pyvis(G)
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            st.components.v1.html(html_content, height=750, scrolling=False)

            st.subheader("섹터 범례")
            cols = st.columns(len(SECTOR_COLOR))
            for i, (sector, color) in enumerate(SECTOR_COLOR.items()):
                cols[i].markdown(
                    f"<div style='background:{color};padding:6px 10px;border-radius:6px;"
                    f"text-align:center;font-size:12px;color:white'>{sector}</div>",
                    unsafe_allow_html=True,
                )


run_dashboard()
