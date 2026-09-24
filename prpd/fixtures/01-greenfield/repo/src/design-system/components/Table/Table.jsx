import styles from "./Table.module.css";
import { Button } from "../Button/Button";

/**
 * Generic tabular data primitive. Renders a native <table> so row/column
 * semantics, keyboard navigation, and screen-reader table announcements come
 * from the platform rather than a reimplemented ARIA grid. Callers compose
 * cell content themselves (e.g. a Badge for a status column) — Table has no
 * opinion about what a column means.
 *
 * columns: [{ key, label, sortable }]
 * rows: array of plain objects; row[column.key] is rendered per cell
 * sort: { key, direction: "ascending" | "descending" } | undefined
 * onSort(key): called when a sortable header is activated
 * loading: shows skeleton rows instead of data
 * error: string | undefined — shows a retry banner instead of the table body
 * onRetry: called when the error banner's retry button is pressed
 * emptyMessage: shown when rows is empty and not loading/error
 */
export function Table({
  columns,
  rows,
  sort,
  onSort,
  loading = false,
  error,
  onRetry,
  emptyMessage = "No data to display.",
  className = "",
  ...rest
}) {
  if (error) {
    return (
      <div className={styles.errorBanner} role="alert">
        <span>{error}</span>
        {onRetry && (
          <Button variant="secondary" onClick={onRetry}>
            Retry
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className={styles.wrapper}>
      <table
        className={[styles.table, className].filter(Boolean).join(" ")}
        aria-busy={loading || undefined}
        {...rest}
      >
        <thead>
          <tr>
            {columns.map((col) => {
              const isSorted = sort?.key === col.key;
              const ariaSort = col.sortable ? (isSorted ? sort.direction : "none") : undefined;
              return (
                <th key={col.key} scope="col" aria-sort={ariaSort}>
                  {col.sortable ? (
                    <button
                      type="button"
                      className={styles.sortButton}
                      onClick={() => onSort?.(col.key)}
                    >
                      {col.label}
                      <span aria-hidden="true" className={styles.sortIndicator}>
                        {isSorted ? (sort.direction === "ascending" ? "\u25B2" : "\u25BC") : ""}
                      </span>
                    </button>
                  ) : (
                    col.label
                  )}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <tr key={i} className={styles.skeletonRow}>
                {columns.map((col) => (
                  <td key={col.key}>
                    <span className={styles.skeleton} />
                  </td>
                ))}
              </tr>
            ))
          ) : rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className={styles.emptyCell}>
                {emptyMessage}
              </td>
            </tr>
          ) : (
            rows.map((row, i) => (
              <tr key={row.id ?? i} className={styles.row}>
                {columns.map((col) => (
                  <td key={col.key} data-label={col.label}>
                    {row[col.key]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
