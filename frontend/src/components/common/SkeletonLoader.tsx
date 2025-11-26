export default function SkeletonLoader() {
  return (
    <div className="mx-auto w-full rounded-xl p-4">
      <div className="flex animate-pulse space-x-4">
        <div className="size-12 rounded-full bg-gray-200"></div>
        <div className="flex-1 space-y-4 py-1">
          <div className="h-3 rounded bg-gray-200 w-1/3"></div>
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2 h-3 rounded bg-gray-200"></div>
              <div className="col-span-1 h-3 rounded bg-gray-200"></div>
            </div>
            <div className="h-3 rounded bg-gray-200"></div>
          </div>
        </div>
      </div>
    </div>
  );
}
