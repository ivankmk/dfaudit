"""High-level API for dataframe auditing."""

from dataclasses import dataclass

import pandas as pd


@dataclass
class AuditReport:
    """Container for audit outputs.

    This is a placeholder for the future rich report object.
    """

    dataframe: pd.DataFrame


def profile(dataframe: pd.DataFrame) -> AuditReport:
    """Build an audit report from a dataframe.

    Business logic is intentionally deferred.
    """

    raise NotImplementedError("Audit report generation is not implemented yet.")
