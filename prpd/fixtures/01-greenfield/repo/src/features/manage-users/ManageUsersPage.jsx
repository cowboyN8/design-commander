import { useEffect, useState } from "react";
import { Text } from "../../design-system/components/Text/Text";
import { Table } from "../../design-system/components/Table/Table";
import { Badge } from "../../design-system/components/Badge/Badge";
import { Select } from "../../design-system/components/Select/Select";
import { Checkbox } from "../../design-system/components/Checkbox/Checkbox";

const MOCK_USERS = [
  { id: 1, name: "Ada Lovelace", email: "ada@example.com", role: "Admin", status: "active" },
  { id: 2, name: "Grace Hopper", email: "grace@example.com", role: "Member", status: "invited" },
  { id: 3, name: "Alan Turing", email: "alan@example.com", role: "Member", status: "disabled" },
];

const STATUS_VARIANT = { active: "success", invited: "warning", disabled: "neutral" };

const COLUMNS = [
  { key: "name", label: "Name", sortable: true },
  { key: "email", label: "Email" },
  { key: "role", label: "Role", sortable: true },
  { key: "status", label: "Status" },
];

export function ManageUsersPage() {
  const [viewAsRole, setViewAsRole] = useState("admin");
  const [forceError, setForceError] = useState(false);
  const [forceEmpty, setForceEmpty] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [users, setUsers] = useState([]);
  const [sort, setSort] = useState({ key: "name", direction: "ascending" });

  function load() {
    setLoading(true);
    setError(null);
    setTimeout(() => {
      if (forceError) {
        setError("Couldn't load users.");
      } else {
        setUsers(forceEmpty ? [] : MOCK_USERS);
      }
      setLoading(false);
    }, 400);
  }

  useEffect(load, [forceError, forceEmpty]);

  function handleSort(key) {
    setSort((prev) =>
      prev.key === key
        ? { key, direction: prev.direction === "ascending" ? "descending" : "ascending" }
        : { key, direction: "ascending" }
    );
  }

  const rows = [...users]
    .sort((a, b) => {
      const dir = sort.direction === "ascending" ? 1 : -1;
      return a[sort.key] > b[sort.key] ? dir : a[sort.key] < b[sort.key] ? -dir : 0;
    })
    .map((u) => ({
      ...u,
      status: <Badge variant={STATUS_VARIANT[u.status] || "neutral"}>{u.status}</Badge>,
    }));

  if (viewAsRole !== "admin") {
    return (
      <main style={{ padding: "2rem" }}>
        <Text as="h1" variant="heading-1">403</Text>
        <Text variant="body" as="p">You don't have permission to view this page.</Text>
        <DevControls
          viewAsRole={viewAsRole}
          setViewAsRole={setViewAsRole}
          forceError={forceError}
          setForceError={setForceError}
          forceEmpty={forceEmpty}
          setForceEmpty={setForceEmpty}
        />
      </main>
    );
  }

  return (
    <main style={{ padding: "2rem", maxWidth: "720px" }}>
      <Text as="h1" variant="heading-1">Manage users</Text>

      <Table
        columns={COLUMNS}
        rows={rows}
        sort={sort}
        onSort={handleSort}
        loading={loading}
        error={error}
        onRetry={load}
        emptyMessage="No users yet."
      />

      <DevControls
        viewAsRole={viewAsRole}
        setViewAsRole={setViewAsRole}
        forceError={forceError}
        setForceError={setForceError}
        forceEmpty={forceEmpty}
        setForceEmpty={setForceEmpty}
      />
    </main>
  );
}

function DevControls({ viewAsRole, setViewAsRole, forceError, setForceError, forceEmpty, setForceEmpty }) {
  return (
    <div style={{ marginTop: "2rem", borderTop: "var(--border-width-thin) solid var(--color-border)", paddingTop: "1rem" }}>
      <Text variant="caption" as="div" style={{ marginBottom: "0.5rem" }}>
        Fixture demo controls (not part of the shipped feature)
      </Text>
      <Select label="View as" value={viewAsRole} onChange={(e) => setViewAsRole(e.target.value)}>
        <option value="admin">Admin</option>
        <option value="member">Member</option>
      </Select>
      <Checkbox
        label="Simulate load error"
        checked={forceError}
        onChange={(e) => setForceError(e.target.checked)}
      />
      <Checkbox
        label="Simulate empty list"
        checked={forceEmpty}
        onChange={(e) => setForceEmpty(e.target.checked)}
      />
    </div>
  );
}
