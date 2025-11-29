import { useRef, useState } from "react";
import {
  generateAudioRaw,
  generateDialogueRequest,
  generateSyntheSizeDiffusionRequest,
  uploadImage,
} from "../api/generate";
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
  video?: string;
  audio?: string;
  tempId?: number;
  modeSelect?: boolean;
  bgmSelect?: boolean;
  retryType?: "image" | "video" | "audio";
}

export function useVoiceChat() {
  const { isLogin } = useAuth();
  const [isWorking, setIsWorking] = useState(false);
  const { messages, addMessage, updateTempMessage } = useChat();
  const { startDots, stopDots } = useDotsAnimation();
  const [needImage, setNeedImage] = useState(false);
  const [uploadedImageFile, setUploadedImageFile] = useState<File | null>(null);
  const [imageMode, setImageMode] = useState<ImageMode | null>(null);
  const [needBgmChoice, setNeedBgmChoice] = useState(false);
  const pendingQuestionRef = useRef<string | null>(null);
  const sessionKeyRef = useRef<string | null>(null);
  const userSelectBgmRef = useRef<"video" | "image" | "separate" | null>(null);

  const imagePromptRef = useRef<string | null>(null);
  const bgmPromptRef = useRef<string | null>(null);

  const updateSessionKey = (key: string) => {
    sessionKeyRef.current = key;
  };

  const toBase64 = (blob: Blob, type: "image" | "video" | "audio") => {
    return new Promise<string>((resolve) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result as string);
      reader.readAsDataURL(
        new File([blob], `file.${type === "image" ? "png" : type === "video" ? "mp4" : "mp3"}`, {
          type: blob.type,
        })
      );
    });
  };
  // 이미지 or 동영상 생성
  const processImageOrVideo = async (mode: "image" | "video" | "separate") => {
    if (!uploadedImageFile || !imageMode || !imagePromptRef.current) return;

    const msgId = Date.now();
    addMessage({
      role: "assistant",
      tempId: msgId,
      content: mode === "video" ? "🎬 동영상 생성 중..." : "🖼️ 이미지 생성 중...",
    });

    try {
      const blob = await generateSyntheSizeDiffusionRequest(
        imagePromptRef.current,
        uploadedImageFile,
        imageMode,
        mode === "video" ? bgmPromptRef.current! : undefined
      );

      if (!blob) throw new Error("Blob empty");

      const base64 = await toBase64(blob, mode === "video" ? "video" : "image");

      updateTempMessage(msgId, {
        content: mode === "video" ? "🎬 동영상 생성 완료!" : "🖼️ 이미지 생성 완료!",
        ...(mode === "video" ? { video: base64 } : { img: base64 }),
      });

      // 🎨+🎵 따로일 경우 → 이미지 완료 후 음악 생성
      if (mode === "separate") {
        await processAudio();
      }
    } catch (err) {
      updateTempMessage(msgId, {
        content:
          mode === "video"
            ? "동영상 생성 실패! 다시 시도해주세요."
            : "이미지 생성 실패! 다시 시도해주세요.",
        retryType: mode === "video" ? "video" : "image",
      });
    } finally {
      setUploadedImageFile(null); // 다음 업로드 대기
    }
  };
  // 음원 생성
  const processAudio = async () => {
    if (!bgmPromptRef.current) return;

    const msgId = Date.now();
    addMessage({
      role: "assistant",
      tempId: msgId,
      content: "🎵 음악 생성 중...",
    });

    try {
      const audioBlob = await generateAudioRaw(bgmPromptRef.current);
      const base64Audio = await toBase64(audioBlob, "audio");

      updateTempMessage(msgId, {
        content: "🎶 음악 생성 완료!",
        audio: base64Audio,
      });
    } catch {
      updateTempMessage(msgId, {
        content: "음악 생성 실패! 다시 시도해주세요.",
        retryType: "audio",
      });
    }
  };

  const retryProcess = async (type: "image" | "video" | "audio") => {
    if (type === "image") {
      await processImageOrVideo("image");
    } else if (type === "video") {
      await processImageOrVideo("video");
    } else if (type === "audio") {
      await processAudio();
    }
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
      if (!userText || userText.trim() === "") {
        updateTempMessage(userTempId, {
          content: "🎤 음성이 잘 인식되지 않았어요! 다시 한 번 말씀해주세요 😅",
        });
        setIsWorking(false);
        return;
      }
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

      imagePromptRef.current = adRes.final_content?.image_prompt || null;
      bgmPromptRef.current = adRes.final_content?.bgm_prompt || null;

      if (bgmPromptRef.current!) {
        setNeedBgmChoice(true);
        addMessage({
          role: "assistant",
          content: `🖼️ 이미지와 함께 배경 음악도 만들어드릴까요?`,
          bgmSelect: true,
        });
        return;
      }
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

  const fileToBase64 = (file: File): Promise<string> =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });

  const onImageUpload = async (file: File) => {
    const key = sessionKeyRef.current;
    if (!key) return;

    const base64Img = await fileToBase64(file);

    setUploadedImageFile(file);
    setNeedImage(false);

    await uploadImage(key, file);

    addMessage({ role: "user", content: "", img: base64Img });

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

    const lastMsg = messages[messages.length - 1];
    if (lastMsg?.modeSelect && lastMsg.tempId) {
      updateTempMessage(lastMsg.tempId, { modeSelect: false });
    }

    if (pendingQuestionRef.current) {
      addMessage({
        role: "assistant",
        content: pendingQuestionRef.current,
      });
      pendingQuestionRef.current = null;
    }
  };

  const onSelectBgmOption = async (option: "video" | "image" | "separate") => {
    userSelectBgmRef.current = option;
    setNeedBgmChoice(false);

    addMessage({
      role: "user",
      content:
        option === "video"
          ? "🎬 동영상으로 만들어주세요!"
          : option === "image"
          ? "📸 이미지만 생성할게요!"
          : "🎨 이미지 + 🎵 음악을 따로 생성할게요!",
    });

    const lastMsg = messages[messages.length - 1];
    if (lastMsg?.bgmSelect && lastMsg.tempId) {
      updateTempMessage(lastMsg.tempId, { bgmSelect: false });
    }

    await processImageOrVideo(option);
  };

  return {
    messages,
    needImage,
    needBgmChoice,
    isWorking,
    onAudioSend,
    onImageUpload,
    onSelectMode,
    onSelectBgmOption,
    retryProcess,
  };
}
