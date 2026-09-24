import styles from "./Button.module.css";

/**
 * Reconciled against Figma "Design System v2": renamed from the old "kind"
 * prop to "variant" and added the missing "danger" variant. Always renders a
 * native <button> so keyboard activation, focus, and disabled behavior come
 * from the platform instead of being reimplemented.
 */
export function Button({ variant = "primary", disabled = false, className = "", children, ...rest }) {
  const variantClass = styles[variant] || styles.primary;
  return (
    <button
      className={[styles.button, variantClass, className].filter(Boolean).join(" ")}
      disabled={disabled}
      {...rest}
    >
      {children}
    </button>
  );
}
