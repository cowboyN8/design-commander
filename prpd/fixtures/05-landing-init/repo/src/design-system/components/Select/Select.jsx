import { useId } from "react";
import fieldStyles from "../Field/Field.module.css";
import { Text } from "../Text/Text";

export function Select({ id, label, helpText, error, disabled, children, className = "", ...rest }) {
  const generatedId = useId();
  const selectId = id || generatedId;
  const helpId = helpText ? `${selectId}-help` : undefined;
  const errorId = error ? `${selectId}-error` : undefined;
  const describedBy = [helpId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div className={[fieldStyles.field, className].filter(Boolean).join(" ")}>
      <label className={fieldStyles.label} htmlFor={selectId}>
        {label}
      </label>
      <select
        id={selectId}
        className={[fieldStyles.select, error && fieldStyles.invalid].filter(Boolean).join(" ")}
        disabled={disabled}
        aria-invalid={error ? "true" : undefined}
        aria-describedby={describedBy}
        {...rest}
      >
        {children}
      </select>
      {helpText && (
        <Text variant="caption" as="span" id={helpId} className={fieldStyles.helpText}>
          {helpText}
        </Text>
      )}
      {error && (
        <Text variant="caption" as="span" id={errorId} className={fieldStyles.errorText}>
          {error}
        </Text>
      )}
    </div>
  );
}
