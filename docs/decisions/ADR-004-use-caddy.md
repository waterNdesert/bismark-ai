# ADR-004 — Use Caddy as the Production Reverse Proxy and TLS Termination Layer

**Project:** Bismark AI  
**ADR ID:** ADR-004  
**Title:** Use Caddy for Reverse Proxying and Automatic HTTPS  
**Status:** Accepted  
**Date:** 2026-09-23  
**Decision Owners:** Bismark AI Product/Engineering  
**Scope:** V1 backend edge architecture

---

## 1. Context

Bismark AI requires a secure public entry point for its backend API.

The backend runs on a Hostinger VPS and includes:

```text
FastAPI
background worker
Redis
document parser dependencies
```

Only the FastAPI application should be exposed publicly.

The deployment requires a reverse proxy that can:

- terminate HTTPS;
- obtain and renew TLS certificates;
- redirect HTTP to HTTPS;
- proxy traffic to the internal FastAPI container;
- remain simple to operate;
- work cleanly with Docker Compose;
- avoid unnecessary operational complexity.

Several options were considered:

1. Caddy;
2. Nginx;
3. Traefik;
4. exposing FastAPI directly;
5. a managed load balancer or external proxy service.

---

## 2. Decision

Bismark AI V1 will use **Caddy** as the production reverse proxy and TLS termination layer.

The public backend topology will be:

```text
Internet
   |
   v
Caddy
   |
   v
FastAPI
```

Caddy will handle:

```text
HTTP
HTTPS
TLS certificate issuance
TLS certificate renewal
reverse proxying
HTTP -> HTTPS redirection
```

---

## 3. Why Caddy

### 3.1 Automatic HTTPS

Caddy provides automatic certificate issuance and renewal with minimal configuration.

This reduces the operational work required for:

- certificate provisioning;
- renewal automation;
- HTTPS redirects;
- TLS configuration.

---

### 3.2 Simple Configuration

A basic production API proxy can remain concise.

Conceptual example:

```caddy
api.bismark.ai {
    reverse_proxy api:8000
}
```

This is easier to maintain than a more verbose equivalent configuration when the required edge topology is simple.

---

### 3.3 Good Docker Fit

Caddy works cleanly as a Docker Compose service.

Expected services:

```text
caddy
api
worker
redis
```

Caddy can communicate with FastAPI through a Docker network while remaining the only application service publishing web ports.

---

### 3.4 Operational Simplicity

Bismark AI V1 deliberately avoids excessive infrastructure.

Caddy supports that goal by keeping:

- TLS;
- reverse proxying;
- certificate renewal;

inside one small component.

---

## 4. Responsibilities

Caddy is responsible for:

- listening on public HTTP/HTTPS ports;
- automatic TLS;
- reverse proxying API traffic;
- redirecting HTTP to HTTPS;
- optionally setting approved response/security headers;
- optionally supporting HTTP/3 if configured.

Caddy is not responsible for:

- user authentication;
- authorization;
- tenant isolation;
- rate-limit business policy;
- database access;
- RAG logic;
- document processing.

Those remain application responsibilities.

---

## 5. Public Ports

The host should expose only the required ports.

Expected:

```text
22/tcp
80/tcp
443/tcp
```

Optional:

```text
443/udp
```

for HTTP/3.

FastAPI's internal port should not be publicly published.

Redis must never be publicly exposed.

---

## 6. Internal Network Model

Recommended Docker topology:

```text
Internet
   |
   v
caddy:80/443
   |
   v
api:8000
```

Internal-only services:

```text
worker
redis
```

Caddy should not need direct access to Redis.

---

## 7. Docker Compose Role

Caddy should run as a dedicated service.

Conceptual:

```yaml
services:
  caddy:
    image: caddy:2
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"
    volumes:
      - ./infra/caddy/Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
```

Persist:

```text
/data
/config
```

so certificate state is not lost unnecessarily.

---

## 8. DNS Requirements

The API hostname must resolve to the Hostinger VPS public IP.

Example:

```text
api.bismark.ai
```

DNS must be correct before expecting automatic certificate issuance.

---

## 9. HTTPS Policy

Production traffic must use HTTPS.

HTTP should redirect to HTTPS.

Do not expose a separate insecure application endpoint for convenience.

---

## 10. TLS Management

Caddy should handle automatic certificate renewal.

Operators should monitor:

- certificate issuance failures;
- DNS misconfiguration;
- port blocking;
- renewal problems.

---

## 11. Security Headers

Caddy may set selected headers where appropriate.

Possible examples:

```text
Strict-Transport-Security
X-Content-Type-Options
Referrer-Policy
```

However, security headers should not be added blindly.

Content Security Policy is primarily a frontend concern and should be tested carefully.

---

## 12. Request Size

Caddy may enforce request-size limits in combination with the application.

However, the backend must still enforce:

```text
MAX_UPLOAD_SIZE_MB
```

Proxy limits are defense in depth, not the sole control.

---

## 13. Client IP Handling

If FastAPI uses forwarded client IP information:

- trusted proxy count must be configured;
- forwarding headers must be handled safely;
- the application must not blindly trust arbitrary client-provided `X-Forwarded-For`.

---

## 14. Health Checks

Caddy may proxy:

```text
/health
/ready
```

to FastAPI.

Infrastructure should use these endpoints appropriately.

---

## 15. Alternative Considered — Nginx

### Benefits

- widely deployed;
- mature ecosystem;
- highly configurable;
- extensive operational knowledge.

### Drawbacks

- certificate automation usually requires separate tooling or more configuration;
- more verbose configuration for this simple V1 use case;
- Bismark AI does not currently need advanced Nginx-specific features.

### Decision

Not selected for V1.

Nginx remains a viable future alternative if operational requirements change.

---

## 16. Alternative Considered — Traefik

### Benefits

- strong Docker integration;
- dynamic service discovery;
- useful for larger container environments.

### Drawbacks

- more complexity than required;
- Bismark AI currently has a very small service topology;
- dynamic routing capabilities are unnecessary for V1.

### Decision

Rejected for initial V1.

---

## 17. Alternative Considered — Direct FastAPI Exposure

### Benefits

- fewer components;
- simpler local testing.

### Drawbacks

- weaker production edge posture;
- certificate management burden;
- less separation between application server and public edge;
- no dedicated TLS/reverse-proxy layer.

### Decision

Rejected for production.

FastAPI may be directly exposed only in local development.

---

## 18. Alternative Considered — Managed Load Balancer

### Benefits

- high availability;
- managed TLS;
- advanced routing;
- easier horizontal scaling.

### Drawbacks

- additional cost;
- unnecessary complexity for one VPS;
- no immediate need for multi-node routing.

### Decision

Deferred.

Revisit if Bismark AI moves to multiple backend nodes.

---

## 19. Failure Implications

If Caddy fails:

- the API becomes unavailable externally;
- internal FastAPI may remain healthy.

Container restart policy should be:

```text
restart: unless-stopped
```

or equivalent.

---

## 20. Recovery

If Caddy configuration is broken:

1. validate config;
2. inspect logs;
3. revert last change;
4. reload/restart;
5. test HTTPS;
6. test API health.

Before reload:

```bash
caddy validate --config /etc/caddy/Caddyfile
```

where appropriate.

---

## 21. Configuration Validation

Configuration changes should be validated before production reload.

Do not deploy malformed Caddy configuration directly.

---

## 22. Secrets

Caddy should not contain:

- Supabase service-role key;
- Voyage key;
- LLM key;
- database credentials.

Its role is network edge management.

---

## 23. Logging

Caddy access logs may be enabled.

Do not log:

- authorization headers;
- sensitive query parameters;
- secrets.

Retention must be bounded.

---

## 24. Reverse Proxy Headers

Caddy should pass standard proxy metadata such as:

- host;
- protocol;
- client address;

using trusted defaults.

FastAPI should be configured appropriately for trusted proxy behavior.

---

## 25. WebSocket / Streaming Compatibility

Bismark AI chat uses streaming responses.

Caddy configuration must preserve streaming behavior.

The proxy must not introduce excessive buffering that delays token delivery.

---

## 26. SSE Compatibility

If Server-Sent Events are used:

```text
FastAPI
→ Caddy
→ browser
```

must support long-lived streaming connections.

This should be verified in staging.

---

## 27. Timeout Considerations

Proxy timeouts should allow legitimate long-running streamed chat responses.

Do not set aggressive timeouts that terminate valid generation streams.

---

## 28. Upload Considerations

Large document uploads may take longer than ordinary API requests.

Caddy configuration must not prematurely terminate valid uploads within the configured product limit.

---

## 29. HTTP/3

HTTP/3 is optional.

If enabled:

```text
443/udp
```

must be allowed through UFW.

Bismark AI does not depend on HTTP/3.

---

## 30. Certificate Storage

Certificate data should persist across container restarts.

Use Docker volumes:

```text
caddy_data
caddy_config
```

---

## 31. Domain Migration

If the API domain changes:

1. update DNS;
2. update Caddyfile;
3. update backend environment configuration;
4. update frontend API URL;
5. update CORS;
6. verify TLS issuance;
7. smoke test.

---

## 32. Security Consequences

Positive:

- production HTTPS by default;
- reduced certificate-maintenance burden;
- internal application ports remain private.

Risk:

- misconfigured reverse proxy could expose unintended routes or headers.

Mitigation:

- minimal config;
- config validation;
- deployment tests.

---

## 33. Operational Consequences

Positive:

- easy configuration;
- simple Docker deployment;
- automatic TLS lifecycle.

Negative:

- another service to monitor;
- certificate issuance depends on correct DNS/networking.

---

## 34. Scaling Consequences

Caddy works well for the initial single-node design.

If the backend later becomes multi-node, options include:

- Caddy load balancing;
- external managed load balancer;
- alternative ingress architecture.

A material change requires a new ADR.

---

## 35. Implementation Requirements

Agents implementing this decision must:

- deploy Caddy via Docker Compose;
- keep API container port internal;
- persist Caddy state;
- use production domain configuration;
- enforce HTTPS;
- preserve streaming;
- keep Redis private.

---

## 36. Prohibited Actions

Without a superseding ADR, do not:

- replace Caddy with Nginx;
- replace Caddy with Traefik;
- expose FastAPI directly to the public internet in production;
- expose Redis through Caddy;
- store application secrets in the Caddyfile;
- disable HTTPS for production.

---

## 37. Review Triggers

Revisit this decision if:

- multiple backend nodes require more advanced load balancing;
- enterprise networking requirements change;
- managed ingress becomes operationally preferable;
- Caddy becomes incompatible with required infrastructure;
- platform moves away from single-VPS deployment.

---

## 38. Consequences Summary

### Positive

- automatic TLS;
- minimal config;
- Docker-friendly;
- simple operations;
- good streaming support;
- clean public/private service boundary.

### Negative

- single-node dependency;
- another container to operate;
- requires correct DNS and open ports.

---

## 39. Status

**Accepted**

Caddy is the canonical reverse proxy and TLS termination layer for Bismark AI V1.

The expected edge path is:

```text
Internet
→ Caddy
→ FastAPI
```

Any replacement requires a new or superseding ADR.
