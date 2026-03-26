"""
AI 인프라 동적 맵 시각화

AI 인프라 기업들의 공급망 연결 관계를 네트워크 그래프로 시각화한다.
노드 크기와 색깔은 yfinance 주가 모멘텀 데이터로 자동 업데이트된다.

실행:
    streamlit run src/visualization/infra_map.py
"""

from pathlib import Path
import pandas as pd

# 선택적 임포트 — 설치 안 된 경우 안내 메시지 출력
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

DATA_DIR = Path(__file__).parent.parent.parent / "data"
COMPANIES_CSV = DATA_DIR / "reference" / "companies.csv"


# ---------------------------------------------------------------------------
# 1. 그래프 구조 정의 — 기업 간 공급망 연결 관계
# ---------------------------------------------------------------------------

# 엣지: (공급자 ticker, 수요자 ticker, 관계 설명)
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

# 섹터별 색상 (기본 색 — 모멘텀 적용 전)
SECTOR_COLOR = {
    "semiconductor":   "#7B61FF",
    "power_equipment": "#FF9900",
    "power_utility":   "#00B4D8",
    "cooling":         "#06D6A0",
    "network":         "#EF476F",
    "cloud":           "#118AB2",
    "datacenter_reit": "#FFD166",
}


def load_companies() -> pd.DataFrame:
    """companies.csv에서 기업 마스터 데이터를 불러온다."""
    return pd.read_csv(COMPANIES_CSV)


def build_graph(df_companies: pd.DataFrame) -> "nx.DiGraph":
    """
    공급망 방향성을 가진 NetworkX 그래프를 생성한다.

    노드 속성:
        label    : 티커
        sector   : 섹터 분류
        color    : 섹터 기본 색상
        size     : 기본값 20 (모멘텀 적용 후 조정)
        ret_3m   : 3개월 수익률 (apply_momentum 호출 후 채워짐)

    엣지 속성:
        title    : 관계 설명 (hover 시 표시)
    """
    if nx is None:
        raise ImportError("networkx가 설치되지 않았습니다. pip install networkx")

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


def apply_momentum(G: "nx.DiGraph", df_returns: pd.DataFrame) -> "nx.DiGraph":
    """
    수익률 데이터를 그래프 노드에 적용한다.

    노드 크기  = 3개월 수익률 절댓값 (최소 15, 최대 60)
    노드 색깔  = 빨강(높은 수익률) ~ 흰색(0) ~ 파랑(낮은 수익률)

    Args:
        G          : build_graph()로 생성한 DiGraph
        df_returns : 컬럼에 ticker, ret_3m이 포함된 DataFrame
    """
    if df_returns is None or df_returns.empty:
        return G

    ret_map = df_returns.set_index("ticker")["ret_3m"].to_dict()

    for ticker in G.nodes:
        ret = ret_map.get(ticker)
        if ret is None:
            continue

        G.nodes[ticker]["ret_3m"] = ret
        G.nodes[ticker]["size"] = max(15, min(60, 20 + abs(ret) * 1.5))
        G.nodes[ticker]["title"] += f"\n3개월 수익률: {ret:+.1f}%"

        # 색깔: 양수 → 빨강 계열, 음수 → 파랑 계열
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


def render_pyvis(G: "nx.DiGraph", output_path: Path = None) -> str:
    """
    NetworkX 그래프를 PyVis 인터랙티브 HTML로 변환한다.

    Returns:
        HTML 파일 경로 문자열
    """
    if Network is None:
        raise ImportError("pyvis가 설치되지 않았습니다. pip install pyvis")

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
        output_path = Path(__file__).parent.parent.parent / "reports" / "infra_map.html"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    net.save_graph(str(output_path))
    return str(output_path)


# ---------------------------------------------------------------------------
# 2. Streamlit 대시보드 진입점
# ---------------------------------------------------------------------------

def run_dashboard():
    """
    streamlit run src/visualization/infra_map.py 로 실행한다.
    """
    if st is None:
        print("streamlit이 설치되지 않았습니다. pip install streamlit")
        return

    st.set_page_config(page_title="AI 인프라 섹터 트래커", layout="wide")
    st.title("AI 인프라 공급망 맵")
    st.caption("노드 크기 = 3개월 모멘텀 강도 | 빨강 = 강한 상승 | 파랑 = 약세")

    # TODO: 실제 수익률 데이터 연결 (Phase 1-2 완료 후)
    # df_returns = pd.read_csv(DATA_DIR / "processed" / "returns" / "latest.csv")

    df_companies = load_companies()

    if nx is None or Network is None:
        st.warning("networkx 또는 pyvis가 설치되지 않았습니다.\n"
                   "터미널에서 실행: pip install networkx pyvis")
        st.dataframe(df_companies[["ticker", "company", "sector", "sub_sector"]])
        return

    G = build_graph(df_companies)
    # G = apply_momentum(G, df_returns)  # 수익률 데이터 연결 후 주석 해제

    html_path = render_pyvis(G)

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    st.components.v1.html(html_content, height=750, scrolling=False)

    st.subheader("기업 목록")
    st.dataframe(
        df_companies[["ticker", "company", "sector", "sub_sector", "bottleneck_relevance"]],
        use_container_width=True,
    )


if __name__ == "__main__":
    run_dashboard()
