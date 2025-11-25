
// 새로고침 시, guest_session_id 삭제
window.addEventListener("beforeunload", () => {
  sessionStorage.removeItem("guest_session_id");
});

// UUID 생성
export const generateUUID = () => {
  return crypto.randomUUID();
}

export const getGuestSessionId = () => {
  const key = "guest_session_id";

  let id = sessionStorage.getItem(key);

  if(!id) {
    id = generateUUID();
    sessionStorage.setItem(key, id);
  }

  return id;
}