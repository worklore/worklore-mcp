| check | result | evidence |
| tool list open | PASS | initialize + tools/list 200 without a token |
| resources | FAIL | initialize advertises capabilities.resources, resources/list answers 401 without a token |
| refusal | FAIL | get_note with id n-99 returns JSON-RPC error -32602 "note not found" instead of a result with isError: true |
| session after error | PASS | a valid get_note right after works |
| outputSchema honoured | PASS | get_note structuredContent validates |
| outputSchema can reject | FAIL | search_notes outputSchema is {"type": "object"}: it accepts anything |
| names | PASS | all match the pattern |
| version negotiation | PASS | "banana" gets 2025-06-18 |
| logging | PASS | one JSON line per call on stderr |
