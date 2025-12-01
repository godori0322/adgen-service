import { RgbColorPicker } from "react-colorful";
// import "react-colorful/dist/index.css";

export default function ColorSelector({
  color,
  onChange,
}: {
  color: { r: number; g: number; b: number };
  onChange: (c: { r: number; g: number; b: number }) => void;
}) {
  return (
    <div className="bg-white p-3 rounded-xl shadow flex flex-col items-center gap-3 border border-gray-100">
      <RgbColorPicker color={color} onChange={onChange} />
      <div className="">
        선택된 RGB:{" "}
        <span className="font-semibold">
          {color.r}, {color.g}, {color.b}
        </span>
        <div
          className="w-6 h-6 rounded border shadow inline-block ml-2"
          style={{ backgroundColor: `rgb(${color.r}, ${color.g}, ${color.b})` }}
        />
      </div>
    </div>
  );
}
