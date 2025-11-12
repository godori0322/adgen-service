// src/api/http.ts

const BASE_URL = import.meta.env.FAST_API_URL

export async function httpGet(url: string) {
  const res = await fetch(BASE_URL + url, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: localStorage.getItem("token") ? `Bearer ${localStorage.getItem("token")}` : "",
    },
  });
  return res.json();
}

export async function httpPost(url: string, body: any) {
  const res = await fetch(BASE_URL + url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: localStorage.getItem("token") ? `Bearer ${localStorage.getItem("token")}` : "",
    },
    body: JSON.stringify(body),
  });
  return res.json();
}

export async function httpPut(url: string, body: any) {
  const res = await fetch(BASE_URL + url, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
    body: JSON.stringify(body),
  });
  return res.json();
}

export async function httpDelete(url: string) {
  const res = await fetch(BASE_URL + url, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  return res.json();
}
