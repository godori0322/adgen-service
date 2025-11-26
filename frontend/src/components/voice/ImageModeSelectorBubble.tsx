export type ImageMode = "rigid" | "balanced" | "creative";

const MODE_OPTIONS: { key: ImageMode; title: string; desc: string; color: string }[] = [
  {
    key: "rigid",
    title: "원본 유지 (Rigid)",
    desc: "제품 모양/각도/배치를 거의 변경하지 않고 안정적으로 합성해요.",
    color: "bg-blue-500",
  },
  {
    key: "balanced",
    title: "균형 변경 (Balanced)",
    desc: "구조는 유지하면서 색감·밝기·배경 정도만 자연스럽게 바꿔요.",
    color: "bg-green-500",
  },
  {
    key: "creative",
    title: "창의적 변경 (Creative)",
    desc: "광고 느낌으로 배경·분위기를 크게 바꾸는 모드예요.",
    color: "bg-orange-500",
  },
];

export default function ImageModeSelectorBubble({
  onSelect,
}: {
  onSelect: (mode: ImageMode) => void;
}) {
  return (
    <div className="flex flex-col gap-2 mt-3">
      {MODE_OPTIONS.map((option) => (
        <button
          key={option.key}
          onClick={() => onSelect(option.key)}
          className={`p-3 rounded-xl text-white text-left shadow-sm hover:opacity-90 transition ${option.color}`}
        >
          <p className="font-bold">{option.title}</p>
          <p className="text-sm opacity-80">{option.desc}</p>
        </button>
      ))}
    </div>
  );
}
