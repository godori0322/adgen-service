import { httpGet } from "./http";

export async function getHistory(skip = 0, limit = 20) {
  return httpGet(`/history?skip=${skip}&limit=${limit}`);
}
