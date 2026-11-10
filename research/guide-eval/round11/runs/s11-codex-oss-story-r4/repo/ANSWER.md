The bug occurred because `similarity` returned a Python ``float``. DynamoDB does not accept floats, only ``Decimal`` or integer types. The first publish succeeded because the `similar` list was empty (no existing stories), so no float was written. On the second publish a non‑empty `similar` list caused a float to be stored, triggering ``TypeError: Float types are not supported``.

**Fix**
- Updated `similarity` to return an integer percentage (0‑100) instead of a float.
- Added a detailed docstring explaining the DynamoDB limitation and conversion.
- This preserves ordering while using a DynamoDB‑compatible type.

**Colleague note applied**
- Recognized the state‑dependent failure path.
- Converted the float to an int/Decimal at the DynamoDB boundary as recommended.
- No new tests were added; existing tests pass and the runtime error is resolved.

