import { httpPost } from "./http";


const MOCK_USERS = [
  { id:1, email: "test123@test.com", password: "abc123!", token: "dummy-token-abc", name: "Tester" },
  { id:2, email: "admin@test.com", password: "admin123!", token: "dummy-token-admin", name: "Admin" },
];


export type LoginResult = {
  token: string;
  user: { id: number; email: string; name?: string };
};


function mockLogin(email: string, password: string): Promise<LoginResult> {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const user = MOCK_USERS.find((u) => u.email === email && u.password === password);
      if (user) {
        // ✅ id 포함해서 반환
        resolve({ token: user.token, user: { id: user.id, email: user.email, name: user.name } });
      } else {
        reject(new Error("이메일 또는 비밀번호가 올바르지 않습니다."));
      }
    }, 400);
  });
}


export async function loginRequest(email: string, password: string): Promise<LoginResult> {
  // return httpPost("/auth/login", {email, password})
  return mockLogin(email, password);
}