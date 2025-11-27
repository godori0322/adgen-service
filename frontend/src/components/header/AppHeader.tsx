// src/components/header/AppHeader.tsx
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useChat } from "../../context/ChatContext";
import ConfirmModal from "../common/ConfirmModal";

export default function AppHeader() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isLogin, logout } = useAuth();
  const { resetMessages } = useChat();
  const [showConfirm, setShowConfirm] = useState(false);

  const handleLogoClick = (e: React.MouseEvent) => {
    if (location.pathname === "/") {
      e.preventDefault();
      if (!isLogin) {
        window.location.reload();
      }
    }
  };
  const handleLogout = () => {
    resetMessages();
    logout();
  };

  const handleNewChat = () => setShowConfirm(true);
  const confirmNewChat = () => {
    resetMessages();
    navigate("/");
    setShowConfirm(false);
  };
  const cancelNewChat = () => setShowConfirm(false);

  return (
    <header className="w-full bg-white shadow-sm px-6 py-4 flex justify-between items-center">
      <Link to="/" onClick={handleLogoClick} className="text-xl font-bold text-blue-600">
        AdGen
      </Link>

      <nav className="flex gap-4">
        {/* <Link to="/voiceChat" className="text-gray-700 hover:text-blue-600">
          음성 입력
        </Link> */}
        {/* 로그인 상태 */}
        {isLogin ? (
          <>
            {/* <Link to="/history" className="hover:text-blue-600">
              히스토리
            </Link> */}
            <button
              onClick={handleNewChat}
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              🆕 새 대화
            </button>
            <Link to="/mypage" className="hover:text-blue-600">
              마이페이지
            </Link>
            <button onClick={handleLogout} className="text-red-500 hover:text-red-600 font-medium">
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
      {showConfirm && (
        <ConfirmModal
          title="새 대화 시작"
          message={`현재 대화를 모두 삭제하고
            새로 시작할까요?`}
          confirmText="네, 새로 시작"
          cancelText="아니요"
          onConfirm={confirmNewChat}
          onCancel={cancelNewChat}
        />
      )}
    </header>
  );
}
