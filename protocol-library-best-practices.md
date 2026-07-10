# Protocol Library Best Practices

## Core Principle

Organize the library around the protocol, not around a transport framework.

The core module should model messages, frames, codecs, client/server behavior,
errors, and transport interfaces in protocol terms. Concrete transports then
adapt those abstractions to TCP, TLS, serial devices, hardware, in-memory tests,
or a framework such as Netty.

Netty is a good default for Java TCP/TLS transports, but it should usually be an
implementation module, not the conceptual center of the library.

## Recommended Libraries

- Use JSpecify (`org.jspecify:jspecify`) in core from the beginning. Mark public
  packages or classes with `@NullMarked` and annotate intentional nullable
  boundaries before callers depend on ambiguous nullness.
- Use Netty for TCP-based and TLS-over-TCP transports. Keep Netty runtime types
  out of high-level protocol APIs.
- For Netty TCP client transports that need reconnect, lazy reconnect, idle
  keep-alive, or non-blocking `Channel` access, consider
  `com.digitalpetri.netty:netty-channel-fsm`. Keep it inside the TCP transport
  module; do not let it become part of the core protocol API.
- Use jOOU (`org.jooq:joou`, package `org.joou`) when unsigned protocol fields
  cross public API boundaries. Prefer `UByte`, `UShort`, `UInteger`, and `ULong`
  when unsigned semantics are part of the domain model.
- Keep core dependency-light. Add larger utility libraries only when they
  improve API clarity, correctness, or interoperability enough to justify the
  dependency surface.

## Repository Shape

Prefer a small multi-module layout unless the repository already has a stronger
convention:

```text
example-parent/
|-- pom.xml
|-- example-core/              # protocol model, codecs, client/server APIs
|-- example-transport-tcp/     # TCP/TLS transport, usually Netty-backed
|-- example-transport-serial/  # optional serial or hardware transport
|-- example-testkit/           # optional reusable fixtures
`-- example-tests/             # cross-module integration tests, not published
```

Core should contain protocol-neutral abstractions and minimal dependencies.
Transport modules should contain sockets, TLS, event loops, device handles,
framework pipelines, native dependencies, and transport-specific configuration.

## Public API

- Use immutable records or final classes for messages and config.
- Validate required config in builders and protocol fields in message
  constructors or factories.
- Defensively copy arrays and mutable buffers at public boundaries unless
  ownership is explicitly documented.
- Prefer asynchronous transport methods returning `CompletionStage`.
- Add blocking convenience methods only at the high-level API, with deliberate
  exception translation.
- Keep runtime transport types out of core public APIs. Netty `Channel`,
  `EventLoopGroup`, `SslHandler`, and pooled `ByteBuf` objects should not appear
  in message, client, or server APIs by accident.
- Model protocol failures as typed exceptions or result objects so callers can
  distinguish timeout, connection failure, malformed local input, remote
  protocol error, unsupported operation, and unexpected execution failure.

## Protocol Model And Codecs

- Put public message, PDU, request, and response types in core.
- Use typed enums or value classes for discriminators and status codes.
- Preserve unknown codes when the protocol requires extension or forwarding.
- Represent unsigned protocol values deliberately. Use jOOU wrappers when the
  unsigned meaning matters to callers; use primitive widening only for internal
  calculations where the signed carrier cannot escape.
- Split transport framing from payload encoding/decoding.
- Decode payloads where role context is known, especially when the same
  discriminator can appear in both request and response directions.
- Validate malformed input during decode: too short, too long, impossible
  length, unsupported discriminator, invalid flags, bad checksum, bad version,
  and trailing bytes when disallowed.
- Never rely on Java `assert` for wire validation.

Choose a buffer strategy before writing codecs:

- Prefer `byte[]` or `ByteBuffer` in core when codecs must work across Netty,
  serial, file, test, hardware, or non-Netty transports.
- Use Netty `ByteBuf` in core only when a `netty-buffer` dependency is
  deliberate and every public boundary documents ownership and release rules.
- If a transport stores, slices, duplicates, or forwards a pooled buffer, test
  retain/release behavior.

### Co-located Serde/Codec Pattern

When a protocol record, struct, or class must be wire serializable, keep its
encode/decode logic in a nested static helper on the type itself rather than in a
separate, central codec registry. This keeps the wire format next to the data
model it describes, so a field and its serialization always change together.

- Model the message as an immutable `record` (or `final class`) carrying
  domain-typed fields. Use jOOU unsigned wrappers (`UByte`, `UShort`,
  `UInteger`, `ULong`) where the unsigned meaning is part of the domain.
- Nest a `public static final class Serde` (or `Codec`) with a private
  constructor so it is a static-only utility that cannot be instantiated.
- Expose exactly two static methods: `encode(Message, Buffer)` and
  `decode(Buffer) -> Message`. Keep the method names and shapes uniform across
  every message type so call sites and generic dispatch are predictable.
- Convert at the wire boundary inside `Serde`: widen unsigned wrappers to the
  signed carrier on encode (`request.length().intValue()`), and re-wrap on
  decode (`UInteger.valueOf(buffer.readUnsignedIntLE())`). The signed carrier
  never escapes into the public type.
- Make endianness and width explicit in the read/write calls
  (`writeIntLE`/`readUnsignedIntLE`); do not rely on buffer defaults.
- Javadoc the record components and the `encode`/`decode` methods so the wire
  contract is documented alongside the model.

```java
/**
 * Request to read data from an ADS device.
 *
 * @param indexGroup index group of the data to read.
 * @param indexOffset index offset of the data to read.
 * @param length length of the data (in bytes) to read.
 */
public record AdsReadRequest(UInteger indexGroup, UInteger indexOffset, UInteger length) {

  /** Serialization and deserialization utilities for {@link AdsReadRequest}. */
  public static final class Serde {

    private Serde() {}

    /**
     * Encode a request into the provided buffer.
     *
     * @param request the request to encode.
     * @param buffer the buffer to encode into.
     */
    public static void encode(AdsReadRequest request, ByteBuf buffer) {
      buffer.writeIntLE(request.indexGroup().intValue());
      buffer.writeIntLE(request.indexOffset().intValue());
      buffer.writeIntLE(request.length().intValue());
    }

    /**
     * Decode a request from the provided buffer.
     *
     * @param buffer the buffer to decode from.
     * @return the decoded request.
     */
    public static AdsReadRequest decode(ByteBuf buffer) {
      UInteger indexGroup = UInteger.valueOf(buffer.readUnsignedIntLE());
      UInteger indexOffset = UInteger.valueOf(buffer.readUnsignedIntLE());
      UInteger length = UInteger.valueOf(buffer.readUnsignedIntLE());

      return new AdsReadRequest(indexGroup, indexOffset, length);
    }
  }
}
```

The buffer type in the `Serde` signatures is governed by the buffer-strategy
choice above. The example uses Netty `ByteBuf`, which is appropriate only when a
`netty-buffer` dependency in core is deliberate; otherwise use `byte[]` or
`ByteBuffer` so the codec stays transport-neutral. Apply the malformed-input
validation rules above inside `decode`.

## Transport, Client, And Server Design

Transport interfaces should operate on protocol frames or envelopes, not on
framework channels.

Typical client transport shape:

```java
CompletionStage<Void> connect();
CompletionStage<Void> disconnect();
boolean isConnected();
CompletionStage<Void> send(ExampleFrame frame);
void receive(Consumer<ExampleFrame> receiver);
```

Client behavior:

- On send, encode the request, create a promise, schedule a timeout, store the
  promise, send the frame, and clean up on send failure.
- On response, match the promise, cancel the timeout, validate the frame, decode
  the payload, and complete the future.
- Clean up promises exactly once on response, timeout, send failure, disconnect,
  and unrecoverable parser errors.
- Use the protocol's real correlation model. If there is no correlation id,
  restrict to one in-flight request or document a FIFO policy only when ordered
  responses are guaranteed.
- Expose one-way or no-response operations as send-completion APIs, not fake
  response futures.

Server behavior:

- Define a core service interface that receives request context plus typed
  requests and returns typed responses or protocol-native errors.
- Keep transport metadata in narrow context interfaces: addresses, TLS peer
  certificate, negotiated session data, authenticated principal, and similar.
- Implement authorization, logging, metrics, tracing, and simulation as service
  decorators where possible.
- Do not run blocking user handlers on event-loop or I/O threads.

## Netty-Backed TCP Transport

Use Netty for robust Java TCP/TLS transports, but isolate it:

- Put `Bootstrap`, `ServerBootstrap` when server support exists, `Channel`,
  Netty `ChannelHandler` implementations, event-loop configuration, TLS setup,
  and handlers that convert between Netty `ByteBuf` values and core frame types
  in the TCP transport module. Keep transport-neutral payload serializers in
  core.
- Consider `netty-channel-fsm` for outgoing TCP channel lifecycle management;
  DigitalPetri Modbus uses it this way in its `modbus-tcp` transport while
  keeping the core transport interface protocol-shaped.
- Expose Netty-specific customization through TCP transport config, such as
  `bootstrapCustomizer`, `serverBootstrapCustomizer`, named pipeline extension
  points, and event-loop injection.
- Build pipelines in a fixed safe order: TLS/security first, then framing,
  protocol frame adapter, optional metrics/logging/backpressure, and finally
  user extension points that cannot bypass required validation.
- Complete `connect()` only after TLS handshake succeeds when TLS is enabled.
- Track accepted server channels so `unbind()` closes both the listening channel
  and client channels.
- Use per-channel parser state.
- Test Netty frame codecs and handlers with `EmbeddedChannel`, including partial
  reads and malformed frames.

## Shared Resources And Lifecycle

A protocol library needs expensive, long-lived runtime resources — thread pools,
scheduled executors, Netty event-loop groups, timers — but most of its objects
should not own them. Creating a fresh `ExecutorService` or `EventLoopGroup` per
client or per connection wastes threads and file descriptors, and an application
that hosts many clients usually already has these resources to hand.

Make every such resource configurable but optional. When a caller does not
supply one, fall back to a lazily-initialized, process-wide shared instance.
Callers who already have an executor or event loop — most non-trivial
applications do — inject their own and avoid duplication; casual callers get
working defaults with no setup.

### Where shared resources live

Split the shared resources by dependency surface, mirroring the module split:

- Put transport-neutral resources (`ExecutorService`, `ScheduledExecutorService`)
  in a holder in core. DigitalPetri Modbus uses a `Modbus` class with
  `sharedExecutor()` and `sharedScheduledExecutor()`.
- Put framework-specific resources (Netty `EventLoopGroup`, `HashedWheelTimer`)
  in a holder in the transport module, not in core. DigitalPetri Modbus uses a
  `Netty` class in `modbus-tcp` with `sharedEventLoop()` and
  `sharedWheelTimer()`. This keeps Netty runtime types out of core, consistent
  with the core principle above.

### The holder

- Make the holder a `final` class with a private constructor (a static-only
  utility), or a Kotlin `object`.
- Lazily initialize each resource on first access, guarded for thread safety
  (`synchronized` accessor, or a holder/double-checked idiom).
- Name threads descriptively and number them (`"<lib>-event-loop-0"`) so they
  are identifiable in thread dumps and profilers.
- Mark the threads daemon so a shared singleton never keeps the JVM alive when
  the application is otherwise done.
- Give worker threads an uncaught-exception handler that logs, so a failure on a
  shared pool thread is visible rather than silent.

```java
public final class Modbus {

  private Modbus() {}

  private static ExecutorService EXECUTOR_SERVICE;

  public static synchronized ExecutorService sharedExecutor() {
    if (EXECUTOR_SERVICE == null) {
      ThreadFactory threadFactory = new ThreadFactory() {
        private final AtomicLong threadNumber = new AtomicLong(0L);

        @Override
        public Thread newThread(Runnable r) {
          Thread thread =
              new Thread(r, "modbus-shared-thread-pool-" + threadNumber.getAndIncrement());
          thread.setDaemon(true);
          thread.setUncaughtExceptionHandler(
              (t, e) -> LoggerFactory.getLogger(Modbus.class)
                  .warn("Uncaught Exception on shared ExecutorService thread", e));
          return thread;
        }
      };
      EXECUTOR_SERVICE = Executors.newCachedThreadPool(threadFactory);
    }
    return EXECUTOR_SERVICE;
  }
}
```

### Wiring the fallback through config

Apply the fallback once, at the boundary where config is finalized, so nothing
downstream has to know whether a resource is shared or caller-supplied:

- Expose the resource as a plain nullable builder field — no `Optional` wrapper,
  no default instance constructed eagerly.
- In `build()`, substitute the shared instance when the field is still null.
- Have the immutable config record carry a concrete, non-null instance.
  Point-of-use code reads `config.executor()` and never sees null, never
  branches on shared-vs-supplied.

```java
public Config build() {
  if (eventLoopGroup == null) {
    eventLoopGroup = Netty.sharedEventLoop();   // transport-module holder
  }
  if (executor == null) {
    executor = Modbus.sharedExecutor();         // core holder
  }
  return new Config(/* ... */ eventLoopGroup, executor);
}
```

Document the fallback on the builder setter so callers know the field is
optional and what they get if they leave it unset.

### Releasing shared resources

- Provide a `releaseSharedResources()` method on each holder that shuts the
  resources down gracefully, plus an overload taking a timeout and unit. Log a
  warning if a resource does not terminate within the timeout.
- Null out the references after shutdown so the next accessor call re-initializes
  fresh instances; this makes the holder safe across repeated test runs and
  application restarts within one classloader.
- Tell users to call it at JVM shutdown or when the classloader that loaded the
  library is unloaded — important in application servers, OSGi, and hot-redeploy
  environments where a leaked event loop or pool would otherwise survive the
  application. Daemon threads keep this from blocking JVM exit, but explicit
  release is the clean path and is required to reclaim resources mid-lifetime.
- A caller who injected their own resource owns its lifecycle; the holder only
  releases instances it created.

## Tests And Docs

Before calling an implementation complete, cover:

- Message validation and immutability.
- Golden-byte encode/decode for every message type.
- Complete, partial, malformed, and oversized frames.
- Client timeout cleanup, send failure, disconnect with in-flight requests,
  remote errors, malformed responses, and late/unmatched responses.
- Server dispatch, unsupported operations, protocol error mapping, unexpected
  exceptions, and request context population.
- Loopback integration for every supported transport.
- TLS trust success and failure when TLS is supported.
- Optional hardware/native tests behind profiles, tags, environment variables,
  or system properties.

Docs should explain module selection, lifecycle, dependencies, nullness
conventions, buffer ownership, and exact Maven commands for full verify,
targeted tests, formatting, and transport-specific integration tests. CI should
run the documented quality gate.
