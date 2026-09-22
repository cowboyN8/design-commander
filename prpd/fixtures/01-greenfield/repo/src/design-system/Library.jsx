import { useState } from "react";
import { Text } from "./components/Text/Text";
import { Button } from "./components/Button/Button";
import { Badge } from "./components/Badge/Badge";
import { TextInput } from "./components/TextInput/TextInput";
import { Select } from "./components/Select/Select";
import { Checkbox } from "./components/Checkbox/Checkbox";
import { Card } from "./components/Card/Card";
import { Modal } from "./components/Modal/Modal";

function Section({ title, children }) {
  return (
    <section style={{ marginBottom: "2rem" }}>
      <Text as="h2" variant="heading-2">{title}</Text>
      <div style={{ marginTop: "0.75rem" }}>{children}</div>
    </section>
  );
}

function Swatch({ label, children }) {
  return (
    <div style={{ marginBottom: "1rem" }}>
      <Text variant="caption" as="div">{label}</Text>
      {children}
    </div>
  );
}

const RAMP_STEPS = [100, 200, 300, 400, 500, 600, 700, 800, 900];
const HUES = ["primary", "neutral", "success", "warning", "danger"];
const SPACE_STEPS = [0, 1, 2, 3, 4, 5, 6, 7, 8];
const RADIUS_STEPS = ["sm", "md", "lg", "full"];
const BORDER_WIDTH_STEPS = ["thin", "default", "thick"];
const SHADOW_STEPS = ["sm", "md", "lg"];

function SpacingRow({ step }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.4rem" }}>
      <Text variant="caption" as="span" style={{ width: "90px" }}>
        --space-{step}
      </Text>
      <div style={{ height: "16px", width: `var(--space-${step})`, background: "var(--color-primary)" }} />
    </div>
  );
}

function RadiusSwatch({ step }) {
  return (
    <div style={{ textAlign: "center", marginRight: "1rem", display: "inline-block" }}>
      <div
        style={{
          width: "56px",
          height: "56px",
          background: "var(--color-surface)",
          border: "1px solid var(--color-border)",
          borderRadius: `var(--radius-${step})`,
        }}
      />
      <Text variant="caption" as="div">radius-{step}</Text>
    </div>
  );
}

function BorderWidthSwatch({ step }) {
  return (
    <div style={{ textAlign: "center", marginRight: "1rem", display: "inline-block" }}>
      <div
        style={{
          width: "56px",
          height: "56px",
          background: "var(--color-background)",
          borderStyle: "solid",
          borderColor: "var(--color-primary)",
          borderWidth: `var(--border-width-${step})`,
        }}
      />
      <Text variant="caption" as="div">border-width-{step}</Text>
    </div>
  );
}

function ShadowSwatch({ step }) {
  return (
    <div style={{ textAlign: "center", marginRight: "1.5rem", display: "inline-block" }}>
      <div
        style={{
          width: "56px",
          height: "56px",
          background: "var(--color-background)",
          borderRadius: "var(--radius-md)",
          boxShadow: `var(--shadow-${step})`,
        }}
      />
      <Text variant="caption" as="div">shadow-{step}</Text>
    </div>
  );
}

function ColorRamp({ hue }) {
  return (
    <div style={{ marginBottom: "1rem" }}>
      <Text variant="caption" as="div">{hue}</Text>
      <div style={{ display: "flex" }}>
        {RAMP_STEPS.map((step) => (
          <div
            key={step}
            style={{
              width: "56px",
              height: "40px",
              background: `var(--color-${hue}-${step})`,
              display: "flex",
              alignItems: "flex-end",
              justifyContent: "center",
            }}
          >
            <Text variant="caption" as="span" style={{ fontSize: "0.625rem", opacity: 0.7 }}>
              {step}
            </Text>
          </div>
        ))}
      </div>
    </div>
  );
}

function SemanticSwatch({ name }) {
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.5rem",
        marginRight: "1.5rem",
        marginBottom: "0.5rem",
      }}
    >
      <div
        style={{
          width: "20px",
          height: "20px",
          borderRadius: "4px",
          border: "1px solid var(--color-border)",
          background: `var(--color-${name})`,
        }}
      />
      <Text variant="caption">--color-{name}</Text>
    </div>
  );
}

export function Library() {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <main style={{ padding: "2rem", maxWidth: "720px" }}>
      <Text as="h1" variant="heading-1">Design System Library</Text>
      <Text variant="body" as="p">
        Every approved foundation and component, organized by layer order.
      </Text>

      <Section title="Typography">
        <Swatch label="heading-1">
          <Text variant="heading-1">The quick brown fox</Text>
        </Swatch>
        <Swatch label="heading-2">
          <Text variant="heading-2">The quick brown fox</Text>
        </Swatch>
        <Swatch label="body">
          <Text variant="body">The quick brown fox jumps over the lazy dog.</Text>
        </Swatch>
        <Swatch label="caption">
          <Text variant="caption">The quick brown fox jumps over the lazy dog.</Text>
        </Swatch>
      </Section>

      <Section title="Color">
        {HUES.map((hue) => (
          <ColorRamp key={hue} hue={hue} />
        ))}
        <Text variant="caption" as="div" style={{ marginBottom: "0.5rem" }}>
          semantic aliases
        </Text>
        <div>
          {[
            "text",
            "text-secondary",
            "background",
            "surface",
            "border",
            "primary",
            "primary-hover",
            "focus-ring",
            "success-text",
            "warning-text",
            "danger-text",
            "success-surface",
            "warning-surface",
            "danger-surface",
          ].map((name) => (
            <SemanticSwatch key={name} name={name} />
          ))}
        </div>
      </Section>

      <Section title="Spacing & foundational tokens">
        <Text variant="caption" as="div" style={{ marginBottom: "0.4rem" }}>spacing scale</Text>
        {SPACE_STEPS.map((step) => (
          <SpacingRow key={step} step={step} />
        ))}

        <Text variant="caption" as="div" style={{ margin: "1rem 0 0.4rem" }}>border radius</Text>
        <div>
          {RADIUS_STEPS.map((step) => (
            <RadiusSwatch key={step} step={step} />
          ))}
        </div>

        <Text variant="caption" as="div" style={{ margin: "1rem 0 0.4rem" }}>border width</Text>
        <div>
          {BORDER_WIDTH_STEPS.map((step) => (
            <BorderWidthSwatch key={step} step={step} />
          ))}
        </div>

        <Text variant="caption" as="div" style={{ margin: "1rem 0 0.4rem" }}>shadow / elevation</Text>
        <div>
          {SHADOW_STEPS.map((step) => (
            <ShadowSwatch key={step} step={step} />
          ))}
        </div>
      </Section>

      <Section title="Small components">
        <Text variant="caption" as="div" style={{ marginBottom: "0.4rem" }}>Button</Text>
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", marginBottom: "1rem" }}>
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="danger">Danger</Button>
          <Button variant="primary" disabled>Disabled</Button>
          <Button variant="primary" loading>Loading</Button>
        </div>

        <Text variant="caption" as="div" style={{ marginBottom: "0.4rem" }}>Badge</Text>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <Badge variant="neutral">Neutral</Badge>
          <Badge variant="success">Success</Badge>
          <Badge variant="warning">Warning</Badge>
          <Badge variant="danger">Danger</Badge>
        </div>
      </Section>

      <Section title="Interactive components">
        <Text variant="caption" as="div" style={{ marginBottom: "0.4rem" }}>Text input</Text>
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginBottom: "1.5rem" }}>
          <TextInput label="Default" placeholder="Type here" />
          <TextInput label="With help text" helpText="We'll never share your email." />
          <TextInput label="Disabled" disabled defaultValue="Can't edit this" />
          <TextInput label="Error" error="This field is required." />
        </div>

        <Text variant="caption" as="div" style={{ marginBottom: "0.4rem" }}>Select</Text>
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginBottom: "1.5rem" }}>
          <Select label="Default" defaultValue="a">
            <option value="a">Option A</option>
            <option value="b">Option B</option>
          </Select>
          <Select label="Error" error="Please choose an option.">
            <option value="">Select one</option>
            <option value="a">Option A</option>
          </Select>
        </div>

        <Text variant="caption" as="div" style={{ marginBottom: "0.4rem" }}>Checkbox</Text>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <Checkbox label="Default" />
          <Checkbox label="Checked" defaultChecked />
          <Checkbox label="Indeterminate" indeterminate />
          <Checkbox label="Disabled" disabled />
        </div>
      </Section>

      <Section title="Composite components">
        <Text variant="caption" as="div" style={{ marginBottom: "0.4rem" }}>Card</Text>
        <div style={{ maxWidth: "320px", marginBottom: "1.5rem" }}>
          <Card
            title="Card title"
            footer={<Button variant="primary">Action</Button>}
          >
            <Text variant="body">
              Card body content goes here, using approved spacing and typography.
            </Text>
          </Card>
        </div>

        <Text variant="caption" as="div" style={{ marginBottom: "0.4rem" }}>Modal / Dialog</Text>
        <Button variant="secondary" onClick={() => setModalOpen(true)}>
          Open modal
        </Button>
        <Modal
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          title="Modal title"
          footer={
            <>
              <Button variant="secondary" onClick={() => setModalOpen(false)}>Cancel</Button>
              <Button variant="primary" onClick={() => setModalOpen(false)}>Confirm</Button>
            </>
          }
        >
          <Text variant="body">
            Built on native &lt;dialog&gt;: focus trap, Escape-to-close, and backdrop-click all work without custom JS.
          </Text>
        </Modal>
      </Section>
    </main>
  );
}
