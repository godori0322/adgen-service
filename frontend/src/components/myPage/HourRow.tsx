import TimePicker from "../common/TimePicker";

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
          <div className="flex-1">
            <TimePicker
              label="오픈시간"
              value={openTime}
              onChange={(v) => onChange("openTime", v)}
            />
          </div>

          <div className="flex-1">
            <TimePicker
              label="마감시간"
              value={closeTime}
              onChange={(v) => onChange("closeTime", v)}
            />
          </div>
        </>
      ) : (
        <span className="font-medium flex-1">
          {openTime} ~ {closeTime}
        </span>
      )}
    </div>
  );
}
