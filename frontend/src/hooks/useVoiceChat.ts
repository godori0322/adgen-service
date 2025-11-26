import { useRef, useState } from "react";
import { generateDialogueRequest, generateDiffusionRequest, generateSyntheSizeDiffusionRequest, uploadImage } from "../api/generate";
import { IMAGE_GUIDE_MESSAGE } from "../constants/chat";
import { useAuth } from "../context/AuthContext";
import { formatChatResponse } from "../utils/chatFormatter";
import { useDotsAnimation } from "./useDotsAnimation";
import { useWhisper } from "./useWhisper";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  img?: string;
  tempId?: number; // 임시 메시지 식별용
}

export function useVoiceChat() {
  const { isLogin } = useAuth();
  const [isWorking, setIsWorking] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const { startDots, stopDots } = useDotsAnimation(setMessages);
  const [needImage, setNeedImage] = useState(false);
  const [uploadedImageFile, setUploadedImageFile] = useState<File | null>(null);
  const pendingQuestionRef = useRef<string | null>(null);
  const sessionKeyRef = useRef<string | null>(null);

  // 세션키 업데이트
  const updateSessionKey = (key: string) => {
    sessionKeyRef.current = key;
  };

  const onAudioSend = async (audioBlob: Blob) => {

    setIsWorking(true);
    // 너무 짧은 음성
    if (audioBlob.size < 10000) {
      setMessages((prev) => [
        ...prev,
        { role: "user", content: "인식할 수 없습니다. 🎤" },
        { role: "assistant", content: "음성이 너무 짧아요! 조금 더 이야기해주세요 😊" },
      ]);
      setIsWorking(false);
      return;
    }
    try {
      const userTempId = Date.now();
      setMessages((prev) => [...prev, { role: "user", content: ".", tempId: userTempId }]);
      startDots(userTempId);

      // 1. Whisper API 호출
      const userText = await useWhisper(audioBlob);
      stopDots();
      setMessages((prev) =>
        prev.map((m) => (m.tempId === userTempId ? { ...m, content: userText } : m))
      );

      // 2. assistant 임시 메세지
      const assistantTempId = Date.now() + 1;
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: ".", tempId: assistantTempId },
      ]);
      startDots(assistantTempId);

      // 3. 멀티턴 대화 모드

      const adRes = await generateDialogueRequest(userText, isLogin);
      stopDots();
      if (sessionKeyRef.current !== adRes.session_key) {
        updateSessionKey(adRes.session_key);
      }
      if (!adRes.is_complete) {
        // 3-1. 광고 생성  - 이미지 요청
        if (adRes.type === "ad" && !uploadedImageFile) {
          pendingQuestionRef.current = adRes.next_question;
          setNeedImage(true);

          setMessages((prev) =>
            prev.map((m) =>
              m.tempId === assistantTempId ? { ...m, content: IMAGE_GUIDE_MESSAGE } : m
            )
          );
          return;
        } else {
          // 이미 이미지 업로드가 되어 있다면 next_question 바로 출력
          setMessages((prev) =>
            prev.map((m) =>
              m.tempId === assistantTempId ? { ...m, content: adRes.next_question } : m
            )
          );
          return;
        }
      }

      // 4. 대화 죵로 멘트 처리
      const formatted = adRes.final_content
        ? formatChatResponse(adRes.final_content)
        : adRes.last_ment ?? "";
      setMessages((prev) =>
        prev.map((m) => (m.tempId === assistantTempId ? { ...m, content: formatted } : m))
      );

      // 5. 광고 - 이미지 생성
      const imagePrompt =
        adRes.final_content?.image_prompt ?? adRes.final_content?.img_prompt ?? null;

      if (imagePrompt) {
        const imgTempId = Date.now() + 2;
        // 이미지 생성 중 메시지 추가
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "🖼️ 이미지 생성 중입니다...", tempId: imgTempId },
        ]);

        if (!uploadedImageFile) return;
        const imgSrc = await generateSyntheSizeDiffusionRequest(imagePrompt, uploadedImageFile);

        // 이미지 채우기
        setMessages((prev) =>
          prev.map((m) => (m.tempId === imgTempId ? { ...m, content: "", img: imgSrc } : m))
        );
      }
      if (adRes.is_complete) setUploadedImageFile(null);
    } catch (err: any) {
      const content = `❌ 오류 발생가 발생하였습니다. 다시 시도 부탁드립니다.`;
      setMessages((prev) => {
        if (prev.length === 0) {
          return [{ role: "assistant", content }];
        }
        const lastIndex = prev.length - 1;
        return prev.map((m, idx) => (idx === lastIndex ? { ...m, content } : m));
      });
      stopDots();
    } finally {
      setIsWorking(false);
    }
  };

  // 6. 이미지 업로드 처리
  const onImageUpload = async (file: File) => {
    const imgUrl = URL.createObjectURL(file);
    setUploadedImageFile(file);
    setNeedImage(false);
    // setAdImageUploaded(true);

    // 이미지 전송
    const key = sessionKeyRef.current;
    if (!key) return;
    await uploadImage(key, file);

    const cleaned = pendingQuestionRef.current!.trim();
    setMessages((prev) => [...prev, { role: "user", content: "", img: imgUrl }]);
    if (pendingQuestionRef.current!) {
      setMessages((prev) => [...prev, { role: "assistant", content: cleaned }]);
      pendingQuestionRef.current = null;
    }
    return;
  };

  return { messages, needImage, isWorking, onAudioSend, onImageUpload };
}
