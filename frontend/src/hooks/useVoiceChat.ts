import { useRef, useState } from "react";
import { generateDialogueRequest, generateDiffusionRequest, uploadImage } from "../api/generate";
import type { ImageMode } from "../components/voice/ImageModeSelectorBubble";
import { IMAGE_GUIDE_MESSAGE } from "../constants/chat";
import { useAuth } from "../context/AuthContext";
import { useChat } from "../context/ChatContext";
import { formatChatResponse } from "../utils/chatFormatter";
import { useDotsAnimation } from "./useDotsAnimation";
import { useWhisper } from "./useWhisper";

export interface ChatMessage {
  role: "user" | "assistant";
  content?: string;
  img?: string;
  tempId?: number;
  parsed?: {
    idea: string;
    caption: string;
    hashtags?: string[];
  };
  modeSelect?: boolean;
}

export function useVoiceChat() {
  const { isLogin } = useAuth();
  const [isWorking, setIsWorking] = useState(false);
  const { messages, addMessage, updateTempMessage } = useChat();
  const { startDots, stopDots } = useDotsAnimation();
  const [needImage, setNeedImage] = useState(false);
  const [uploadedImageFile, setUploadedImageFile] = useState<File | null>(null);
  const [imageMode, setImageMode] = useState<ImageMode | null>(null);
  const pendingQuestionRef = useRef<string | null>(null);
  const sessionKeyRef = useRef<string | null>(null);

  const updateSessionKey = (key: string) => {
    sessionKeyRef.current = key;
  };

  const onAudioSend = async (audioBlob: Blob) => {
    setIsWorking(true);

    if (audioBlob.size < 10000) {
      addMessage({
        role: "assistant",
        content: "🎤 음성이 너무 짧아요! 다시 말해주세요 😅",
      });
      setIsWorking(false);
      return;
    }

    try {
      const userTempId = Date.now();
      addMessage({ role: "user", content: ".", tempId: userTempId });
      startDots(userTempId);

      // Whisper 변환
      const userText = await useWhisper(audioBlob);
      stopDots();
      updateTempMessage(userTempId, { content: userText });

      // Assistant 임시 버블
      const assistantTempId = Date.now() + 1;
      addMessage({ role: "assistant", content: ".", tempId: assistantTempId });
      startDots(assistantTempId);

      // Dialogue API
      const adRes = await generateDialogueRequest(userText, isLogin);
      stopDots();

      if (sessionKeyRef.current !== adRes.session_key) updateSessionKey(adRes.session_key);

      // 이미지 요청 단계
      if (!adRes.is_complete) {
        if (adRes.type === "ad" && !uploadedImageFile) {
          pendingQuestionRef.current = adRes.next_question;
          setNeedImage(true);
          updateTempMessage(assistantTempId, {
            content: IMAGE_GUIDE_MESSAGE,
          });
          return;
        }

        updateTempMessage(assistantTempId, {
          content: adRes.next_question,
        });
        return;
      }

      // 최종 문구 처리
      const content = adRes.final_content
        ? formatChatResponse(adRes.final_content)
        : adRes.last_ment ?? "";
      updateTempMessage(assistantTempId, { content });

      // Diffusion 이미지 생성 단계
      const imagePrompt = adRes.final_content?.image_prompt;
      if (imagePrompt && uploadedImageFile) {
        if (!imageMode) return;

        const imgTempId = Date.now() + 2;
        addMessage({
          role: "assistant",
          content: "🖼️ 이미지 생성 중...",
          tempId: imgTempId,
        });

        const imgSrc = await generateDiffusionRequest(imagePrompt, uploadedImageFile, imageMode);

        updateTempMessage(imgTempId, {
          content: "",
          img: imgSrc,
          parsed: adRes.final_content,
        });
      }

      if (adRes.is_complete) setUploadedImageFile(null);
    } catch (err) {
      addMessage({
        role: "assistant",
        content: "❌ 오류가 발생했습니다. 다시 시도해주세요!",
      });
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

    addMessage({
      role: "assistant",
      content: "어떤 방식으로 이미지를 합성할까요?",
      modeSelect: true,
    });
  };

  const onSelectMode = (mode: ImageMode) => {
    setImageMode(mode);

    addMessage({
      role: "user",
      content: `👉 ${mode} 모드 선택!`,
    });

    if (pendingQuestionRef.current) {
      addMessage({
        role: "assistant",
        content: pendingQuestionRef.current,
      });
      pendingQuestionRef.current = null;
    }
  };

  return { messages, needImage, isWorking, onAudioSend, onImageUpload, onSelectMode };
}
