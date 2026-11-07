# Security

- Production HTTP and WebSocket ticket endpoints require HTTPS/WSS. HTTP is accepted only for loopback development URLs. TLS verification uses the Python default trust store.
- HTTP redirects are rejected; the transport does not forward credentials to a redirect target. WebSocket ticket redirects are also disabled. The backend protocol requires the short-lived ticket in the WebSocket query string; this is the only SDK credential sent in a URL.
- HTTP request logging records method and endpoint path only, omitting query values, headers, and bodies. API errors redact configured tokens and omit raw details from `repr`.
- Access tokens are held in memory and are not written to disk. There is no token refresh endpoint in the inspected desktop contract.
- GET calls may be retried once after network failure. State-changing POST requests are never retried. A potentially ambiguous order request raises `UnknownOutcomeError`; query order history and reconcile before considering another submission.
- Order checks catch basic invalid values but do not replace instrument-specific server validation, account permission checks, or risk controls.

## Public source history note

The previous SDK revision copied a static Basic OAuth client value from Finger_desk configuration into the public Python package. This was removed from the current source and replaced with explicit operator configuration. Because the value existed in publicly reachable Git history and the same value appears in desktop app configuration, the service owner should confirm that it is a public client identifier and rotate/disable it if it grants confidential client privileges. Removing it from the current tree does not erase historical commits; this change does not rewrite history or force-push.
