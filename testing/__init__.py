"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  mark the governed testing tree as an importable Python package for local verification

- Later Extension Points:
    --> add package-level exports only if shared test helpers move into this package root later

- Role:
    --> keeps the top-level testing package importable for unit discovery and support modules
    --> exists as a bounded package marker rather than a hidden test helper module

- Exports:
    --> package marker only

- Consumed By:
    --> Python test discovery and repository verification imports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """
