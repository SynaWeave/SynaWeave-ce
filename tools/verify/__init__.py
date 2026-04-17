"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  expose the governed repository verification helpers from one package boundary

- Later Extension Points:
    --> add package exports only when new verifier lanes join the default repo stack

- Role:
    --> re-exports the active repository verification checks
    --> keeps verifier package imports stable for callers and tests

- Exports:
    --> `check_shape()` and related verifier helpers

- Consumed By:
    --> repository verification scripts and unit tests importing `tools.verify`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from .adr import check_adrs
from .commentary import check_commentary
from .commit import check_commit_head
from .docs import check_docs
from .governance import check_governance
from .headers import check_headers
from .html_ship import check_html_ship
from .pr_quality import validate_pr_body, validate_pr_title
from .security import check_security
from .shape import check_shape
from .suppressions import check_suppressions
from .tldr import summarize_issues
from .workflows import check_workflows

__all__ = [
    "check_shape",
    "check_docs",
    "check_commentary",
    "check_governance",
    "check_headers",
    "check_html_ship",
    "check_adrs",
    "check_workflows",
    "check_commit_head",
    "validate_pr_title",
    "validate_pr_body",
    "check_security",
    "check_suppressions",
    "summarize_issues",
]
