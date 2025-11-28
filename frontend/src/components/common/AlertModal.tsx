interface AlertModalProps {
  title?: string;
  message: string;
  buttonText?: string;
  onClose: () => void;
}

export default function AlertModal({
  title,
  message,
  buttonText = "확인",
  onClose,
}: AlertModalProps) {
  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl p-6 w-[90%] max-w-xs text-center animate-fadeIn">
        {title && <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>}

        <p className="text-gray-600 whitespace-pre-line">{message}</p>

        <button
          onClick={onClose}
          className="px-6 py-2 mt-5 rounded-xl bg-blue-600 text-white hover:bg-blue-700"
        >
          {buttonText}
        </button>
      </div>
    </div>
  );
}
