# SC001 / B15-P1 — dialog handoff v6.37 — 2026-09-25

Current state:

`B15P1_V011_SOURCE_VALIDITY_TIMEOUT_READ_ONLY_DIAGNOSTIC_NEXT`

## Latest real retry

v0.1.1 correctly handled startup NOT_READY, but never observed a fully valid poll.

Repeated:

`NOT_READY = valid_poll_count:0`

Final:

`reason=collector_initial_readiness_timeout`

Rollback completed:

`rollback_incomplete=0`

Collector had reached RUNNING and price/PnL remained CLOSED.

## Important interpretation

The old ERR-trap/timing bug is fixed.

Now at least one fast source is invalid on every poll. Do not guess the venue/cause.

Poll evidence already contains exact venue status/error/http/raw SHA and can be analyzed without any new exchange call.

## Read-only diagnostic

`scripts/research/diagnose-b15p1-final-launch-v0.1.1-source-invalid-v0.1.py`

SHA256:

`fb4401b355cbc098863b9913cdaafaea5b5974ece7dbc35a0031265047780470`

The diagnostic:
- reads saved evidence only;
- does not load credentials;
- performs no exchange/API calls;
- does not start/enable systemd;
- does not modify collector state/polls/raw;
- writes only a separate diagnostic report.

Next: run the diagnostic on VPS and inspect venue-specific source errors before any retry.
