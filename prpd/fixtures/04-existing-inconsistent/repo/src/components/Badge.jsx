import styles from "./Badge.module.css";

/**
 * New component, built from the Figma "Design System v2" spec (no prior code
 * to reconcile against). Always requires a text label so status is never
 * communicated by color alone.
 */
export function Badge({ variant = "neutral", className = "", children, ...rest }) {
  if (import.meta.env.DEV && !children) {
    console.warn("Badge: a text label is required; status must not be conveyed by color alone.");
  }
  const variantClass = styles[variant] || styles.neutral;
  return (
    <span className={[styles.badge, variantClass, className].filter(Boolean).join(" ")} {...rest}>
      {children}
    </span>
  );
}
