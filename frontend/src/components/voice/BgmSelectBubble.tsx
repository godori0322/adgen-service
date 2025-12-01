import { useState } from "react";

type BgmOption = "video" | "image" | "separate";

export default function BgmSelectBubble({ onSelect }: { onSelect: (option: BgmOption) => void }) {
  const [selected, setSelected] = useState<BgmOption | null>(null);

  const handleClick = (opt: BgmOption) => {
    if (selected) return; // 이미 선택하면 무시
    setSelected(opt);
    onSelect(opt);
  };

  const baseBtn =
    "w-full text-center px-4 py-3 rounded-xl text-white shadow-md transition font-semibold";

  const disabledClass = "opacity-40 cursor-not-allowed pointer-events-none"; // 🔥 hover도 완전 차단

  return (
    <div className="flex flex-col gap-2 mt-3">
      {/* 🎬 동영상 */}
      <button
        onClick={() => handleClick("video")}
        className={`${baseBtn}
          ${selected === "video" ? "bg-blue-700 ring-4 ring-yellow-300" : "bg-blue-500"}
          ${selected && selected !== "video" ? disabledClass : ""}
        `}
      >
        🎬 동영상(릴스)으로
      </button>

      {/* 🖼️ 이미지만 */}
      <button
        onClick={() => handleClick("image")}
        className={`${baseBtn}
          ${selected === "image" ? "bg-orange-600 ring-4 ring-yellow-300" : "bg-orange-500"}
          ${selected && selected !== "image" ? disabledClass : ""}
        `}
      >
        🖼️ 이미지만
      </button>

      {/* 🎨 + 🎵 따로 생성 */}
      <button
        onClick={() => handleClick("separate")}
        className={`${baseBtn}
          ${selected === "separate" ? "bg-purple-700 ring-4 ring-yellow-300" : "bg-purple-500"}
          ${selected && selected !== "separate" ? disabledClass : ""}
        `}
      >
        🎨 + 🎵 이미지+음원(따로)
      </button>
    </div>
  );
}
