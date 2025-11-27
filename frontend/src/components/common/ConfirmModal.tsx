interface ConfirmModalProps {
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmModal({
  title = "확인",
  message,
  confirmText = "확인",
  cancelText = "취소",
  onConfirm,
  onCancel,
}: ConfirmModalProps) {
  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-lg p-6 w-[90%] max-w-sm text-center animate-fadeIn">
        {title && <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>}
        <p className="text-gray-600 whitespace-pre-line">{message}</p>

        <div className="mt-6 flex gap-3 justify-center">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-xl bg-gray-200 hover:bg-gray-300 text-gray-700"
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 rounded-xl bg-blue-600 text-white hover:bg-blue-700"
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
