import { Button } from "./components/Button.jsx";
import { Card } from "./components/Card.jsx";
import { OldCard } from "./legacy/OldCard.jsx";

// Existing app: mixes the newer Card (2 usages, most recent screens) with the
// older OldCard (3 usages across the rest of the app) and the pre-design-system
// Button (kind prop, hardcoded colors).
export default function App() {
  return (
    <main style={{ padding: "24px" }}>
      <Card title="Newest screen">
        <Button variant="primary">Save</Button>
        <Button variant="secondary">Cancel</Button>
      </Card>

      <OldCard heading="Dashboard widget 1">Legacy widget content</OldCard>
      <OldCard heading="Dashboard widget 2">Legacy widget content</OldCard>
      <OldCard heading="Dashboard widget 3">Legacy widget content</OldCard>
    </main>
  );
}
