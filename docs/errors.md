# Exceptions and errors

`APIError` reports the backend message, code, HTTP status, endpoint path, and response details. Successful API envelopes are returned as `ApiResponse`; access the original value using `.data`, and inspect `.code`, `.message`, or `.raw` as needed.

Only GET/HEAD calls may be retried once after a network/timeout failure. POST calls, including order submission, are never automatically retried because the server mapping contains no idempotency-key contract. Authentication credentials and tokens are excluded from request logging; logging records method and URL only.

Input validation raises `ValueError` before a request for invalid SDK arguments. `NotImplementedError` identifies operations for which no backend endpoint contract was confirmed; it does not indicate a simulated operation.
