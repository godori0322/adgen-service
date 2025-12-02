import http from "k6/http";
import { sleep } from "k6";

// ===== [INIT 단계: 파일 로드 가능] =====
const img = open("images/sample1.png", "b");
console.log(`[INIT] Image loaded: size=${img.length} bytes`);

export let options = {
  vus: 10,
  duration: "30s",
};

// ===== [VU EXECUTION 단계] =====
export default function () {
  const url = "http://127.0.0.1:8001/api/diffusion/synthesize/auto/upload";

  // 파일이 정상 로드됐는지 확인
  if (!img || img.length === 0) {
    console.log("[ERROR] imageBytes is empty — open() failed in INIT stage");
    return;
  }

  const form = {
    file: http.file(img, "sample1.png"),
    prompt: "A cinematic product shot on a warm cafe background",
    composition_mode: "balanced",
  };

  // HTTP 요청 수행
  const res = http.post(url, form);
  console.log(`[DEBUG] status=${res.status}`);

  // 응답 body 확인
  if (res.status !== 0) {
    console.log("[DEBUG] Body snippet:", String(res.body).slice(0, 200));
  } else {
    console.log("[ERROR] HTTP request seems not executed (status=0)");
  }

  sleep(1);
}
