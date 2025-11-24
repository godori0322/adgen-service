import { useState } from "react";

interface TimePickerProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
}

export default function TimePicker({label, value, onChange}: TimePickerProps) {
  const [open, setOpen] = useState(false);

  const [hour, minute] = value.split(":").map(Number);
  const [tempHour, setTempHour] = useState(hour || 9);
  const [tempMinute, setTempMinute] = useState(minute || 0);

  const hours = Array.from({ length: 24 }, (_, i) => i);
  const minutes = [0, 10, 20, 30, 40, 50];

  const handleConfirm = () => {
    const hh = String(tempHour).padStart(2, "0");
    const mm = String(tempMinute).padStart(2, "0");
    onChange(`${hh}:${mm}`);
    setOpen(false);
  };

  return (
    <div className="w-full">
      <label className="text-sm font-medium text-gray-600">{label}</label>

      <button
        onClick={() => setOpen(true)}
        className="w-full mt-1 px-3 py-2 border rounded-lg text-left bg-white"
      >
        {value || "시간 선택"}
      </button>

      {open && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-end justify-center z-50">
          <div className="bg-white w-full rounded-t-2xl p-6 pb-8 animate-slide-up">
            <h3 className="text-lg font-semibold mb-4 text-center">시간 선택</h3>

            <div className="flex justify-center gap-6 h-40 items-center">
              {/* Hours */}
              <div className="overflow-y-scroll h-full snap-y snap-mandatory scrollbar-hide">
                {hours.map((h) => (
                  <div
                    key={h}
                    onClick={() => setTempHour(h)}
                    className={`text-xl py-2 text-center cursor-pointer snap-start ${
                      tempHour === h ? "text-blue-600 font-bold" : "text-gray-400"
                    }`}
                  >
                    {String(h).padStart(2, "0")}
                  </div>
                ))}
              </div>

              <span className="text-xl">:</span>

              {/* Minutes */}
              <div className="overflow-y-scroll h-full snap-y snap-mandatory scrollbar-hide">
                {minutes.map((m) => (
                  <div
                    key={m}
                    onClick={() => setTempMinute(m)}
                    className={`text-xl py-2 text-center cursor-pointer snap-start ${
                      tempMinute === m ? "text-blue-600 font-bold" : "text-gray-400"
                    }`}
                  >
                    {String(m).padStart(2, "0")}
                  </div>
                ))}
              </div>
            </div>

            {/* Buttons */}
            <div className="flex justify-between mt-6">
              <button onClick={() => setOpen(false)} className="px-4 py-2 rounded-lg bg-gray-200">
                취소
              </button>
              <button
                onClick={handleConfirm}
                className="px-4 py-2 rounded-lg bg-blue-600 text-white"
              >
                확인
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}