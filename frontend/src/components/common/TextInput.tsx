

interface TextInputProps {
  id: string;
  label: string;
  type?: string;
  value: string;
  placeholder?: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: () => void;
  error?: string| null;
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
}: TextInputProps) {
  return (
    <div className="mb-3">
      <label htmlFor={id} className="block text-sm font-medium text-gray-600 mb-1">
        {label}
      </label>
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
      ) : (
        <p className="mt-1 text-xs min-h-[20px]">&nbsp;</p> 
      )}
    </div>
  );
}