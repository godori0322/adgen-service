export function isTokenExpired(token: string) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    const exp = payload.exp * 1000; // exp는 초 단위
    return Date.now() > exp;
  } catch {
    return true; // JWT 파싱 실패 = 만료된 것으로 처리
  }
}
