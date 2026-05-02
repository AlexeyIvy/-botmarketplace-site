/**
 * Global trading kill-switch (docs/54-T6 §5 / docs/15-operations §6.3).
 *
 * Operators flip `TRADING_ENABLED=false` (or `0` / `no` / `off`) to halt
 * every Bybit order placement at the lowest layer of the stack. Read-only
 * paths (status fetch, market data, balance reconciliation) are NOT
 * guarded — only outbound order placement is.
 *
 * Default behaviour is **fail-open**: if `TRADING_ENABLED` is unset, the
 * switch is considered ON. This keeps existing dev / demo environments
 * working without an explicit setting; production deployments wishing
 * to gate live trading must set the variable explicitly to a truthy
 * value (or rely on `BYBIT_ENV=demo`, see runbook §6.3).
 *
 * Errors thrown here are classified as `transient` by `errorClassifier`
 * (matched on the message pattern `/trading disabled/i`) so the worker
 * retry loop will pick the order up again on the next tick once an
 * operator re-enables trading. No manual intent re-queuing is required.
 */

const FALSE_LITERALS = new Set(["false", "0", "no", "off"]);

/**
 * Is global trading currently enabled?
 *
 * Read at every call site — the env variable is intentionally not cached
 * so an operator can flip it without restarting the process if they
 * have shell access to the host (the variable is read on every order
 * placement attempt).
 */
export function isTradingEnabled(): boolean {
  const raw = process.env.TRADING_ENABLED;
  if (raw === undefined) return true; // fail-open
  const normalised = raw.trim().toLowerCase();
  if (normalised === "") return true; // empty string ⇒ unset ⇒ enabled
  return !FALSE_LITERALS.has(normalised);
}

/**
 * Thrown when the global kill-switch is off and order placement is
 * attempted. Carries no extra fields — the message is the classifier
 * key ("trading disabled" matches `/trading disabled/i`).
 */
export class TradingDisabledError extends Error {
  constructor(message = "Trading disabled by global TRADING_ENABLED kill switch") {
    super(message);
    this.name = "TradingDisabledError";
  }
}

/**
 * Throw `TradingDisabledError` if the kill-switch is off; no-op otherwise.
 *
 * Intended call site: at the top of any function that places an outbound
 * order on the exchange. Read-only fetches (status, market data, wallet)
 * must NOT call this — operators need diagnostics to keep working
 * during an incident.
 */
export function assertTradingEnabled(): void {
  if (!isTradingEnabled()) {
    throw new TradingDisabledError();
  }
}
