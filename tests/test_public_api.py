import pandas as pd
import pytest

from dfaudit import profile


def test_profile_is_not_implemented_yet() -> None:
    df = pd.DataFrame({"a": [1, None, 3]})

    with pytest.raises(NotImplementedError):
        profile(df)
