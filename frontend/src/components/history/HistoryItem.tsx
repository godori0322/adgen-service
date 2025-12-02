import { format } from "date-fns";
import { ko } from "date-fns/locale";
import { useState } from "react";

interface HistoryItemProps {
  item: {
    id: number;
    idea: string;
    caption: string;
    hashtags: string;
    image_url: string | null;
    audio_url: string | null;
    video_url: string | null;
    created_at: string;
  };
  onClick?: () => void;
}

export default function HistoryItem({ item, onClick }: HistoryItemProps) {
  const { idea, image_url, audio_url, video_url, created_at } = item;
  const [imgLoading, setImgLoading] = useState(true);
  const [imgError, setImgError] = useState(false);

  const createdDate = format(new Date(created_at), "yyyy.MM.dd", { locale: ko });
  const mediaEndpoint = import.meta.env.VITE_MINIO_ENDPOINT;

  return (
    <div
      className="flex gap-4 items-start cursor-pointer rounded-2xl bg-white
             shadow-sm border border-gray-200 p-5 transition-all
             hover:shadow-lg hover:-translate-y-1 active:scale-[0.98]
             duration-200 relative"
      onClick={onClick}
    >
      {/* 썸네일 */}
      <div className="relative w-48 h-48 rounded-xl overflow-hidden shrink-0 bg-gray-100">
        {imgLoading && !imgError && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="animate-spin h-7 w-7 border-2 border-gray-400 border-t-transparent rounded-full" />
          </div>
        )}

        {!imgError && image_url && (
          <img
            src={mediaEndpoint + image_url}
            alt="thumbnail"
            className={`object-cover w-full h-full transition-opacity duration-300 ${
              imgLoading ? "opacity-0" : "opacity-100"
            }`}
            onLoad={() => setImgLoading(false)}
            onError={() => {
              setImgError(true);
              setImgLoading(false);
            }}
          />
        )}

        {imgError && (
          <span className="absolute inset-0 text-xl flex justify-center items-center">🖼️❌</span>
        )}

        {!image_url && !imgError && (
          <span className="absolute inset-0 text-4xl flex justify-center items-center">
            {video_url ? "🎬" : audio_url ? "🎧" : "📝"}
          </span>
        )}
      </div>

      {/* 텍스트 */}
      <div className="flex flex-col flex-1 min-w-0 pr-12">
        {/* 날짜 */}
        <p className="text-sm text-gray-400 font-medium mb-1.5">{createdDate}</p>

        {/* 제목 */}
        <p className="text-[18px] font-medium text-gray-700 leading-snug line-clamp-3 mt-3">
          {idea}
        </p>
      </div>

      {/* 아이콘 — 카드 오른쪽 아래 고정 */}
      <div className="absolute bottom-4 right-4 text-xl flex gap-1 opacity-70">
        {image_url && <span>🖼️</span>}
        {audio_url && <span>🎧</span>}
        {video_url && <span>🎬</span>}
      </div>
    </div>
  );
}
