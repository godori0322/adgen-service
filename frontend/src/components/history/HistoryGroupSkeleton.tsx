export default function HistoryGroupSkeleton() {
  return (
    <div className="animate-pulse">
      {/* 날짜 영역 */}
      <div className="h-6 w-44 bg-gray-300 rounded-md mb-4" />

      {/* 리스트 아이템 3개 */}
      <div className="flex flex-col gap-6">
        {[1, 2, 3].map((_, i) => (
          <div
            key={i}
            className="relative flex gap-5 items-start rounded-2xl bg-white
                       shadow-sm border border-gray-200 p-5"
          >
            {/* 썸네일 스켈레톤 */}
            <div className="w-48 h-48 bg-gray-200 rounded-xl shrink-0" />

            {/* 텍스트 영역 */}
            <div className="flex flex-col flex-1 min-w-0 pr-12 justify-between">
              {/* 날짜 */}
              <div className="w-24 h-4 bg-gray-200 rounded mb-4" />

              {/* 아이디어 텍스트 3줄 */}
              <div className="space-y-2">
                <div className="w-full h-4 bg-gray-200 rounded" />
                <div className="w-4/5 h-4 bg-gray-200 rounded" />
                <div className="w-2/3 h-4 bg-gray-200 rounded" />
              </div>
            </div>

            {/* 아이콘 영역 */}
            <div className="absolute bottom-4 right-4 flex gap-2">
              <div className="w-6 h-6 bg-gray-200 rounded-full" />
              <div className="w-6 h-6 bg-gray-200 rounded-full" />
              <div className="w-6 h-6 bg-gray-200 rounded-full" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
