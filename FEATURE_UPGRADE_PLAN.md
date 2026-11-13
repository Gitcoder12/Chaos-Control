# Chaos-Control — Feature Upgrade Plan

## Objective

A Python tool that reads records from several sources, converts them into one common format and lets multiple sources be read concurrently.

## P0 — safe ingestion

- [ ] Validate source configuration, file encodings, URL schemes, HTTP response limits and record-size limits.
- [ ] Test cancellation, partial source failure, queue backpressure and file traversal boundaries.

## P1 — stable records and observability

- [ ] Define a stable Record schema and document metadata/raw-field behavior for each source type.
- [ ] Add structured error events, counters and a clear CLI/example pipeline.

## P2 — performance and restart behavior

- [ ] Benchmark throughput/memory against fixed file and HTTP fixtures.
- [ ] Add optional checkpoint/restart semantics only after defining idempotency and source offsets.

## Contributor work packages

1. Source adapters and input validation.
2. Record schema and normalisation tests.
3. Async cancellation/backpressure and error handling.
4. Reproducible throughput/memory benchmark.

## Definition of done

- [ ] File and HTTP inputs have clear limits and errors.
- [ ] One source failure does not silently corrupt other output.
- [ ] Cancellation releases resources and stops tasks cleanly.
- [ ] Performance evidence states dataset, concurrency and environment.
