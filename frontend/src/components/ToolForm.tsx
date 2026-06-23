import { useState } from "react";
import type { FieldSpec, ToolSpec } from "../types";

export type FormValues = Record<string, unknown>;

export function initialValues(spec: ToolSpec): FormValues {
  const values: FormValues = {};
  for (const field of spec.fields) {
    if (field.type === "bool") {
      values[field.key] = field.default === true;
    } else if (field.default !== null && field.default !== undefined) {
      values[field.key] = String(field.default);
    } else {
      values[field.key] = "";
    }
  }
  return values;
}

interface ToolFormProps {
  spec: ToolSpec;
  values: FormValues;
  onChange: (key: string, value: unknown) => void;
}

function Field({
  field,
  value,
  onChange,
}: {
  field: FieldSpec;
  value: unknown;
  onChange: (value: unknown) => void;
}) {
  const inputClass =
    "w-full rounded-md border border-arango-border bg-white px-3 py-2 text-sm text-arango-text outline-none focus:border-arango-green focus:ring-1 focus:ring-arango-green";

  if (field.type === "bool") {
    return (
      <label className="flex items-center gap-2 py-1">
        <input
          type="checkbox"
          checked={Boolean(value)}
          onChange={(e) => onChange(e.target.checked)}
          className="h-4 w-4 accent-arango-green"
        />
        <span className="text-sm text-arango-text">{field.label}</span>
        {field.help && <span className="text-xs text-arango-muted">— {field.help}</span>}
      </label>
    );
  }

  const label = (
    <label className="mb-1 block text-sm font-medium text-arango-text" htmlFor={field.key}>
      {field.label}
      {field.required && <span className="ml-1 text-arango-error">*</span>}
    </label>
  );

  let control;
  if (field.type === "enum") {
    control = (
      <select
        id={field.key}
        className={inputClass}
        value={String(value ?? "")}
        onChange={(e) => onChange(e.target.value)}
      >
        {field.options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    );
  } else if (field.type === "text") {
    control = (
      <textarea
        id={field.key}
        rows={3}
        className={`${inputClass} font-mono`}
        value={String(value ?? "")}
        placeholder={field.placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    );
  } else {
    control = (
      <input
        id={field.key}
        type={field.type === "int" ? "number" : "text"}
        className={inputClass}
        value={String(value ?? "")}
        placeholder={field.placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    );
  }

  return (
    <div>
      {label}
      {control}
      {field.help && <p className="mt-1 text-xs text-arango-muted">{field.help}</p>}
    </div>
  );
}

export default function ToolForm({ spec, values, onChange }: ToolFormProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const common = spec.fields.filter((f) => f.group === "Common");
  const advanced = spec.fields.filter((f) => f.group === "Advanced");

  return (
    <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {common.map((field) => (
          <div key={field.key} className={field.type === "text" ? "md:col-span-2" : ""}>
            <Field field={field} value={values[field.key]} onChange={(v) => onChange(field.key, v)} />
          </div>
        ))}
      </div>

      {advanced.length > 0 && (
        <div className="rounded-md border border-arango-border">
          <button
            type="button"
            onClick={() => setShowAdvanced((s) => !s)}
            className="flex w-full items-center justify-between px-4 py-2 text-sm font-medium text-arango-text"
          >
            <span>Advanced</span>
            <span className="text-arango-muted">{showAdvanced ? "−" : "+"}</span>
          </button>
          {showAdvanced && (
            <div className="grid grid-cols-1 gap-4 border-t border-arango-border p-4 md:grid-cols-2">
              {advanced.map((field) => (
                <div key={field.key} className={field.type === "text" ? "md:col-span-2" : ""}>
                  <Field
                    field={field}
                    value={values[field.key]}
                    onChange={(v) => onChange(field.key, v)}
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </form>
  );
}
