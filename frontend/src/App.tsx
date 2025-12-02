import { Route, Routes } from "react-router-dom";
import AuthLayout from "./components/layout/AuthLayout";
import MainLayout from "./components/layout/MainLayout";
import FindAccountPage from "./pages/auth/FindAccount";
import LoginPage from "./pages/auth/Login";
import ResetPasswordPage from "./pages/auth/ResetPassword";
import SignupPage from "./pages/auth/Signup";
import VoiceHomePage from "./pages/home/VoiceHome";
import MyPage from "./pages/mypage/MyPage";
import NotFoundPage from "./pages/NotFound";
import PrivateRoute from "./router/PrivateRoute";

function App() {
  return (
    <>
      <Routes>
        {/* 로그인/회원가입 */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/find" element={<FindAccountPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
        </Route>

        <Route element={<MainLayout />}>
          {/* 로그인 없이 접근 가능 */}
          <Route path="/" element={<VoiceHomePage />} />

          {/* 로그인 필요한 페이지 */}
          <Route
            path="/mypage"
            element={
              <PrivateRoute>
                <MyPage />
              </PrivateRoute>
            }
          />
          {/* 404 에러 페이지 */}
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </>
  );
}

export default App;
