import { httpDelete, httpGet, httpPut, httpPostJson, httpPostForm } from "./http";

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
  const form = new FormData();
  form.append("username", username);
  form.append("password", password);
  form.append("grant_type", "password");

  return httpPostForm("/auth/login", form);
}

export async function registerRequest(form: {
  username: string;
  password: string;
  email: string;
  business_type: string;
  location: string;
  menu_items: string[];
  business_hours: string;
}) {
  return httpPostJson("/auth/register", form);
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
  return httpPostJson("/auth/find/username", { email });
}

export async function findPasswordRequest(username: string, email: string) {
  return httpPostJson("/auth/find/password", { username, email });
}

export async function resetPasswordRequest(username: string, password: string) {
  return httpPostJson("/auth/reset/password", { username, password });
}
