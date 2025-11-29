import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 text-center px-6">
      <h1 className="text-7xl font-bold text-blue-600 mb-4">404</h1>
      <h2 className="text-2xl font-semibold text-gray-800 mb-2">페이지를 찾을 수 없습니다</h2>
      <p className="text-gray-500 mb-6">요청하신 페이지가 존재하지 않거나 이동되었어요.</p>

      <Link
        to="/"
        className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium shadow hover:bg-blue-700 transition"
      >
        홈으로 돌아가기 🏠
      </Link>
    </div>
  );
}
