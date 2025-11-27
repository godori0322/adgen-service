interface TextInputProps {
  id: string;
  label?: string;
  type?: string;
  value: string;
  placeholder?: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: () => void;
  error?: string | null;
  size?: "normal" | "small";
  empty?: boolean;
}

export default function TextInput({
  id,
  label,
  type = "text",
  value,
  placeholder,
  onChange,
  onBlur,
  error,
  size = "normal",
  empty = true,
}: TextInputProps) {
  const sizeClass = size === "small" ? "px-3 py-2 text-sm" : "px-4 py-3 text-base";
  return (
    <div className="mb-3">
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-gray-600 mb-1">
          {label}
        </label>
      )}
      <input
        id={id}
        name={id}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        aria-invalid={!!error}
        aria-describedby={`${id}-error`}
        className={`
                w-full px-4 py-3 rounded-lg border
                ${sizeClass} 
                ${
                  error
                    ? "border-red-500 focus:ring-red-400"
                    : "border-gray-300 focus:ring-blue-400"
                }
                focus:outline-none focus:ring-2 transition-all
              `}
      />
      {error ? (
        <p id={`${id}-error`} className="mt-1 text-xs text-red-600 min-h-[20px]">
          {error}
        </p>
      ) : empty ? (
        <p className="mt-1 text-xs min-h-[20px]">&nbsp;</p>
      ) : (
        <></>
      )}
    </div>
  );
}
