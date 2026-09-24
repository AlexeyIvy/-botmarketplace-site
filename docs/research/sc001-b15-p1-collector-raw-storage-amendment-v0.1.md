# SC001 — B15-P1 Collector Raw Storage Implementation Amendment v0.1

Date: 2026-09-24  
Status: **IMPLEMENTATION-ONLY HARDENING / RESEARCH RULES UNCHANGED**

## Purpose

Avoid repeated storage of byte-identical full Bybit/OKX source responses while preserving exact raw evidence for every 15-second poll.

## Content-addressed object store

Exact HTTP response bytes are keyed by SHA256.

Each unique body is persisted once in an immutable object file.

Every poll ledger row references the exact object hash and byte length.

Therefore for every poll:

`poll -> raw_body_sha256 -> exact_raw_bytes`

is deterministic and auditable.

## Integrity

If an object path already exists, re-hash before reuse.

Mismatch =>

`RAW_OBJECT_INTEGRITY_FAIL`

and stop.

Object creation uses atomic temporary-file + fsync + rename semantics.

## Evidence semantics

Deduplication is permitted only for byte-identical bodies.

It does not deduplicate:

- poll timestamps;
- request timing;
- API status;
- rate-limit diagnostics;
- gap state;
- normalized state;
- route state;
- event transitions.

Those remain append-only per poll.

## Retention

No automatic protected-object deletion.

Daily close manifest contains the set of raw body hashes referenced during that day.

## Self-test

Offline implementation self-test must verify:

1. first write creates one object;
2. second identical write reuses the same object without changing bytes;
3. different bytes create a different object;
4. deliberate corruption of an existing object causes `RAW_OBJECT_INTEGRITY_FAIL`.
