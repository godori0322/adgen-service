

interface ButtonProps {
  type?: "button" | "submit";
  text: string;
  loading?: boolean;
  disabled?: boolean;
  onClick?: () => void;
}

export default function Button ({
  type="button",
  text,
  loading=false,
  disabled=false,
  onClick,
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`
        w-full text-white font-semibold py-3 rounded-lg transition shadow-md hover:shadow-lg
        ${disabled ? "bg-blue-300 cursor-not-allowed" : "bg-blue-500 hover:bg-blue-600"}
      `}
    >
      {loading ? "처리 중..." : text}
    </button>
  );
}