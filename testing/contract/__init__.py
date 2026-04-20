"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  mark the governed contract test tree as an importable Python package for schema checks

- Later Extension Points:
    --> add shared contract-test exports only if multiple contract suites begin
        depending on package-level helpers

- Role:
    --> keeps contract tests importable for discovery and helper reuse
    --> exists as a bounded package marker rather than a hidden helper module

- Exports:
    --> package marker only

- Consumed By:
    --> Python contract discovery and shared contract helper imports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """
