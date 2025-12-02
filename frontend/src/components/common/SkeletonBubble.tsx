export default function SkeletonBubble({ text }: { text: string }) {
  return (
    // <div className="mr-auto  text-gray-900  p-3 shadow w-fit max-w-[80%]">
    //   <div className="animate-pulse rounded-lg bg-gray-300 w-40 h-40 mb-2"></div>
    //   <p className="text-sm text-gray-600">{text}</p>

    // </div>
    <div className="flex flex-col items-center text-center gap-2 p-4">
      {/* 이미지 스켈레톤 */}
      <div className="w-40 h-40 bg-gray-300 animate-pulse rounded-lg" />

      {/* 텍스트 */}
      <span className="text-gray-600 text-sm">{text}</span>

      {/* 로딩 스피너 */}
      <div className="w-6 h-6 border-4 border-gray-400 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}
