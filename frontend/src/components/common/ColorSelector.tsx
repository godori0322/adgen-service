import { RgbColorPicker } from "react-colorful";

export default function ColorSelector({
  color,
  onChange,
}: {
  color: { r: number; g: number; b: number };
  onChange: (c: { r: number; g: number; b: number }) => void;
}) {
  return (
    <div className="bg-white p-3 rounded-xl shadow flex flex-col items-center gap-3 border border-gray-100 w-full sm:w-auto">
      <div className="w-full max-w-[280px] sm:max-w-none">
        <RgbColorPicker color={color} onChange={onChange} />
      </div>

      <div className="text-center sm:text-left text-sm">
        선택된 RGB:{" "}
        <span className="font-semibold">
          {color.r}, {color.g}, {color.b}
        </span>
        <div
          className="w-5 h-5 rounded border shadow inline-block ml-2 align-middle"
          style={{ backgroundColor: `rgb(${color.r}, ${color.g}, ${color.b})` }}
        />
      </div>
    </div>
  );
}
