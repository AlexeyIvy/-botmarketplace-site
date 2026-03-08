// /lab/test — Test tab placeholder (Phase 5 will add Test Runner)
export default function LabTestPage() {
  return (
    <div style={{ padding: "48px 40px" }}>
      <h2 style={{ fontSize: 18, marginBottom: 12, color: "var(--text-primary)" }}>
        Test
      </h2>
      <p style={{ color: "var(--text-secondary)", fontSize: 14, lineHeight: 1.6 }}>
        Test runner coming in Phase 5. You will be able to run reproducible
        backtests against explicit datasets with full diagnostics and equity
        curve.
      </p>
    </div>
  );
}
