import { format } from "date-fns";
import { ko } from "date-fns/locale";

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

  // 날짜 변환
  const createdDate = format(new Date(created_at), "yyyy.MM.dd", { locale: ko });
  const mediaEndpoint = import.meta.env.VITE_MINIO_ENDPOINT;

  // 이미지가 없을 경우 아이콘
  const renderThumbnail = () => {
    if (image_url)
      return (
        <img
          src={mediaEndpoint + image_url}
          className="w-20 h-20 rounded-lg object-cover bg-gray-200"
          alt="thumbnail"
        />
      );
    return (
      <div className="w-20 h-20 bg-gray-100 rounded-lg flex items-center justify-center text-2xl">
        {video_url ? "🎬" : audio_url ? "🎧" : "📝"}
      </div>
    );
  };

  return (
    <div
      className="w-full flex gap-4 items-start bg-white p-4 rounded-xl border shadow-sm
                           hover:shadow-md transition-all cursor-pointer mb-3"
      onClick={onClick}
    >
      {/* 썸네일 */}
      {renderThumbnail()}

      {/* 텍스트 */}
      <div className="flex flex-col flex-1 min-w-0">
        <p className="text-xs text-gray-400 mb-1">{createdDate}</p>

        <p className="text-sm font-medium text-gray-800 line-clamp-2 leading-tight">{idea}</p>
        {/* 미디어 타입 */}
        <div className="mt-1 text-lg flex gap-1">
          {image_url && <span>🖼️</span>}
          {audio_url && <span>🎧</span>}
          {video_url && <span>🎬</span>}
        </div>
      </div>
    </div>
  );
}
