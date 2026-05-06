import pandas as pd

from dfaudit import overview


def test_overview_sorts_by_missing_then_uniques() -> None:
    df = pd.DataFrame(
        {
            "low_miss": [1, 2, 3],
            "high_miss": [1.0, None, None],
            "all_miss": [None, None, None],
        }
    )
    html = overview(df).to_html()
    assert html.index("all_miss") < html.index("high_miss") < html.index("low_miss")


def test_overview_columns() -> None:
    df = pd.DataFrame({"a": [1, None, 3], "b": ["x", "y", "z"]})
    result = overview(df)
    expected = ["column", "dtype", "missing", "missing_pct", "soft_missing", "soft_missing_pct", "unique", "unique_pct", "mode", "mode_pct", "top3_pct"]
    assert list(result.data.columns) == expected


def test_overview_top3_pct_is_dict() -> None:
    df = pd.DataFrame({"a": ["x", "x", "y", "z"]})
    data = overview(df).data
    top3 = data.loc[data["column"] == "a", "top3_pct"].iloc[0]
    assert isinstance(top3, dict)
    assert "x" in top3
    assert top3["x"] == "50.0%"


def test_overview_renders_vivid_style() -> None:
    df = pd.DataFrame({"a": [1, None, 3]})
    html = overview(df, style="vivid").to_html()
    assert "#0d1321" in html
