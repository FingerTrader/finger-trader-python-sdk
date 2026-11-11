# Exceptions and errors

`APIError` reports the backend message, code, HTTP status, and endpoint path. Raw error details are available as `.details` but are hidden from `repr`. Successful API envelopes are returned as `ApiResponse`; access the original value using `.data`, and inspect `.code`, `.message`, or `.raw` as needed. Raw successful payloads are hidden from `repr` as well.

Only GET/HEAD calls may be retried once after a network/timeout failure. POST calls, including order submission, are never automatically retried because the server mapping contains no idempotency-key contract. If an order request times out, returns an invalid body, or the server returns a 5xx response, `UnknownOutcomeError` indicates that the server may have processed the request. Reconcile through order history before retrying. Authentication credentials and tokens are excluded from request logging; logging records method and endpoint path only.

Input validation raises `ValueError` before a request for invalid SDK arguments. `NotImplementedError` identifies operations for which no backend endpoint contract was confirmed; it does not indicate a simulated operation.

## Hosted errors

Hosted services raise `finger_trader.hosted.HostedError` subclasses with a stable `code`, explanatory `message`, and optional `rpc_code`. Use the code or exception class for control flow, rather than matching message text. Examples include `InvalidArgumentError`, `PermissionDeniedError`, `StaleCallbackError`, `UnsupportedCapabilityError`, and `HostedIOError`.

Local checks reject an unbound/stale Context, calls from another thread, invalid stage access, float financial values, and non-UTC timestamps. The Host independently validates requests. Host deadlines and disconnects can fail a run; they do not prove that an accepted operation was undone. There is no implicit HTTP fallback or automatic trading retry. See [all error mappings](quant/python-managed-api-v1.md) and [Hosted strategies](hosted-strategies.md).
