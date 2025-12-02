import { useEffect, useState } from "react";
import { getHistory } from "../../api/history";
import { PageTitle } from "../../components/common/Title";
import HistoryItem from "../../components/history/HistoryItem";
import HistoryItemSkeleton from "../../components/history/HistoryItemSkeleton";

interface History {
  id: number;
  idea: string;
  caption: string;
  hashtags: string;
  image_url: string | null;
  audio_url: string | null;
  video_url: string | null;
  created_at: string;
}

export default function HistoryPage() {
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  const [histories, setHistories] = useState<History[]>([]);
  const [totalCount, setTotalCount] = useState(0);

  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [selected, setSelected] = useState<History | null>(null);

  const openModal = (item: History) => setSelected(item);
  const closeModal = () => setSelected(null);

  const limit = 10; // default

  const loadHistory = async () => {
    if (!hasMore) return;

    if (skip === 0) setLoading(true);
    else setLoadingMore(true);

    const res = await getHistory(skip, limit);
    if (skip === 0) setTotalCount(res.total ?? 0);
    const newData = res.history ?? [];
    setHistories((prev) => [...prev, ...newData]);

    setSkip((prev) => prev + newData.length);
    setHasMore(newData.length > 0);

    setLoading(false);
    setLoadingMore(false);
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const SKELETON_COUNT = 6;

  return (
    <div className="max-w-3xl mx-auto pt-4 pb-32 px-2">
      <PageTitle variant="section">🎙️ 광고 히스토리</PageTitle>

      <p className="text-sm text-gray-500 mt-3 mb-4">
        총 <span className="font-semibold text-gray-700">{totalCount}</span>개
      </p>

      <div className="flex flex-col gap-4 mt-2 min-h-[400px]">
        {loading && histories.length === 0
          ? // 🔥 Skeleton 목록 렌더링
            Array.from({ length: SKELETON_COUNT }).map((_, idx) => (
              <HistoryItemSkeleton key={`skeleton-${idx}`} />
            ))
          : histories.map((history, index) => (
              <HistoryItem
                key={`${history.id}-${index}`}
                item={history}
                onClick={() => openModal(history)}
              />
            ))}
      </div>

      {/* 더 보기 로딩 */}
      {hasMore && (
        <div className="flex justify-center mt-4">
          <button
            onClick={loadHistory}
            disabled={loadingMore}
            className="text-blue-600 text-sm border border-blue-300 py-1 px-4 rounded-md 
                     hover:bg-blue-50 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loadingMore ? (
              <div className="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full" />
            ) : (
              "🔽 더 보기"
            )}
          </button>
        </div>
      )}

      {!hasMore && !loading && (
        <p className="text-center text-gray-500 text-sm my-4">모든 광고 기록을 불러왔습니다!</p>
      )}
    </div>
  );
}
