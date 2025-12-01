// src/hooks/useVoiceChat.ts
import { useEffect, useRef, useState } from "react";
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
import { blobToBase64, blobToFile, fileToBase64 } from "../utils/files";
import { useDotsAnimation } from "./useDotsAnimation";
import { useWhisper } from "./useWhisper";

export function useVoiceChat() {
  const { isLogin } = useAuth();
  const [isWorking, setIsWorking] = useState(false);
  const { messages, addMessage, updateTempMessage } = useChat();
  const { startDots, stopDots } = useDotsAnimation();
  const [needImage, setNeedImage] = useState(false);
  const [uploadedImageFile, setUploadedImageFile] = useState<File | null>(null);
  const [imageMode, setImageMode] = useState<ImageMode | null>(null);
  const [isCaptionEditing, setIsCaptionEditing] = useState(false);

  const [needBgmChoice, setNeedBgmChoice] = useState(false);
  const pendingQuestionRef = useRef<string | null>(null);
  const sessionKeyRef = useRef<string | null>(null);
  const userSelectBgmRef = useRef<"video" | "image" | "separate" | null>(null);
  const isResetRef = useRef(false);

  const imagePromptRef = useRef<string | null>(null);
  const bgmPromptRef = useRef<string | null>(null);
  const captionTextRef = useRef<string | null>(null);

  const updateSessionKey = (key: string) => {
    sessionKeyRef.current = key;
  };
  useEffect(() => {
    resetChatFlow();
  }, []);
  // 이미지 or 동영상 생성
  const processImageOrVideo = async () => {
    const mode = userSelectBgmRef.current;
    if (!uploadedImageFile || !imageMode || !imagePromptRef.current || !mode) return;

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

      const base64 = await blobToBase64(blob, mode === "video" ? "video" : "image");

      updateTempMessage(msgId, {
        content: mode === "video" ? "🎬 동영상 생성 완료!" : "🖼️ 이미지 생성 완료!",
        ...(mode === "video" ? { video: base64 } : { img: base64 }),
      });

      if (mode === "image") {
        const tempId = Date.now();
        const imgObj = new Image();
        imgObj.src = base64;
        const resultFile = blobToFile(blob, "generated_image.png");
        imgObj.onload = () => {
          if (captionTextRef.current) {
            addMessage({
              tempId,
              role: "assistant",
              content: "📝 생성된 광고 문구를 이미지에 넣어볼까요?",
              captionSelect: true,
              textData: {
                caption: captionTextRef.current,
                imgWidth: imgObj.width,
                imgHeight: imgObj.height,
                file: resultFile,
              },
            });
            setIsCaptionEditing(true);
          }
        };
      }

      // 따로일 경우 → 이미지 완료 후 음악 생성
      if (mode === "separate") {
        await processAudio();
      }
    } catch (err) {
      updateTempMessage(msgId, {
        content:
          mode === "video"
            ? "동영상 생성 실패! 다시 시도해주세요."
            : "이미지 생성 실패! 다시 시도해주세요.",
        fail: true,
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
      const base64Audio = await blobToBase64(audioBlob, "audio");

      updateTempMessage(msgId, {
        content: "🎶 음악 생성 완료!",
        audio: base64Audio,
      });
    } catch {
      updateTempMessage(msgId, {
        content: "음악 생성 실패! 다시 시도해주세요.",
        fail: true,
      });
    }
  };

  const retryProcess = async () => {
    const mode = userSelectBgmRef.current;

    if (!mode) {
      const last = messages[messages.length - 1];
      if (last?.tempId) {
        updateTempMessage(last.tempId, {
          content: "죄송합니다. 다시 대화를 시작해주세요 😥",
          img: undefined,
          video: undefined,
          audio: undefined,
          modeSelect: false,
          bgmSelect: false,
          fail: false,
        });
      }

      resetChatFlow();
      return;
    }

    if (mode === "separate") {
      await processAudio();
    } else {
      await processImageOrVideo();
    }
  };

  const onAudioSend = async (audioBlob: Blob) => {
    if (isResetRef.current) {
      isResetRef.current = false;
    }
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
      // 1) 유저 버블 로딩
      const userTempId = Date.now();
      addMessage({ role: "user", content: ".", tempId: userTempId });
      startDots(userTempId);

      // Whisper 변환
      const userText = await useWhisper(audioBlob);
      stopDots(userTempId); // ✅ 해당 버블 로딩만 종료

      if (!userText || userText.trim() === "") {
        updateTempMessage(userTempId, {
          content: "🎤 음성이 잘 인식되지 않았어요! 다시 한 번 말씀해주세요 😅",
        });
        setIsWorking(false);
        return;
      }
      updateTempMessage(userTempId, { content: userText });

      // 2) 어시스턴트 버블 로딩
      const assistantTempId = Date.now() + 1;
      addMessage({ role: "assistant", content: ".", tempId: assistantTempId });
      startDots(assistantTempId);

      // Dialogue API
      const adRes = await generateDialogueRequest(userText, isLogin);
      stopDots(assistantTempId); // ✅ 이 버블 로딩 종료

      pendingQuestionRef.current = adRes.next_question;
      if (sessionKeyRef.current !== adRes.session_key) updateSessionKey(adRes.session_key);

      // 리턴 타입 선택
      if (!userSelectBgmRef.current && adRes.type === "ad" && !isResetRef.current) {
        setNeedBgmChoice(true);
        updateTempMessage(assistantTempId, {
          content: "🎬 어떤 방식의 광고를 원하시나요?",
          bgmSelect: true,
        });
        return;
      }

      // 이미지 요청
      if (!uploadedImageFile && adRes.type === "ad" && !isResetRef.current) {
        setNeedImage(true);
        updateTempMessage(assistantTempId, {
          content: IMAGE_GUIDE_MESSAGE,
        });
        return;
      }

      // 다음 질문 표시
      if (pendingQuestionRef.current !== null) {
        const nextQ = pendingQuestionRef.current.trim();
        pendingQuestionRef.current = null;

        if (nextQ.length > 0) {
          updateTempMessage(assistantTempId, {
            content: nextQ,
          });
        } else {
          updateTempMessage(assistantTempId, {
            content: "대화가 종료되었습니다 😊\n원하시면 새로운 광고를 시작해볼까요?",
          });
          resetChatFlow();
        }

        return;
      }

      // 최종 문구 처리
      const content = adRes.final_content
        ? formatChatResponse(adRes.final_content)
        : adRes.last_ment ?? "";
      updateTempMessage(assistantTempId, { content });

      if (adRes.final_content?.caption) {
        captionTextRef.current = adRes.final_content.caption;
      }

      // Diffusion 이미지 생성 단계
      imagePromptRef.current = adRes.final_content?.image_prompt || null;
      bgmPromptRef.current = adRes.final_content?.bgm_prompt || null;

      if (imagePromptRef.current && userSelectBgmRef.current) {
        await processImageOrVideo();
      }
    } catch (err) {
      addMessage({
        role: "assistant",
        content: "❌ 오류가 발생했습니다. 다시 시도해주세요!",
      });
      stopDots(); // ✅ 혹시 남아있을지 모르는 로딩 전부 정리
    } finally {
      setIsWorking(false);
    }
  };

  const onImageUpload = async (file: File) => {
    const key = sessionKeyRef.current;
    if (!key) return;

    const base64Img = await fileToBase64(file);

    setUploadedImageFile(file);
    setNeedImage(false);

    try {
      await uploadImage(key, file);
    } catch (err) {
      console.error("이미지 업로드 실패:", err);
    }

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
    if (pendingQuestionRef.current) {
      addMessage({
        role: "assistant",
        content: pendingQuestionRef.current,
      });
      pendingQuestionRef.current = null;
    }
  };

  const onSelectBgmOption = async (option: "video" | "image" | "separate") => {
    if (isResetRef.current) return;
    userSelectBgmRef.current = option;
    setNeedBgmChoice(false);

    addMessage({
      role: "user",
      content:
        option === "video"
          ? "🎬 동영상(릴스)으로 만들어주세요!"
          : option === "image"
          ? "📸 이미지만 생성할게요!"
          : "🎨 이미지 + 🎵 음악을 따로 생성할게요!",
    });

    setNeedImage(true);
  };

  const onInsertCaption = async (choice: boolean, tempId?: number) => {
    setIsCaptionEditing(false);
    setNeedImage(false);

    if (!choice) {
      if (tempId) {
        updateTempMessage(tempId, {
          role: "assistant",
          content: "문구 삽입 없이 완료되었어요 😊",
        });
      }
    } else {
      addMessage({
        role: "assistant",
        content: "문구 삽입 없이 완료되었어요 😊",
      });
    }

    // 종료 안내 멘트
    addMessage({
      role: "assistant",
      content: "대화가 종료되었습니다 😊\n원하시면 음성으로 새로운 광고를 시작해주세요!",
    });

    resetChatFlow();
  };
  const lastMsg = messages[messages.length - 1];

  const isUiBlocking =
    isWorking ||
    needImage ||
    isCaptionEditing ||
    (lastMsg?.modeSelect && userSelectBgmRef.current == null) ||
    (lastMsg?.bgmSelect && imageMode == null);

  const resetChatFlow = () => {
    isResetRef.current = true;

    setNeedImage(false);
    setNeedBgmChoice(false);
    setUploadedImageFile(null);
    setImageMode(null);
    setIsWorking(false);

    sessionKeyRef.current = null;
    pendingQuestionRef.current = null;
    userSelectBgmRef.current = null;
    imagePromptRef.current = null;
    bgmPromptRef.current = null;
    captionTextRef.current = null;
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
    resetChatFlow,
    onInsertCaption,
    isUiBlocking,
  };
}
