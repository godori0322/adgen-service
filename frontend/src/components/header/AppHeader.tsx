// src/components/header/AppHeader.tsx
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function AppHeader() {
  const {isLogin, logout} = useAuth();

  
  return (
    <header className="w-full bg-white shadow-sm px-6 py-4 flex justify-between items-center">
      <Link to="/" className="text-xl font-bold text-blue-600">
        AdGen
      </Link>

      <nav className="flex gap-4">
        <Link to="/voice" className="text-gray-700 hover:text-blue-600">
          음성 입력
        </Link>
        {/* 로그인 상태 */}
        {isLogin ? (
          <>
            <Link to="/history" className="hover:text-blue-600">
              히스토리
            </Link>
            <Link to="/mypage" className="hover:text-blue-600">
              마이페이지
            </Link>
            <button onClick={logout} className="text-red-500 hover:text-red-600 font-medium">
              로그아웃
            </button>
          </>
        ) : (
          // 비로그인
          <Link to="/login" className="hover:text-blue-600 font-medium">
            로그인
          </Link>
        )}
      </nav>
    </header>
  );
}
