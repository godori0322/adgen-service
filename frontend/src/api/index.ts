// src/api/axios.ts
import axios from "axios";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8080/api",
});

// ⭐ 401 응답 시 자동 로그아웃
API.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      console.log("❌ Unauthorized → 자동 로그아웃");

      localStorage.removeItem("accessToken");
      sessionStorage.removeItem("chatMessages");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default API;
