# Exceptions and errors

`APIError` reports the backend message, code, HTTP status, and endpoint path. Raw error details are available as `.details` but are hidden from `repr`. Successful API envelopes are returned as `ApiResponse`; access the original value using `.data`, and inspect `.code`, `.message`, or `.raw` as needed. Raw successful payloads are hidden from `repr` as well.

Only GET/HEAD calls may be retried once after a network/timeout failure. POST calls, including order submission, are never automatically retried because the server mapping contains no idempotency-key contract. If an order request times out, returns an invalid body, or the server returns a 5xx response, `UnknownOutcomeError` indicates that the server may have processed the request. Reconcile through order history before retrying. Authentication credentials and tokens are excluded from request logging; logging records method and endpoint path only.

Input validation raises `ValueError` before a request for invalid SDK arguments. `NotImplementedError` identifies operations for which no backend endpoint contract was confirmed; it does not indicate a simulated operation.
