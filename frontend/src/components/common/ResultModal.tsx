// src/components/common/ResultModal.tsx
interface ResultModalProps {
  title: string;
  message: string;
  primaryText: string;
  secondaryText?: string;
  onPrimary: () => void;
  onSecondary?: () => void;
  onClose: () => void; 
}

export default function ResultModal({
  title,
  message,
  primaryText,
  secondaryText,
  onPrimary,
  onSecondary,
  onClose,
}: ResultModalProps) {
  const handleBackgroundClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose();
  };

  return (
    <div
      className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50"
      onClick={handleBackgroundClick}
    >
      <div className="bg-white rounded-2xl shadow-xl p-6 w-[90%] max-w-sm text-center animate-fadeIn relative">
        {/* X 닫기 버튼 */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-400 hover:text-gray-600 transition"
        >
          ✕
        </button>

        <h3 className="text-lg font-bold text-gray-900 mb-3">{title}</h3>
        <p className="text-gray-600 whitespace-pre-line mb-6">{message}</p>

        <div className="space-y-2">
          <button
            onClick={onPrimary}
            className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 font-semibold"
          >
            {primaryText}
          </button>

          {secondaryText && (
            <button
              onClick={onSecondary}
              className="w-full bg-gray-200 text-gray-800 py-2 rounded-lg hover:bg-gray-300"
            >
              {secondaryText}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
