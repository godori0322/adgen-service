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
      className="flex sm:flex-row flex-col items-start cursor-pointer group gap-2"
      onClick={onClick}
    >
      {/* 이미지 영역 */}
      <div className="relative w-full sm:w-48 h-56 sm:h-48  rounded-xl bg-gray-100 overflow-hidden shrink-0 border border-gray-200">
        {imgLoading && !imgError && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="animate-spin h-7 w-7 border-2 border-gray-300 border-t-transparent rounded-full" />
          </div>
        )}

        {!imgError && image_url && (
          <img
            src={mediaEndpoint + image_url}
            alt="thumbnail"
            className={`object-cover object-center w-full h-full transition-opacity duration-300 ${
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
          <span className="text-3xl absolute inset-0 flex items-center justify-center">❌</span>
        )}

        {!image_url && !imgError && (
          <span className="text-3xl absolute inset-0 flex items-center justify-center">
            {video_url ? "🎬" : audio_url ? "🎧" : "📝"}
          </span>
        )}
      </div>

      {/* 텍스트 카드 */}
      <div className="bg-white border border-gray-200 rounded-xl shadow-[0_2px_6px_rgba(0,0,0,0.05)] p-4 flex flex-col gap-2 w-full min-h-48 transition-all group-hover:shadow-md">
        <p className="text-xs text-gray-400">{createdDate}</p>
        <p className="text-base font-medium text-gray-900 line-clamp-3 leading-snug">{idea}</p>
        <div className="mt-auto text-lg flex gap-1 opacity-80">
          {image_url && <span>🖼️</span>}
          {audio_url && <span>🎧</span>}
          {video_url && <span>🎬</span>}
        </div>
      </div>
    </div>
  );
}
