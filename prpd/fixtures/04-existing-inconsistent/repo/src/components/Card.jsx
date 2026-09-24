// Newer card, used on the two most recently built screens.
export function Card({ title, children }) {
  return (
    <div style={{ border: "1px solid #ddd", borderRadius: "8px", padding: "16px" }}>
      {title && <h3>{title}</h3>}
      {children}
    </div>
  );
}
