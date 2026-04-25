"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  expose the API package marker for the first request-serving runtime entrypoint

- Later Extension Points:
    --> add package-level exports only when the API runtime grows durable reusable bootstrap helpers

- Role:
    --> keeps the API runtime importable as a Python package
    --> supports module-based startup paths for local development and tests

- Exports:
    --> package marker only

- Consumed By:
    --> `apps.api.main` module startup and tests importing the API app object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """
