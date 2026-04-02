"""
=============================================================================
STEP 3 — 리포트 & 시각화 레이어 (src/reports/, src/visualization/)
=============================================================================

실행 순서 (weekly, STEP 2 완료 후):
  ① weekly_report.py  → 분석 결과 → Jinja2 템플릿 → Markdown 리포트 저장
  ② infra_map.py      → NetworkX 그래프 생성 → PyVis HTML → Streamlit 대시보드

이 파일의 모든 테스트는 현재 RED(실패) 상태입니다.
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src" / "analysis"))


# =============================================================================
# ① weekly_report.py
#
# 역할: 분석 결과를 Jinja2 템플릿에 주입해서 Markdown 파일 저장
#   · df_to_md_table(df)  → DataFrame → Markdown 테이블 문자열
#   · generate_report()   → 분석 함수 호출 → 템플릿 렌더링 → .md 파일 저장
# =============================================================================

class TestWeeklyReport:

    def test_df_to_md_table_has_header_row(self):
        """
        [df_to_md_table]
        Markdown 테이블 첫 줄이 컬럼명 헤더(| col1 | col2 |)여야 한다.
        두 번째 줄이 구분선(| --- | --- |)이어야 한다.
        """
        from src.reports.weekly_report import df_to_md_table
        df = pd.DataFrame([{"sector": "semiconductor", "ret_3m": 40.0}])
        result = df_to_md_table(df)

        lines = result.strip().split("\n")
        assert lines[0].startswith("|"), "첫 줄이 | 로 시작해야 한다 (헤더)"
        assert "sector" in lines[0], "헤더에 컬럼명이 있어야 한다"
        assert "---" in lines[1], "두 번째 줄이 구분선이어야 한다"

    def test_df_to_md_table_empty_returns_placeholder(self):
        """
        [df_to_md_table]
        빈 DataFrame을 넘기면 "_없음_" 문자열을 반환해야 한다.
        (빈 테이블이 아니라 명시적 메시지)
        """
        from src.reports.weekly_report import df_to_md_table
        result = df_to_md_table(pd.DataFrame())
        assert result == "_없음_", "빈 DataFrame → '_없음_' 반환"

    def test_df_to_md_table_data_row_count(self):
        """
        [df_to_md_table]
        3행 DataFrame → 헤더 + 구분선 + 3행 = 총 5줄이어야 한다.
        """
        from src.reports.weekly_report import df_to_md_table
        df = pd.DataFrame([
            {"a": 1, "b": 2},
            {"a": 3, "b": 4},
            {"a": 5, "b": 6},
        ])
        result = df_to_md_table(df)
        lines = [l for l in result.strip().split("\n") if l.strip()]
        assert len(lines) == 5, f"5줄이어야 한다. 현재: {len(lines)}줄"

    def test_generate_report_creates_md_file(self, tmp_path, monkeypatch):
        """
        [generate_report]
        호출 후 reports/weekly/ 에 {YYYY-WXX}_weekly.md 파일이 생성되어야 한다.
        반환값이 Path 객체여야 한다.
        """
        from src.reports import weekly_report as wr
        monkeypatch.setattr(wr, "REPORTS_DIR", tmp_path)

        # 의존 함수들 모두 mock
        fake_returns = pd.DataFrame([
            {"ticker": "NVDA", "company": "NVIDIA", "sector": "semiconductor",
             "ret_1w": 5.0, "ret_1m": 15.0, "ret_3m": 40.0, "ret_6m": 60.0, "ret_1y": 80.0, "ret_ytd": 30.0},
        ])
        fake_sector = pd.DataFrame([
            {"sector": "semiconductor", "ret_1w": 5.0, "ret_1m": 15.0, "ret_3m": 40.0},
        ])
        fake_bottleneck = pd.DataFrame([
            {"sector": "semiconductor", "avg_ret_3m": 40.0, "bottleneck_score": 15.0,
             "signal": "강한 병목", "company_count": 1},
        ])
        fake_signal = pd.DataFrame([
            {"ticker": "NVDA", "company": "NVIDIA", "sector": "semiconductor",
             "ret_1m": 15.0, "ret_3m": 40.0, "total_score": 8.5, "signal": "BUY 관심"},
        ])

        with patch("src.reports.weekly_report.load_latest_returns", return_value=fake_returns), \
             patch("src.reports.weekly_report.sector_summary", return_value=fake_sector), \
             patch("src.reports.weekly_report.calc_bottleneck_score", return_value=fake_bottleneck), \
             patch("src.reports.weekly_report.build_investment_signal", return_value=fake_signal), \
             patch("src.reports.weekly_report.top_performers", return_value=fake_returns[["ticker","company","sector","ret_1m"]]), \
             patch("src.reports.weekly_report.bottom_performers", return_value=fake_returns[["ticker","company","sector","ret_1m"]]):
            result = wr.generate_report()

        assert isinstance(result, Path), "generate_report()은 Path를 반환해야 한다"
        assert result.suffix == ".md", ".md 파일이어야 한다"
        assert result.exists(), "파일이 실제로 생성되어야 한다"

    def test_generate_report_filename_format(self, tmp_path, monkeypatch):
        """
        [generate_report]
        생성된 파일명이 YYYY-WXX_weekly.md 형식이어야 한다.
        예: 2026-W14_weekly.md
        """
        from src.reports import weekly_report as wr
        monkeypatch.setattr(wr, "REPORTS_DIR", tmp_path)

        fake_returns = pd.DataFrame([
            {"ticker": "NVDA", "company": "NVIDIA", "sector": "semiconductor",
             "ret_1w": 5.0, "ret_1m": 15.0, "ret_3m": 40.0, "ret_6m": 60.0, "ret_1y": 80.0, "ret_ytd": 30.0},
        ])
        fake_sector = pd.DataFrame([{"sector": "semiconductor", "ret_1w": 5.0, "ret_1m": 15.0, "ret_3m": 40.0}])
        fake_bottleneck = pd.DataFrame([{"sector": "semiconductor", "avg_ret_3m": 40.0, "bottleneck_score": 15.0, "signal": "강한 병목", "company_count": 1}])
        fake_signal = pd.DataFrame([{"ticker": "NVDA", "company": "NVIDIA", "sector": "semiconductor", "ret_1m": 15.0, "ret_3m": 40.0, "total_score": 8.5, "signal": "BUY 관심"}])

        with patch("src.reports.weekly_report.load_latest_returns", return_value=fake_returns), \
             patch("src.reports.weekly_report.sector_summary", return_value=fake_sector), \
             patch("src.reports.weekly_report.calc_bottleneck_score", return_value=fake_bottleneck), \
             patch("src.reports.weekly_report.build_investment_signal", return_value=fake_signal), \
             patch("src.reports.weekly_report.top_performers", return_value=fake_returns[["ticker","company","sector","ret_1m"]]), \
             patch("src.reports.weekly_report.bottom_performers", return_value=fake_returns[["ticker","company","sector","ret_1m"]]):
            result = wr.generate_report()

        # 파일명 패턴: 숫자4자리-W숫자2자리_weekly.md
        import re
        assert re.match(r"\d{4}-W\d{2}_weekly\.md", result.name), \
            f"파일명 형식이 맞지 않음: {result.name}"


# =============================================================================
# ② infra_map.py (visualization)
#
# 역할: AI 인프라 공급망을 NetworkX 그래프로 시각화
#   · load_companies()      → companies.csv 로드 → DataFrame
#   · build_graph(df)       → 기업 노드 + SUPPLY_EDGES → NetworkX DiGraph
#   · apply_momentum(G, df) → 수익률 데이터 → 노드 크기/색깔 업데이트
#   · render_pyvis(G)       → PyVis HTML 파일 생성 → 파일 경로 반환
#   · run_dashboard()       → Streamlit 앱 실행 진입점
#
# SUPPLY_EDGES: 12개 공급망 관계 (반도체 장비 → 파운드리 → AI칩 → 데이터센터)
# SECTOR_COLOR: 섹터별 기본 색상 dict
# =============================================================================

class TestInfraMap:

    def test_load_companies_returns_dataframe(self):
        """
        [load_companies]
        반환값이 DataFrame이어야 한다.
        ticker, company, sector 컬럼이 있어야 한다.
        """
        from src.visualization.infra_map import load_companies
        df = load_companies()

        assert isinstance(df, pd.DataFrame), "DataFrame을 반환해야 한다"
        for col in ["ticker", "company", "sector"]:
            assert col in df.columns, f"{col} 컬럼이 있어야 한다"

    def test_build_graph_node_count(self):
        """
        [build_graph]
        companies.csv의 기업 수만큼 노드가 있어야 한다.
        """
        from src.visualization.infra_map import load_companies, build_graph
        df = load_companies()

        try:
            G = build_graph(df)
            assert len(G.nodes) == len(df), \
                f"노드 수({len(G.nodes)})가 기업 수({len(df)})와 일치해야 한다"
        except ImportError:
            pytest.skip("networkx가 설치되지 않음")

    def test_build_graph_has_edges(self):
        """
        [build_graph]
        SUPPLY_EDGES가 적용되어 엣지가 1개 이상이어야 한다.
        """
        from src.visualization.infra_map import load_companies, build_graph
        df = load_companies()

        try:
            G = build_graph(df)
            assert len(G.edges) > 0, "엣지가 1개 이상이어야 한다"
        except ImportError:
            pytest.skip("networkx가 설치되지 않음")

    def test_build_graph_node_has_required_attributes(self):
        """
        [build_graph]
        각 노드에 label, sector, color, size, title 속성이 있어야 한다.
        """
        from src.visualization.infra_map import load_companies, build_graph
        df = load_companies()

        try:
            G = build_graph(df)
            first_node = list(G.nodes(data=True))[0]
            attrs = first_node[1]
            for attr in ["label", "sector", "color", "size", "title"]:
                assert attr in attrs, f"노드에 {attr} 속성이 있어야 한다"
        except ImportError:
            pytest.skip("networkx가 설치되지 않음")

    def test_apply_momentum_updates_node_size(self):
        """
        [apply_momentum]
        수익률이 높은 노드는 기본값(20)보다 큰 사이즈여야 한다.
        노드 ret_3m 속성이 수익률 값으로 업데이트되어야 한다.
        """
        from src.visualization.infra_map import load_companies, build_graph, apply_momentum
        df = load_companies()

        try:
            G = build_graph(df)
            df_returns = pd.DataFrame([
                {"ticker": "NVDA", "ret_3m": 50.0},
            ])
            G_updated = apply_momentum(G, df_returns)

            nvda_data = G_updated.nodes.get("NVDA")
            if nvda_data:
                assert nvda_data["ret_3m"] == 50.0, "ret_3m 속성이 업데이트되어야 한다"
                assert nvda_data["size"] > 20, "높은 수익률이면 기본값(20)보다 커야 한다"
        except ImportError:
            pytest.skip("networkx가 설치되지 않음")

    def test_apply_momentum_color_positive(self):
        """
        [apply_momentum]
        ret_3m > 10 인 노드는 색깔이 빨강 계열(#FF3333)이어야 한다.
        """
        from src.visualization.infra_map import load_companies, build_graph, apply_momentum
        df = load_companies()

        try:
            G = build_graph(df)
            df_returns = pd.DataFrame([{"ticker": "NVDA", "ret_3m": 50.0}])
            G_updated = apply_momentum(G, df_returns)

            nvda_data = G_updated.nodes.get("NVDA")
            if nvda_data:
                assert nvda_data["color"] == "#FF3333", \
                    f"ret_3m > 10 → 빨강(#FF3333)이어야 한다. 현재: {nvda_data['color']}"
        except ImportError:
            pytest.skip("networkx가 설치되지 않음")

    def test_render_pyvis_creates_html_file(self, tmp_path):
        """
        [render_pyvis]
        호출 후 .html 파일이 생성되어야 한다.
        반환값이 파일 경로 문자열이어야 한다.
        """
        from src.visualization.infra_map import load_companies, build_graph, render_pyvis

        try:
            df = load_companies()
            G = build_graph(df)
            output = render_pyvis(G, output_path=tmp_path / "test_map.html")

            assert isinstance(output, str), "파일 경로 문자열을 반환해야 한다"
            assert Path(output).exists(), ".html 파일이 생성되어야 한다"
            assert Path(output).suffix == ".html", ".html 확장자여야 한다"
        except ImportError:
            pytest.skip("networkx 또는 pyvis가 설치되지 않음")
