"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  expose the ingest package marker for the first background execution entrypoint

- Later Extension Points:
    --> add package-level exports only when multiple ingest commands become durable shared helpers

- Role:
    --> keeps the ingest runtime importable as a Python package
    --> supports module-based execution for local background job proof and tests

- Exports:
    --> package marker only

- Consumed By:
    --> `apps.ingest.main` module execution and tests importing the ingest command surface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """
