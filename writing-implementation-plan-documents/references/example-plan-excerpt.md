# Example Plan Excerpt

This is a filled-in excerpt from a realistic plan — one phase, one Rejected Splits
entry, and the Verification Summary — showing the target level of detail: decisions and
shape, not implementations. It is calibration material for the author; don't copy its
content into new plans.

* * *

## Phase 2: Rate Limit Enforcement in the Request Pipeline

Wires the `RateLimiter` built in Phase 1 into the HTTP request pipeline and rejects
over-limit requests. Comes after Phase 1 because it consumes the limiter's public API;
comes before the admin UI (Phase 3) so enforcement can soak behind the existing
`rate-limits.enabled` config flag while the UI is built.

**Depends on:** Phase 1 (`RateLimiter`, `RateLimitConfig`).

**Done when:** Requests over the configured per-key limit receive `429 Too Many
Requests` with a `Retry-After` header; under-limit requests are unaffected; setting
`rate-limits.enabled=false` restores pre-plan behavior exactly.

### 2.1 Enforcement filter

**New file:** `gateway-api/src/main/java/org/example/gateway/api/RateLimitFilter.java`

A servlet filter that resolves the API key from the request, consults the limiter, and
either passes the request through or short-circuits with 429. Registered alongside the
existing auth filter — mirror `ApiAuthFilter`'s registration and ordering.

```java
public class RateLimitFilter implements Filter {
    private final RateLimiter limiter;          // from Phase 1
    private final ApiKeyResolver keyResolver;   // existing component

    @Override
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)
        // resolve key -> limiter.tryAcquire(key) -> 429 + Retry-After, or chain
}
```

**Notes:**
- Requests with no resolvable API key bypass the limiter (they are rejected by
  `ApiAuthFilter` later in the chain; see Gaps for the anonymous-endpoint case).
- `Retry-After` is seconds until the current window resets, from
  `RateLimiter.retryAfter(key)`.

### 2.2 Filter registration and config gate

**File:** `gateway-api/src/main/java/org/example/gateway/api/GatewayApiModule.java`

Register `RateLimitFilter` after `ApiAuthFilter` in the filter chain, gated on
`rate-limits.enabled`. Follows the existing conditional-registration pattern used for
`AuditLogFilter`.

### Design Decisions

**Filter order — after auth, not before:** Limiting before auth would let unauthenticated
traffic consume a key's budget via spoofed headers. Costs us limiter protection for the
auth path itself, which is acceptable: auth failures are already cheap and cached.

### Tests

**File:** `gateway-api/src/test/java/org/example/gateway/api/RateLimitFilterTest.java`

Tests:
- Under-limit request passes through unchanged (chain invoked, no extra headers).
- Over-limit request gets 429, `Retry-After` set, chain not invoked.
- Disabled flag: filter not registered; behavior identical to pre-plan baseline.
- Missing API key: request passes to the chain untouched.

### Verification

#### Automated

- [ ] Standard gate for `gateway-api` — commands in
  [Verification Summary](#verification-summary)

#### Manual

These checks require a human. An agent implementing this phase must stop and request
verification rather than checking these boxes.

- [ ] With a 5 req/min limit configured, a scripted burst from one key returns 429 on
  request 6; a second key is unaffected.

### Implementation Notes

Filled in during implementation, not during planning. Record dated entries for
deviations from the plan, surprises, and newly discovered work. If an entry invalidates
a later phase or the File Inventory, update those sections too — the Notes are the
changelog; the plan body is the current truth.

*None yet.*

* * *

## Rejected Splits

- **Split Phase 2 into 2a (filter class) and 2b (registration).** 2a would ship a
  filter no request path executes — dead code with tests asserting behavior nothing
  exercises. Registration is two lines; it belongs with the filter it registers.

* * *

## Verification Summary

Standard per-phase gate:

```bash
mvn -q spotless:apply
mvn -q -pl gateway-api clean compile
mvn -q -pl gateway-api test -Dtest=RateLimitFilterTest
```

The final phase additionally runs a full build:

```bash
mvn -q clean verify
```

| Phase | Build scope | Test target |
| --- | --- | --- |
| 1 | `gateway-core` | `RateLimiterTest` |
| 2 | `gateway-api` | `RateLimitFilterTest` |
| Final | full build | all tests (`mvn -q clean verify`) |
