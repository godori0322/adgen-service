import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useEffect, useState } from "react";

export default function FloatingHubButton() {
  const { isLogin } = useAuth();
  const navigate = useNavigate();

  const [open, setOpen] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [canInstall, setCanInstall] = useState(false);

  // PWA 설치 가능 이벤트 감지
  useEffect(() => {
    const handler = (e: any) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setCanInstall(true);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    await deferredPrompt.useChoice;

    setDeferredPrompt(null);
    setCanInstall(false);
    setOpen(false);
  };

  const FORM_URL =
    "https://docs.google.com/forms/d/e/1FAIpQLSeekZs8uKzFEv4k7Wj3LNVCbwoTQkh9qY-QGPETuE4h1EMqxA/viewform?usp=dialog";

  return (
    <>
      {/* 메뉴 */}
      {open && (
        <div className="fixed bottom-20 right-6 flex flex-col items-end gap-3 z-50">
          {/* 히스토리 (로그인 시만 표시) */}
          {isLogin && (
            <button
              onClick={() => {
                navigate("/history");
                setOpen(false);
              }}
              className="bg-white text-gray-800 px-4 py-2 rounded-full shadow-md border text-sm hover:bg-gray-100"
            >
              🕘 히스토리
            </button>
          )}

          {/* PWA 설치 가능 시 */}
          {canInstall && (
            <button
              onClick={handleInstall}
              className="bg-blue-600 text-white px-4 py-2 rounded-full shadow-md text-sm hover:bg-blue-700"
            >
              📥 앱 설치
            </button>
          )}

          {/* 피드백 */}
          <a
            href={FORM_URL}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => setOpen(false)}
            className="bg-blue-600 text-white px-4 py-2 rounded-full shadow-md text-sm hover:bg-blue-700"
          >
            ✍️ 피드백
          </a>
        </div>
      )}

      {/* 메인 플로팅 버튼 */}
      <button
        onClick={() => setOpen(!open)}
        className="
          fixed bottom-6 right-6 z-50
          w-14 h-14 rounded-full
          flex items-center justify-center
          bg-blue-600 text-white text-2xl font-bold
          shadow-xl hover:bg-blue-700 hover:shadow-2xl
          transition-all duration-200
        "
      >
        {open ? "✕" : "+"}
      </button>
    </>
  );
}
