import styles from "./Card.module.css";
import { Text } from "../Text/Text";

export function Card({ title, footer, children, className = "", ...rest }) {
  return (
    <div className={[styles.card, className].filter(Boolean).join(" ")} {...rest}>
      {title && (
        <div className={styles.header}>
          <Text as="h3" variant="heading-2">{title}</Text>
        </div>
      )}
      {children}
      {footer && <div className={styles.footer}>{footer}</div>}
    </div>
  );
}
