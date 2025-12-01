import { useState, useEffect } from "react";

export default function InstallPwaButton() {
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const isStandalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      (window.navigator as any).standalone === true;
    if (isStandalone) return;

    const handler = (e: any) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setIsVisible(true);
    };

    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  const handleInstallClick = async () => {
    if (!deferredPrompt) return;

    await deferredPrompt.prompt();
    await deferredPrompt.userChoice;

    setDeferredPrompt(null);
    setIsVisible(false);
  };

  if (!isVisible) return null;

  return (
    <button
      onClick={handleInstallClick}
      className="
        fixed bottom-24 right-6 z-50
        flex items-center gap-2
        px-4 py-2 rounded-full
        bg-blue-600 text-white text-sm font-medium
        shadow-lg
        hover:bg-blue-700 hover:shadow-xl
        transition-transform duration-200
        hover:-translate-y-0.5
      "
    >
      📥 앱 설치
    </button>
  );
}
