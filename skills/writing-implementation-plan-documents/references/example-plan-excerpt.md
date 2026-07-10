# Example Plan Excerpt

This is a calibration excerpt from a `Ready` plan. It shows one capability-based work
package, one rejected split, and the shared Verification Summary. Use its level of
specificity, not its content.

* * *

## Work Package 2: Rate Limit Enforcement in the Request Pipeline

Wire the `RateLimiter` delivered by `WP1` into the HTTP request pipeline and reject
over-limit requests. Enforcement precedes the admin UI because it can operate behind
the existing `rate-limits.enabled` flag while later management surfaces are built.

**ID:** `WP2`
**Depends on:** `WP1` (`RateLimiter`, `RateLimitConfig`)
**Done when:** Requests over the configured per-key limit receive `429 Too Many
Requests` with `Retry-After`; under-limit requests are unchanged; disabling
`rate-limits.enabled` restores the pre-plan request path.
**Checkpoint:** None

### 2.1 Enforcement filter

**New file:** `gateway-api/src/main/java/org/example/gateway/api/RateLimitFilter.java`

Add a servlet filter that resolves the authenticated API key, consults the limiter, and
either continues the chain or returns `429`. Mirror `ApiAuthFilter` for construction and
registration rather than introducing another filter lifecycle.

```java
public final class RateLimitFilter implements Filter {
    private final RateLimiter limiter;
    private final ApiKeyResolver keyResolver;

    @Override
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain);
}
```

**Notes:**

- Requests without an authenticated key pass to the existing authorization failure
  path and do not consume a guessed or caller-supplied key's budget.
- `Retry-After` is the number of seconds until the current window resets, obtained from
  `RateLimiter.retryAfter(key)`.
- Limiter failures use the design's fail-closed policy and emit the existing request
  rejection metric without logging API keys.

### 2.2 Filter registration and configuration gate

**File:** `gateway-api/src/main/java/org/example/gateway/api/GatewayApiModule.java`

Register `RateLimitFilter` after `ApiAuthFilter`, gated by `rate-limits.enabled`. Follow
the conditional-registration pattern used by `AuditLogFilter`.

### Design Decisions

- **Filter after authentication.** Running before authentication would let callers
  consume another key's budget through spoofed headers. Authentication failures remain
  outside this limiter because that path is already cheap and separately protected.

### Failure, Safety, and Security

- Do not derive limiter identity from an unauthenticated header.
- Do not include raw API keys in logs, metrics, or error bodies.
- Preserve the configured fail-closed policy when the limiter backend is unavailable.

### Tests

**New file:** `gateway-api/src/test/java/org/example/gateway/api/RateLimitFilterTest.java`

Tests:

- An under-limit authenticated request invokes the chain without extra headers.
- An over-limit request returns 429 with `Retry-After` and does not invoke the chain.
- Disabling the flag leaves the filter unregistered and preserves baseline behavior.
- A request without an authenticated key passes to the existing authorization path.
- A scripted two-key burst limits one key without affecting the other.
- A limiter backend failure follows fail-closed policy without exposing the key.

### Verification

#### Automated

- [ ] Standard gate for `gateway-api` — commands in
  [Verification Summary](#verification-summary)
- [ ] Run `RateLimitFilterTest` with the deterministic clock and limiter fixture.

#### Agent review

- [ ] Confirm filter order is authentication, rate limiting, then request dispatch.
- [ ] Confirm no log or metric records the raw key.

### Implementation Notes

Filled in during implementation. Record dated deviations and update downstream work
packages, readiness, and the File Inventory when a note changes their assumptions.

*None yet.*

* * *

## Rejected Splits

- **Separate filter construction from registration.** The first work package would
  introduce dead code that no request executes, while registration is a small part of
  the same independently verifiable capability.

* * *

## Verification Summary

### Standard affected-scope gate

```bash
mvn -q -pl gateway-api test -Dtest=RateLimitFilterTest
mvn -q -pl gateway-api spotless:check
mvn -q -pl gateway-api package -DskipTests
```

### Final plan gate

```bash
mvn -q clean verify
```

| Work package | Scope | Required evidence |
| --- | --- | --- |
| `WP1` | `gateway-core` | `RateLimiterTest` and module build |
| `WP2` | `gateway-api` | `RateLimitFilterTest`, formatting check, package build |
| Final | full build | `mvn -q clean verify` |
