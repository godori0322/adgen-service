import { useEffect, useState } from "react";

interface Props {
  items: string[];
  editMode: boolean;
  onAdd: (item: string) => void;
  onRemove: (index: number) => void;
}

export default function MenuTagEditor({ items, editMode, onAdd, onRemove }: Props) {
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!editMode) {
      setInput("");
      setError(null);
    }
  }, [editMode]);


  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.nativeEvent.isComposing) return;
    if (e.key !== "Enter") return;

    e.preventDefault();
    const value = input.trim();
    if (!value) return;

    if (items.includes(value)) {
      setError("이미 등록된 메뉴입니다.");
      return;
    }
    setError(null);
    onAdd(value);
    setInput("");
  };
  return (
    <div className="py-2 text-sm">
      {!editMode ? (
        <div className="flex items-center gap-4 h-10">
          <span className="text-gray-600 w-24">메뉴 리스트</span>
          <div className="flex flex-1 flex-wrap gap-2">
            {items.map((item, idx) => (
              <span
                key={idx}
                className="px-4 py-1.5 bg-blue-100 text-blue-700 rounded-full text-sm"
              >
                {item}
              </span>
            ))}
          </div>
        </div>
      ) : (
        <>
          <div className="flex items-center gap-4">
            <span className="text-gray-600 w-24">메뉴 리스트</span>
            <input
              type="text"
              placeholder="메뉴 입력 후 엔터"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg 
            focus:ring-2 focus:ring-blue-400 focus:outline-none"
            />
          </div>
          {error && <p className="text-xs text-red-500 ml-28 mt-1">{error}</p>}
          <div className="flex flex-wrap gap-2 ml-28 mt-2">
            {items.map((item, idx) => (
              <span
                key={idx}
                className="px-4 py-1.5 bg-blue-100 text-blue-700 rounded-full flex items-center gap-1"
              >
                {item}
                <button
                  type="button"
                  onClick={() => onRemove(idx)}
                  className="text-xs text-red-500"
                >
                  ✕
                </button>
              </span>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
