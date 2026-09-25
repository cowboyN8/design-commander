import { useEffect, useId, useRef } from "react";
import styles from "./Checkbox.module.css";

/**
 * `indeterminate` is a DOM property, not an HTML attribute, so it has to be
 * set imperatively via a ref rather than passed as JSX.
 */
export function Checkbox({ id, label, indeterminate = false, disabled, className = "", ...rest }) {
  const generatedId = useId();
  const checkboxId = id || generatedId;
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.indeterminate = indeterminate;
    }
  }, [indeterminate]);

  return (
    <div className={[styles.wrapper, className].filter(Boolean).join(" ")}>
      <input
        ref={ref}
        type="checkbox"
        id={checkboxId}
        className={styles.checkbox}
        disabled={disabled}
        {...rest}
      />
      <label className={styles.label} htmlFor={checkboxId}>
        {label}
      </label>
    </div>
  );
}
