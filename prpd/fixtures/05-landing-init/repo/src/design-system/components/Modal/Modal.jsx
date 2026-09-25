import { useEffect, useId, useRef } from "react";
import styles from "./Modal.module.css";
import { Text } from "../Text/Text";

/**
 * Built on the native <dialog> element so focus trapping, background
 * inerting, top-layer rendering, and Escape-to-close come from the browser
 * instead of a reimplemented focus trap.
 */
export function Modal({ open, onClose, title, children, footer }) {
  const ref = useRef(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    const handleClose = () => onClose?.();
    dialog.addEventListener("close", handleClose);
    return () => dialog.removeEventListener("close", handleClose);
  }, [onClose]);

  const handleBackdropClick = (event) => {
    if (event.target === ref.current) {
      onClose?.();
    }
  };

  return (
    <dialog
      ref={ref}
      className={styles.dialog}
      aria-labelledby={title ? titleId : undefined}
      onClick={handleBackdropClick}
      onCancel={onClose}
    >
      {title && (
        <div className={styles.header}>
          <Text as="h2" variant="heading-2" id={titleId}>{title}</Text>
        </div>
      )}
      {children}
      {footer && <div className={styles.footer}>{footer}</div>}
    </dialog>
  );
}
