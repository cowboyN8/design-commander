import styles from "./Button.module.css";

/**
 * Always renders a native <button> so keyboard activation, focus, and
 * disabled behavior come from the platform instead of being reimplemented.
 */
export function Button({
  variant = "primary",
  loading = false,
  disabled = false,
  className = "",
  children,
  ...rest
}) {
  const variantClass = styles[variant] || styles.primary;
  return (
    <button
      className={[styles.button, variantClass, className].filter(Boolean).join(" ")}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading && <span className={styles.spinner} aria-hidden="true" />}
      {children}
    </button>
  );
}
