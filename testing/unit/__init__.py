"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  mark the governed unit test tree as an importable Python package for local verification

- Later Extension Points:
    --> add shared unit-test exports only if multiple tests begin depending on common helpers here

- Role:
    --> keeps the unit-test package importable for discovery and relative imports
    --> exists as a bounded package marker rather than a hidden helper module

- Exports:
    --> package marker only

- Consumed By:
    --> Python unit discovery and repository verification imports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """
