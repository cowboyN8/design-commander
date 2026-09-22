import styles from "../../tokens/typography.module.css";

const DEFAULT_TAG = {
  "heading-1": "h1",
  "heading-2": "h2",
  body: "p",
  caption: "span",
};

/**
 * Renders text using one of the approved typography roles.
 * Always route heading/body/caption text through this component instead of
 * ad hoc font-size/weight styling, so typography stays traceable to the
 * approved design-system baseline.
 */
export function Text({ variant = "body", as, className = "", children, ...rest }) {
  const Tag = as || DEFAULT_TAG[variant] || "p";
  const roleClass = styles[variant] || styles.body;
  return (
    <Tag className={[roleClass, className].filter(Boolean).join(" ")} {...rest}>
      {children}
    </Tag>
  );
}
