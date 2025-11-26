import { createContext, useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";


interface AuthContextValue {
  token: string | null;
  isLogin: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({children}: {children: React.ReactNode}) {
  const [token, setToken] = useState<string | null>(null);
  const navigate = useNavigate();
  
  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    if (storedToken) setToken(storedToken);
  }, []);

  const login = (token: string) => {
    setToken(token);
    localStorage.setItem('token', token);
  }

  const logout = () => {
    setToken(null);
    localStorage.removeItem('token');
    navigate("/");
    window.location.reload();
  };

  return (
    <AuthContext.Provider value={{ token, isLogin: !!token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("AuthContext must be used inside AuthProvider");
  return ctx;
}