import pandas as pd

from dfaudit import compute_overview, profile, style_overview


def test_profile_returns_audit_report_with_overview() -> None:
    df = pd.DataFrame({"a": [1, None, 3], "b": ["x", "y", "z"]})
    rep = profile(df)

    assert rep.dataframe is df
    assert list(rep.overview.columns) == [
        "column",
        "dtype",
        "missing",
        "missing_pct",
        "unique_values",
        "sample_value",
    ]
    assert rep.overview.loc[rep.overview["column"] == "a", "missing"].iloc[0] == 1


def test_compute_overview_sorts_by_missing_then_uniques() -> None:
    df = pd.DataFrame(
        {
            "low_miss": [1, 2, 3],
            "high_miss": [1.0, None, None],
            "all_miss": [None, None, None],
        }
    )
    out = compute_overview(df)
    assert list(out["column"]) == ["all_miss", "high_miss", "low_miss"]


def test_style_overview_renders_without_error() -> None:
    df = pd.DataFrame({"a": [1, None, 3]})
    html = style_overview(df).to_html()
    assert "Data overview" in html
    assert "missing_pct" in html
