export default function FloatingButton() {
  const FORM_URL =
    "https://docs.google.com/forms/d/e/1FAIpQLSeekZs8uKzFEv4k7Wj3LNVCbwoTQkh9qY-QGPETuE4h1EMqxA/viewform?usp=dialog"; 

  return (
    <a
      href={FORM_URL}
      target="_blank"
      rel="noopener noreferrer"
      className="
        fixed bottom-6 right-6 z-50
        flex items-center gap-2
        px-4 py-2 rounded-full
        bg-blue-600 text-white text-sm font-medium
        shadow-lg
        hover:bg-blue-700 hover:shadow-xl
        transition-transform duration-200
        hover:-translate-y-0.5
      "
    >
      ✍️ 피드백 남기기
    </a>
  );
}
