import { format } from "date-fns";
import { ko } from "date-fns/locale";
import { useEffect, useState } from "react";

interface Props {
  item: any;
  onClose: () => void;
  onPrev?: () => void;
  onNext?: () => void;
}

export default function HistoryModal({ item, onClose, onPrev, onNext }: Props) {
  const mediaEndpoint = import.meta.env.VITE_MINIO_ENDPOINT;
  const createdDate = format(new Date(item.created_at), "yyyy.MM.dd (EEE)", {
    locale: ko,
  });

  const mediaList = [
    item.image_url && { type: "image", src: mediaEndpoint + item.image_url },
    item.video_url && { type: "video", src: mediaEndpoint + item.video_url },
  ].filter(Boolean);

  if (mediaList.length === 0) {
    mediaList.push({ type: "none", src: "" });
  }

  const [activeIndex, setActiveIndex] = useState(0);
  useEffect(() => setActiveIndex(0), [item]);

  const goPrevMedia = () => setActiveIndex((prev) => Math.max(prev - 1, 0));
  const goNextMedia = () => setActiveIndex((prev) => Math.min(prev + 1, mediaList.length - 1));

  return (
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center"
      onClick={onClose}
    >
      <div
        className="flex flex-col sm:flex-row items-center gap-3 pointer-events-none
                   w-[95vw] max-w-[1250px]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* ◀ Prev 버튼 (PC에서만) */}
        <button
          className={`hidden sm:flex pointer-events-auto
                     bg-white/15 hover:bg-white/30 text-white text-4xl rounded-full
                     w-10 h-10 items-center justify-center shrink-0 
                     ${onPrev ? "" : "opacity-0 pointer-events-none"}`}
          onClick={(e) => {
            e.stopPropagation();
            onPrev?.();
          }}
        >
          ❮
        </button>

        {/* Modal */}
        <div
          className="bg-[#111] rounded-xl overflow-hidden relative pointer-events-auto
                     flex flex-col sm:flex-row flex-1
                     h-screen sm:h-[80vh] sm:min-h-[450px] sm:max-h-[800px]"
        >
          {/* 닫기 */}
          <button
            className="absolute top-3 right-3 text-gray-300 hover:text-white text-2xl z-50 pointer-events-auto"
            onClick={onClose}
          >
            ✕
          </button>

          {/* 미디어 영역 */}
          <div className="w-full sm:flex-1 bg-black flex items-center justify-center relative">
            {/* 이미지/비디오 이동 버튼 - PC에서만 */}
            {mediaList.length > 1 && activeIndex > 0 && (
              <button
                className="hidden sm:block absolute left-3 bg-black/50 text-white text-3xl p-2 rounded-full pointer-events-auto"
                onClick={(e) => {
                  e.stopPropagation();
                  goPrevMedia();
                }}
              >
                ❮
              </button>
            )}
            {mediaList.length > 1 && activeIndex < mediaList.length - 1 && (
              <button
                className="hidden sm:block absolute right-3 bg-black/50 text-white text-3xl p-2 rounded-full pointer-events-auto"
                onClick={(e) => {
                  e.stopPropagation();
                  goNextMedia();
                }}
              >
                ❯
              </button>
            )}

            {/* media */}
            {mediaList[activeIndex].type === "none" ? (
              <div className="text-gray-300 text-sm">📁 첨부된 미디어가 없습니다</div>
            ) : mediaList[activeIndex].type === "image" ? (
              <img
                src={mediaList[activeIndex].src}
                className="w-full max-h-[70vh] sm:max-h-[90%] object-contain"
              />
            ) : (
              <video
                src={mediaList[activeIndex].src}
                controls
                autoPlay
                className="w-full max-h-[70vh] sm:max-h-[90%] object-contain"
              />
            )}
          </div>

          {/* 정보 영역 */}
          <div className="w-full sm:w-[32%] min-w-[260px] bg-white p-5 flex flex-col overflow-y-auto">
            <p className="text-xs text-gray-500">{createdDate}</p>
            <p className="text-[15px] font-semibold mt-2 leading-snug break-words">{item.idea}</p>

            {item.audio_url && (
              <audio controls src={mediaEndpoint + item.audio_url} className="mt-4 w-full" />
            )}
            {item.hashtags && (
              <p className="text-blue-600 text-sm mt-4 whitespace-pre-line break-words">
                {item.hashtags}
              </p>
            )}

            <div className="mt-auto pt-4 text-xl flex gap-2 text-gray-500">
              {item.image_url && <span>🖼️</span>}
              {item.audio_url && <span>🎧</span>}
              {item.video_url && <span>🎬</span>}
            </div>
          </div>
        </div>

        {/* ▶ Next 버튼 (PC에서만) */}
        <button
          className={`hidden sm:flex pointer-events-auto
                     bg-white/15 hover:bg-white/30 text-white text-4xl rounded-full
                     w-10 h-10 items-center justify-center shrink-0 
                     ${onNext ? "" : "opacity-0 pointer-events-none"}`}
          onClick={(e) => {
            e.stopPropagation();
            onNext?.();
          }}
        >
          ❯
        </button>
      </div>
    </div>
  );
}
