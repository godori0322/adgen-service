import LoginPage from "./pages/auth/Login";
import SignupPage from "./pages/auth/Signup";
import VoiceHomePage from "./pages/home/VoiceHome";
import MyPage from "./pages/mypage/MyPage";
import PrivateRoute from "./router/PrivateRoute";
import AuthLayout from "./components/layout/AuthLayout";
import MainLayout from "./components/layout/MainLayout";
import { Route, Routes } from "react-router-dom";

function App() {
  return (
      <Routes>
        {/* 로그인/회원가입 */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
        </Route>
        {/* <Route path="/signup" element={<SignupPage />} /> */}

        <Route element={<MainLayout />}>
          {/* 로그인 없이 접근 가능 */}
          <Route path="/" element={<VoiceHomePage />} />
          {/* <Route path="/ad" element={<AdResultPage />} /> */}

          {/* 로그인 필요한 페이지 */}
          <Route
            path="/mypage"
            element={
              <PrivateRoute>
                <MyPage />
              </PrivateRoute>
            }
          />

          {/* <Route
            path="/history"
            element={
              <PrivateRoute>
                <HistoryPage />
              </PrivateRoute>
            }
          /> */}
        </Route>

        <Route path="*" element={<div>404 NOT FOUND</div>} />
      </Routes>
  );
}

export default App;
