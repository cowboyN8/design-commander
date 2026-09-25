import styles from "./Badge.module.css";

/**
 * Status label. Always requires a text label so status is never communicated
 * by color alone — do not use this for icon-only or color-only indicators.
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
