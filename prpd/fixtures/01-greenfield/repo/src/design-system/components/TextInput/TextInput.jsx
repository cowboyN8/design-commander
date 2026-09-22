import { useId } from "react";
import fieldStyles from "../Field/Field.module.css";
import { Text } from "../Text/Text";

export function TextInput({ id, label, helpText, error, disabled, className = "", ...rest }) {
  const generatedId = useId();
  const inputId = id || generatedId;
  const helpId = helpText ? `${inputId}-help` : undefined;
  const errorId = error ? `${inputId}-error` : undefined;
  const describedBy = [helpId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div className={[fieldStyles.field, className].filter(Boolean).join(" ")}>
      <label className={fieldStyles.label} htmlFor={inputId}>
        {label}
      </label>
      <input
        id={inputId}
        className={[fieldStyles.input, error && fieldStyles.invalid].filter(Boolean).join(" ")}
        disabled={disabled}
        aria-invalid={error ? "true" : undefined}
        aria-describedby={describedBy}
        {...rest}
      />
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
