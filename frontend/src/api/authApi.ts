import { httpPost, httpPostUrlEncoded } from "./http";


export type LoginResult = {
  access_token: string;
  token_type: string;
};


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