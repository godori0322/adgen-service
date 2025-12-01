import { useState } from "react";
import AlertModal from "./AlertModal";


interface ShareImageButtonProps {
  imageUrl: string;
}

export default function ShareImageButton({ imageUrl }: ShareImageButtonProps) {
  const [isSharing, setIsSharing] = useState(false);
  const [alertMessage, setAlertMessage] = useState<string | null>(null);

  const handleShare = async () => {
    try {
      setIsSharing(true);

      const res = await fetch(imageUrl);
      const blob = await res.blob();
      const file = new File([blob], "adgen-result.png", { type: blob.type });

      const shareData = { files: [file] };

      if (navigator.share && navigator.canShare && navigator.canShare(shareData)) {
        await navigator.share(shareData);
      } else {
        setAlertMessage(
          `📱 공유 기능이 지원되지 않는 환경입니다.\n이미지를 다운로드하여 직접 공유해주세요!`
        );
      }
    } catch (err) {
      console.error("공유 실패:", err);
    } finally {
      setIsSharing(false);
    }
  };

  return (
    <>
      <button
        disabled={isSharing}
        onClick={handleShare}
        className="bg-blue-600 hover:hover:bg-blue-700 text-white rounded-lg px-4 py-2 mt-2"
      >
        {isSharing ? "공유 중..." : "📤 공유하기"}
      </button>
      {alertMessage && (
        <AlertModal
          title="알림"
          message={alertMessage}
          buttonText="확인"
          onClose={() => setAlertMessage(null)}
        />
      )}
    </>
  );
}
