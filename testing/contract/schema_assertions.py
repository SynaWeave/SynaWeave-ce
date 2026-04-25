"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  validate bounded JSON-like contract fixtures with a tiny schema subset
            for Sprint 1 interfaces

- Later Extension Points:
    --> widen schema keywords only when contract fixtures genuinely need more JSON-schema features

- Role:
    --> keeps contract tests schema-driven without adding a new runtime
        dependency just for validation
    --> centralizes strict type and shape assertions for public serialized interfaces

- Exports:
    --> `assert_matches_schema`

- Consumed By:
    --> contract tests validating Sprint 1 runtime request response and message payloads
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import re
from typing import Any


def _matches_type(value: Any, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "null":
        return value is None
    raise AssertionError(f"unsupported schema type: {expected_type}")


def assert_matches_schema(instance: Any, schema: dict[str, Any], path: str = "$") -> None:
    expected_types = schema.get("type")
    if isinstance(expected_types, str):
        expected_types = [expected_types]
    if expected_types:
        if not any(_matches_type(instance, expected_type) for expected_type in expected_types):
            raise AssertionError(
                f"{path} expected type {expected_types} but got {type(instance).__name__}"
            )

    if "const" in schema and instance != schema["const"]:
        raise AssertionError(
            f"{path} expected constant {schema['const']!r} but got {instance!r}"
        )

    if "enum" in schema and instance not in schema["enum"]:
        raise AssertionError(
            f"{path} expected one of {schema['enum']!r} but got {instance!r}"
        )

    if instance is None:
        return

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                raise AssertionError(f"{path}.{key} is required")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra_keys = sorted(set(instance) - set(properties))
            if extra_keys:
                raise AssertionError(f"{path} has unexpected properties {extra_keys!r}")

        for key, value in instance.items():
            child_schema = properties.get(key)
            if child_schema is not None:
                assert_matches_schema(value, child_schema, f"{path}.{key}")
        return

    if isinstance(instance, list):
        min_items = schema.get("minItems")
        if min_items is not None and len(instance) < min_items:
            raise AssertionError(
                f"{path} expected at least {min_items} items but got {len(instance)}"
            )
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, item in enumerate(instance):
                assert_matches_schema(item, item_schema, f"{path}[{index}]")
        return

    if isinstance(instance, str):
        min_length = schema.get("minLength")
        if min_length is not None and len(instance) < min_length:
            raise AssertionError(f"{path} expected minLength {min_length} but got {len(instance)}")
        pattern = schema.get("pattern")
        if pattern is not None and re.search(pattern, instance) is None:
            raise AssertionError(f"{path} did not match pattern {pattern!r}: {instance!r}")
        return

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        minimum = schema.get("minimum")
        if minimum is not None and instance < minimum:
            raise AssertionError(f"{path} expected minimum {minimum} but got {instance}")
