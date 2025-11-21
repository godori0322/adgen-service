interface ProfileRowProps {
  label: string;
  value: string;
  editMode: boolean;
  onChange?: (value: string) => void;
  onKeyDown?: (value: string) => void;
}

export default function ProfileRow({ label, value, editMode, onChange }: ProfileRowProps) {
  return (
    <div className="flex justify-between items-center py-2 text-sm h-54">
      {/* 왼쪽 라벨 */}
      <span className="text-gray-600 w-24">{label}</span>

      {/* 오른쪽 값 or input */}
      {editMode ? (
        <input
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          className="
            flex-1 ml-4 px-3 py-2 border border-gray-300 rounded-lg 
            focus:ring-2 focus:ring-blue-400 focus:outline-none
          "
        />
      ) : (
        <span className="font-medium flex-1 ml-4">{value}</span>
      )}
    </div>
  );
}
