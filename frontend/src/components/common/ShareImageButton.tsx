import { useState } from "react";
import AlertModal from "./AlertModal";

interface GptParsed {
  idea: string;
  caption: string;
  hashtags?: string[];
}

interface ShareImageButtonProps {
  imageUrl: string;
  parsed?: GptParsed; // GPT 결과 전달받기
}

export default function ShareImageButton({ imageUrl, parsed }: ShareImageButtonProps) {
  const [isSharing, setIsSharing] = useState(false);
  const [alertMessage, setAlertMessage] = useState<string | null>(null);

  const buildShareData = (file: File) => {
    // 기본 메시지 fallback
    let title = "내가 만든 광고 이미지";
    let text = "AI로 만든 광고 이미지입니다!";

    if (parsed) {
      if (parsed.idea?.trim()) title = parsed.idea.trim();
      if (parsed.caption?.trim()) text = parsed.caption.trim();

      if (parsed.hashtags?.length) {
        text += `\n${parsed.hashtags.join(" ")}`;
      }
    }

    return { title, text, files: [file] };
  };

  const handleShare = async () => {
    try {
      setIsSharing(true);

      const res = await fetch(imageUrl);
      const blob = await res.blob();
      const file = new File([blob], "adgen-result.png", { type: blob.type });

      const shareData = buildShareData(file);

      if (navigator.share && navigator.canShare && navigator.canShare(shareData)) {
        await navigator.share(shareData);
      } else {
        alert("공유 기능이 지원되지 않습니다 🥲\n다운로드 후 직접 공유해주세요!");
        setAlertMessage(
          "📱 공유 기능이 지원되지 않는 환경입니다.\n이미지를 다운로드하여 직접 공유해주세요!"
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
