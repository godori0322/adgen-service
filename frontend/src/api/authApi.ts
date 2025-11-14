import { httpPost, httpPostUrlEncoded } from "./http";


export type LoginResult = {
  token: string;
  user: { id: number; username: string; };
};


export async function loginRequest(username: string, password: string): Promise<LoginResult> {
  return httpPostUrlEncoded("/auth/login", { username, password, grant_type: "password" });
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