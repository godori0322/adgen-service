export default function HistoryGroupSkeleton() {
  return (
    <div className="animate-pulse">
      {/* 날짜 영역 */}
      <div className="h-6 w-44 bg-gray-300 rounded-md mb-4" />

      {/* 리스트 아이템 3개 */}
      <div className="flex flex-col gap-6">
        {[1, 2, 3].map((_, i) => (
          <div key={i} className="flex sm:flex-row flex-col items-start gap-2">
            {/* 썸네일 */}
            <div className="relative w-48 h-48 rounded-xl bg-gray-200 shrink-0" />

            {/* 텍스트 카드 */}
            <div
              className="bg-white border border-gray-200 rounded-xl shadow-[0_2px_6px_rgba(0,0,0,0.05)] 
                          p-4 flex flex-col gap-2 w-full min-h-48"
            >
              {/* 날짜 스켈레톤 */}
              <div className="w-20 h-3 bg-gray-200 rounded" />

              {/* 아이디어 스켈레톤 */}
              <div className="space-y-2 mt-2">
                <div className="w-full h-3 bg-gray-200 rounded" />
                <div className="w-5/6 h-3 bg-gray-200 rounded" />
                <div className="w-2/3 h-3 bg-gray-200 rounded" />
              </div>

              {/* 아이콘 스켈레톤 - 카드 아래 정렬 */}
              <div className="mt-auto flex gap-2 opacity-60">
                <div className="w-5 h-5 bg-gray-200 rounded-full" />
                <div className="w-5 h-5 bg-gray-200 rounded-full" />
                <div className="w-5 h-5 bg-gray-200 rounded-full" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
