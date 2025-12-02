export default function HistoryItemSkeleton() {
  return (
    <div className="flex gap-3 animate-pulse">
      <div className="w-20 h-20 bg-gray-200 rounded-lg" />

      <div className="flex-1 flex flex-col gap-2">
        <div className="h-3 w-24 bg-gray-200 rounded" />
        <div className="h-3 w-full bg-gray-200 rounded" />
        <div className="h-3 w-3/4 bg-gray-200 rounded" />
      </div>
    </div>
  );
}
