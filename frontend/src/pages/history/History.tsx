import { format } from "date-fns";
import { ko } from "date-fns/locale";
import { useEffect, useMemo, useState } from "react";
import { getHistory } from "../../api/history";
import { PageTitle } from "../../components/common/Title";
import HistoryGroupSkeleton from "../../components/history/HistoryGroupSkeleton";
import HistoryItem from "../../components/history/HistoryItem";
import HistoryModal from "../../components/history/HistoryModal";

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

  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const limit = 10;

  const loadHistory = async () => {
    if (!hasMore) return;

    if (skip === 0) setLoading(true);
    else setLoadingMore(true);

    const res = await getHistory(skip, limit);
    if (skip === 0) setTotalCount(res.total ?? 0);

    const newData = res.history ?? [];
    setHistories((prev) => [...prev, ...newData]);

    const updatedCount = skip + newData.length;
    setSkip(updatedCount);
    setHasMore(updatedCount < (res.total ?? 0));

    setLoading(false);
    setLoadingMore(false);
  };

  useEffect(() => {
    loadHistory();
  }, []);

  // 그룹핑
  const grouped = useMemo(() => {
    return histories.reduce((acc, item) => {
      const date = format(new Date(item.created_at), "yyyy.MM.dd (EEE)", { locale: ko });
      if (!acc[date]) acc[date] = [];
      acc[date].push(item);
      return acc;
    }, {} as Record<string, History[]>);
  }, [histories]);

  const handlePrev = () =>
    setSelectedIndex((prev) => (prev !== null && prev > 0 ? prev - 1 : prev));

const handleNext = async () => {
  if (selectedIndex === null) return;

  const isLastItem = selectedIndex === histories.length - 1;

  if (isLastItem && hasMore) {
    await loadHistory(); 
    setSelectedIndex((prev) => (prev !== null ? prev + 1 : prev));
    return;
  }

  // 일반적인 이동
  setSelectedIndex((prev) => (prev !== null && prev < histories.length - 1 ? prev + 1 : prev));
};

  return (
    <div className="max-w-3xl mx-auto pt-4 pb-32 px-2">
      <PageTitle variant="section">🎙️ 광고 히스토리</PageTitle>

      <p className="text-md text-gray-500 mt-3 mb-6">
        총 <span className="font-semibold text-gray-700">{totalCount}</span>개
      </p>

      {/* 초기 로딩 */}
      {loading && histories.length === 0 && (
        <div className="flex flex-col gap-10 mt-2 min-h-[400px]">
          {[1, 2].map((_, idx) => (
            <HistoryGroupSkeleton key={idx} />
          ))}
        </div>
      )}

      {/* 그룹 렌더 */}
      {!loading &&
        Object.entries(grouped).map(([date, list]) => (
          <section key={date} className="mb-8">
            <p className="text-xl font-bold text-gray-900 border-b pb-1 mb-3">{date}</p>

            <div className="flex flex-col gap-5">
              {list.map((item) => {
                const globalIndex = histories.findIndex((h) => h.id === item.id);
                return (
                  <HistoryItem
                    key={`${item.id}-${item.created_at}`}
                    item={item}
                    onClick={() => setSelectedIndex(globalIndex)}
                  />
                );
              })}
            </div>
          </section>
        ))}

      {/* 더 보기 버튼 */}
      {hasMore && (
        <div className="flex justify-center mt-4">
          <button
            onClick={loadHistory}
            disabled={loadingMore}
            className="text-blue-600 text-sm border border-blue-300 py-1 px-4 rounded-md 
                     hover:bg-blue-50 transition disabled:opacity-50"
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

      {/* 모달 */}
      {selectedIndex !== null && (
        <HistoryModal
          item={histories[selectedIndex]}
          onClose={() => setSelectedIndex(null)}
          onPrev={selectedIndex > 0 ? handlePrev : undefined}
          onNext={selectedIndex < histories.length - 1 || hasMore ? handleNext : undefined}
        />
      )}
    </div>
  );
}
