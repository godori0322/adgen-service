import { useRef, useState } from "react";
import {
  generateDialogueRequest,
  generateSyntheSizeDiffusionRequest,
  uploadImage,
} from "../api/generate";
import { IMAGE_GUIDE_MESSAGE } from "../constants/chat";
import { useAuth } from "../context/AuthContext";
import { useChat } from "../context/ChatContext";
import { formatChatResponse } from "../utils/chatFormatter";
import { useDotsAnimation } from "./useDotsAnimation";
import { useWhisper } from "./useWhisper";

export function useVoiceChat() {
  const { isLogin } = useAuth();
  const [isWorking, setIsWorking] = useState(false);
  const { messages, addMessage, updateTempMessage } = useChat();
  const { startDots, stopDots } = useDotsAnimation();
  const [needImage, setNeedImage] = useState(false);
  const [uploadedImageFile, setUploadedImageFile] = useState<File | null>(null);
  const pendingQuestionRef = useRef<string | null>(null);
  const sessionKeyRef = useRef<string | null>(null);

  const updateSessionKey = (key: string) => {
    sessionKeyRef.current = key;
  };

  const onAudioSend = async (audioBlob: Blob) => {
    setIsWorking(true);
    // 너무 짧은 음성
    if (audioBlob.size < 10000) {
      addMessage({ role: "assistant", content: "🎤 음성이 너무 짧아요! 다시 말해주세요 😅" });
      setIsWorking(false);
      return;
    }

    try {
      const userTempId = Date.now();
      addMessage({ role: "user", content: ".", tempId: userTempId });
      startDots(userTempId);

      // 1. Whisper API 호출
      const userText = await useWhisper(audioBlob);
      stopDots();
      updateTempMessage(userTempId, { content: userText });

      // 2. assistant 임시 메세지
      const assistantTempId = Date.now() + 1;
      addMessage({ role: "assistant", content: ".", tempId: assistantTempId });
      startDots(assistantTempId);

      // 3. 멀티턴 대화 모드
      const adRes = await generateDialogueRequest(userText, isLogin);
      stopDots();

      if (sessionKeyRef.current !== adRes.session_key) updateSessionKey(adRes.session_key);

      if (!adRes.is_complete) {
        // 3-1. 광고 생성  - 이미지 요청
        if (adRes.type === "ad" && !uploadedImageFile) {
          pendingQuestionRef.current = adRes.next_question;
          setNeedImage(true);
          updateTempMessage(assistantTempId, { content: IMAGE_GUIDE_MESSAGE });
        } else {
          updateTempMessage(assistantTempId, { content: adRes.next_question });
        }
        return;
      }

      // 4. 대화 죵로 멘트 처리
      const content = adRes.final_content
        ? formatChatResponse(adRes.final_content)
        : adRes.last_ment ?? "";
      updateTempMessage(assistantTempId, { content });

      // 5. 광고 - 이미지 생성
      const imagePrompt = adRes.final_content?.image_prompt;
      if (imagePrompt && uploadedImageFile) {
        const imgTempId = Date.now() + 2;
        // 이미지 생성 중 메시지 추가

        addMessage({ role: "assistant", content: "🖼️ 이미지 생성 중...", tempId: imgTempId });

        const imgSrc = await generateSyntheSizeDiffusionRequest(imagePrompt, uploadedImageFile);
        // 이미지 채우기
        updateTempMessage(imgTempId, { content: "", img: imgSrc });
      }

      if (adRes.is_complete) setUploadedImageFile(null);
    } catch (err) {
      addMessage({ role: "assistant", content: "❌ 오류가 발생했습니다. 다시 시도해주세요!" });
      stopDots();
    } finally {
      setIsWorking(false);
    }
  };

  const onImageUpload = async (file: File) => {
    const key = sessionKeyRef.current;
    if (!key) return;

    const imgUrl = URL.createObjectURL(file);
    setUploadedImageFile(file);
    setNeedImage(false);

    await uploadImage(key, file);

    addMessage({ role: "user", content: "", img: imgUrl });

    if (pendingQuestionRef.current) {
      addMessage({ role: "assistant", content: pendingQuestionRef.current });
      pendingQuestionRef.current = null;
    }
  };

  return { messages, needImage, isWorking, onAudioSend, onImageUpload };
}
