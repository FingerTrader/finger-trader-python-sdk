# Security

- Production HTTP and WebSocket ticket endpoints require HTTPS/WSS. HTTP is accepted only for loopback development URLs. TLS verification uses the Python default trust store.
- HTTP redirects are rejected; the transport does not forward credentials to a redirect target. WebSocket ticket redirects are also disabled. The backend protocol requires the short-lived ticket in the WebSocket query string; this is the only SDK credential sent in a URL.
- HTTP request logging records method and endpoint path only, omitting query values, headers, and bodies. API errors redact configured tokens and omit raw details from `repr`.
- Access tokens are held in memory and are not written to disk. There is no token refresh endpoint in the inspected desktop contract.
- GET calls may be retried once after network failure. State-changing POST requests are never retried. A potentially ambiguous order request raises `UnknownOutcomeError`; query order history and reconcile before considering another submission.
- Order checks catch basic invalid values but do not replace instrument-specific server validation, account permission checks, or risk controls.

## Public source history note

The previous SDK revision copied a static Basic OAuth client value from Finger_desk configuration into the public Python package. This was removed from the current source and replaced with explicit operator configuration. Because the value existed in publicly reachable Git history and the same value appears in desktop app configuration, the service owner should confirm that it is a public client identifier and rotate/disable it if it grants confidential client privileges. Removing it from the current tree does not erase historical commits; this change does not rewrite history or force-push.

## OAuth Basic classification still needs server confirmation

Finger_desk declares environment-specific `basicAuthToken` constants for
Local, Dev, and Prod, and attaches the value as `Authorization: Basic ...` to
`POST /oauth2/token`. This proves that the value is a static OAuth client
credential embedded in a distributed desktop app. Client source alone cannot
prove whether the authorization server treats it as a public client identifier
or a confidential client secret. The service owner must inspect the OAuth
client registration, secret-required setting, allowed grants/scopes, and
issuance logs. If it is confidential, revoke or rotate it and assess exposure
history. Do not paste the historical value into an integration environment
until the owner confirms that it is approved for the non-production client.

## Hosted strategy trust and permissions

Only execute trusted local strategy code. The worker imports and instantiates that code in a subprocess; it is not a Python security sandbox. A strategy can use the operating-system permissions of its worker. Process-group cleanup covers ordinary child processes; intentionally escaping that group is outside the resource contract.

A usable Context exists only inside an active run callback, on the callback's owning thread. The worker and Host both enforce run identity, stage, and capabilities. Decimal/UTC validation, message/queue limits, and stdout separation protect protocol correctness; they do not isolate malicious code. Do not embed access tokens or client credentials in strategy source, frozen parameters, logs, or plots.

The current P1 integration does not provide a broker or live order service. Desktop SDK pinning and Runtime/signature verification remain separate responsibilities; an SDK source installation is not proof of platform or release acceptance. See [Hosted strategies](hosted-strategies.md).
