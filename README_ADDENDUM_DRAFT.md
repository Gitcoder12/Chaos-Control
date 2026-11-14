# Chaos-Control — README Explanation Draft

## In plain language

A Python tool that reads records from several sources, converts them into one common format and lets multiple sources be read concurrently.

## Example

Point the collector at a folder of CSV and JSONL files. It reads each file as records and yields them in one common structure. A source can fail without necessarily stopping all other sources.

## Technical explanation

Single-file asynchronous Python collector that reads JSONL/NDJSON, CSV and plain text, recursively walks directories, and optionally streams line-oriented HTTP(S) responses using httpx. A bounded queue/semaphore provides concurrency and source errors can be isolated. It is a collector library/prototype, not a complete production data platform.

Document source adapters, async generator flow, queue/semaphore limits, error policy, Record fields, HTTP line handling and resource cleanup.

## Limitations

An asynchronous collector does not itself provide durable storage, exactly-once delivery, schema governance or a production retry queue. State which are absent.

## Contributing

See FEATURE_UPGRADE_PLAN.md and CONTRIBUTING.md.
