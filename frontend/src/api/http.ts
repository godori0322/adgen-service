// src/api/http.ts

const BASE_URL = import.meta.env.VITE_FAST_API_URL + "/api";

const authHeader = () => {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

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
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function httpPostUrlEncoded(url: string, params: Record<string, string>) {
  const form = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => form.append(k, v));

  const res = await fetch(BASE_URL + url, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: form,
  });

  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function httpPostForm(url: string, form: FormData) {
  const res = await fetch(BASE_URL + url, {
    method: "POST",
    headers: {},
    body: form,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json();
}

export async function httpPostImg(url: string, body: any) {
  const res = await fetch(BASE_URL + url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: localStorage.getItem("token") ? `Bearer ${localStorage.getItem("token")}` : "",
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.blob();
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
