import { Button } from "./components/Button.jsx";
import { Badge } from "./components/Badge.jsx";
import { Card } from "./components/Card.jsx";

function Section({ title, children }) {
  return (
    <section style={{ marginBottom: "2rem" }}>
      <h2>{title}</h2>
      <div style={{ marginTop: "0.75rem" }}>{children}</div>
    </section>
  );
}

export function Library() {
  return (
    <main style={{ padding: "2rem", maxWidth: "720px" }}>
      <h1>Design System Library</h1>
      <p>
        Reconciled against the "Design System v2" Figma file. Every approved
        foundation and component, organized by layer order.
      </p>

      <Section title="Color (reconciled — Figma authoritative)">
        <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
          {["primary", "danger", "success-text", "warning-text", "text", "border"].map((name) => (
            <div key={name} style={{ textAlign: "center" }}>
              <div
                style={{
                  width: "48px",
                  height: "48px",
                  borderRadius: "4px",
                  border: "1px solid var(--color-border)",
                  background: `var(--color-${name})`,
                }}
              />
              <div style={{ fontSize: "0.75rem" }}>--color-{name}</div>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Button (reconciled — variant prop, danger added)">
        <div style={{ display: "flex", gap: "0.75rem" }}>
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="danger">Danger</Button>
          <Button variant="primary" disabled>Disabled</Button>
        </div>
      </Section>

      <Section title="Badge (new — built from Figma spec)">
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <Badge variant="neutral">Neutral</Badge>
          <Badge variant="success">Success</Badge>
          <Badge variant="warning">Warning</Badge>
          <Badge variant="danger">Danger</Badge>
        </div>
      </Section>

      <Section title="Card (preserved — already aligned with Figma)">
        <div style={{ maxWidth: "320px" }}>
          <Card title="Card title">Body content, unchanged from before reconciliation.</Card>
        </div>
      </Section>

      <Section title="Legacy (not migrated by init — recorded for ticket-time migration)">
        <p style={{ fontSize: "0.875rem", color: "var(--color-text-secondary)" }}>
          <code>src/legacy/OldCard.jsx</code> is used more often (3 places) than{" "}
          <code>Card.jsx</code> (2 places), but doesn't match either source of
          truth. It's recorded as legacy with a migration target to{" "}
          <code>Card</code>, not rebuilt here — higher usage isn't the same as
          being correct.
        </p>
      </Section>
    </main>
  );
}
