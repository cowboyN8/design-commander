// Older card implementation, still used on 3 screens that predate Card.jsx.
// Higher usage count than Card.jsx, but it's the one that should be
// considered legacy -- frequency is not the same as precedent.
export function OldCard({ heading, children }) {
  return (
    <table style={{ width: "100%", border: "2px groove gray" }}>
      <tbody>
        {heading && (
          <tr>
            <td><b>{heading}</b></td>
          </tr>
        )}
        <tr>
          <td>{children}</td>
        </tr>
      </tbody>
    </table>
  );
}
