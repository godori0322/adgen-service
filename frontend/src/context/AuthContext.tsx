import { createContext, useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { isTokenExpired } from "../utils/auth";

interface AuthContextValue {
  token: string | null;
  isLogin: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const [token, setToken] = useState<string | null>(null);
  const [isLogin, setIsLogin] = useState(false);

  // 앱 로드 시 토큰 확인
  useEffect(() => {
    const storedToken = sessionStorage.getItem("accessToken");

    if (!storedToken) return;

    if (isTokenExpired(storedToken)) {
      console.log("🔒 토큰 만료 → 자동 로그아웃");
      sessionStorage.removeItem("accessToken");
      setToken(null);
      setIsLogin(false);
      return;
    }

    setToken(storedToken);
    setIsLogin(true);
  }, []);

  // 로그인
  const login = (newToken: string) => {
    sessionStorage.setItem("accessToken", newToken);
    setToken(newToken);
    setIsLogin(true);
  };

  // 로그아웃
  const logout = () => {
    sessionStorage.removeItem("accessToken");
    setToken(null);
    setIsLogin(false);
    navigate("/");
  };

  return (
    <AuthContext.Provider value={{ token, isLogin, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("AuthContext must be used inside AuthProvider");
  return ctx;
}
