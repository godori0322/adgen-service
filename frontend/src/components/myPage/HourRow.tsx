
interface ProfileRowProps {
  label: string;
  openTime: string;
  closeTime: string;
  editMode: boolean;
  onChange: (key: "openTime" | "closeTime", value: string) => void;
}

export default function HourRow({ label, openTime, closeTime, editMode, onChange }: ProfileRowProps) {
  return (
    <div className="flex justify-between items-center py-2 text-sm h-54 gap-4">
      <span className="text-gray-600 w-24">{label}</span>
      {editMode ? (
        <>
          <input
            type="time"
            value={openTime}
            onChange={(e) => onChange("openTime", e.target.value)}
            onClick={(e) => (e.target as HTMLInputElement).showPicker()}
            step="60"
            pattern="[0-9{2}:[0-9]{2}"
            className="flex-1 mt-1 px-3 py-2 border rounded-lg"
          />
          <span>~</span>
          <input
            type="time"
            value={closeTime}
            onChange={(e) => onChange("closeTime", e.target.value)}
            onClick={(e) => (e.target as HTMLInputElement).showPicker()}
            step="60"
            pattern="[0-9{2}:[0-9]{2}"
            className="flex-1 mt-1 px-3 py-2 border rounded-lg"
          />
        </>
      ) : (
        <span className="font-medium flex-1">
          {openTime} ~ {closeTime}
        </span>
      )}
    </div>
  );
}
