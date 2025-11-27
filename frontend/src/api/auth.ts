import { httpDelete, httpGet, httpPost, httpPostUrlEncoded, httpPut } from "./http";


export type LoginResult = {
  access_token: string;
  token_type: string;
};

export type MyPageResult = {
  id: number;
  username: string;
  email: string;
  business_type: string;
  location: string;
  menu_items: string[];
  business_hours: string;
};
interface DeleteMeSuccess {
  status: string;
  message: string;
}




export async function loginRequest(username: string, password: string): Promise<LoginResult> {
  return httpPostUrlEncoded("/auth/login", { username, password, grant_type: "password" });
}

export async function registerRequest(form: {
  username: string;
  password: string;
  // name: string;
  email: string;
  business_type: string;
  location: string;
  menu_items: string[];
  business_hours: string;
}) {
  return await httpPost("/auth/register", form);
}

export async function getMyPageRequest(): Promise<MyPageResult> {
  return httpGet("/auth/me");
}

export async function putMyPageRequest(form: {
  business_type: string;
  location: string;
  menu_items: string[];
  business_hours: string;
}) {
  return httpPut("/auth/me", form);
}

export async function deleteMe(): Promise<DeleteMeSuccess> {
  return httpDelete("/auth/me");
}

export async function findUsernameRequest(email: string) {
  return httpPost("/auth/find/username", { email });
}

export async function findPasswordRequest(username: string, email: string) {
  return httpPost("/auth/find/password", { username, email });
}

export async function resetPasswordRequest(username: string, password: string) {
  return httpPost("/auth/reset/password", { username, password });
}
