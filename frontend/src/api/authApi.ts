import { httpPost } from "./http";


const MOCK_USERS = [
  { id:1, userId: "test123", password: "test123!", token: "dummy-token-abc", name: "Tester" },
  { id:2, userId: "admin", password: "admin123!", token: "dummy-token-admin", name: "Admin" },
];


export type LoginResult = {
  token: string;
  user: { id: number; userId: string; name?: string };
};


function mockLogin(userId: string, password: string): Promise<LoginResult> {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const user = MOCK_USERS.find((u) => u.userId === userId && u.password === password);
      if (user) {
        // ✅ id 포함해서 반환
        resolve({ token: user.token, user: { id: user.id, userId: user.userId, name: user.name } });
      } else {
        reject(new Error("아이디 또는 비밀번호가 올바르지 않습니다."));
      }
    }, 400);
  });
}


export async function loginRequest(userId: string, password: string): Promise<LoginResult> {
  // return httpPost("/auth/login", {userId, password})
  return mockLogin(userId, password);
}

export async function registerUser(form: {
  userId: string;
  password: string;
  name: string;
  storeType: string;
  address: string;
}) {
  return await httpPost("/auth/register", form);
}