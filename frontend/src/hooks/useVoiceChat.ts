// src/hooks/useVoiceChat.ts
import { useEffect, useRef, useState } from "react";
import { adsGenerateRequest, generateDialogueRequest, uploadImage } from "../api/generate";
import type { ImageMode } from "../components/voice/ImageModeSelectorBubble";
import { IMAGE_GUIDE_MESSAGE } from "../constants/chat";
import { useAuth } from "../context/AuthContext";
import { useChat } from "../context/ChatContext";
import { formatChatResponse } from "../utils/chatFormatter";
import { blobToFile, fileToBase64 } from "../utils/files";
import { useDotsAnimation } from "./useDotsAnimation";
import { useImageFlow } from "./useImageFlow";
import { useWhisper } from "./useWhisper";

export function useVoiceChat() {
  const { isLogin } = useAuth();
  const { messages, addMessage, updateTempMessage } = useChat();

  const {
    requestPreview,
    uploadedImageFile,
    isPreviewMode,
    isPreviewLoading,
    cancelPreview,
    setPreviewMode,
  } = useImageFlow();

  const [isWorking, setIsWorking] = useState(false);
  const { startDots, stopDots } = useDotsAnimation();
  const [needImage, setNeedImage] = useState(false);
  const [imageMode, setImageMode] = useState<ImageMode | null>(null);
  const [isCaptionEditing, setIsCaptionEditing] = useState(false);
  const [hasShownImageGuide, setHasShownImageGuide] = useState(false);

  const [needBgmChoice, setNeedBgmChoice] = useState(false);
  const pendingQuestionRef = useRef<string | null>(null);
  const sessionKeyRef = useRef<string | null>(null);
  const userSelectBgmRef = useRef<"video" | "image" | "separate" | null>(null);
  const isResetRef = useRef(false);

  const imagePromptRef = useRef<string | null>(null);
  const bgmPromptRef = useRef<string | null>(null);
  const contentRef = useRef<any | null>(null);

  const updateSessionKey = (key: string) => {
    sessionKeyRef.current = key;
  };

  useEffect(() => {
    resetChatFlow();
  }, []);

  // 이미지 or 동영상 생성
  const processImageOrVideo = async () => {
    const mode = userSelectBgmRef.current;
    if (
      !uploadedImageFile ||
      !imageMode ||
      !imagePromptRef.current ||
      !bgmPromptRef.current ||
      !mode
    )
      return;

    const msgId = Date.now();
    addMessage({
      role: "assistant",
      tempId: msgId,
      loading: true,
      content:
        mode === "video"
          ? "🎬 동영상 생성 중..."
          : mode === "image"
          ? "🖼️ 이미지 생성 중..."
          : "이미지 및 음원 생성 중...",
    });

    try {
      const uploadImageBase64 = await fileToBase64(uploadedImageFile);
      const result = await adsGenerateRequest(
        contentRef.current,
        uploadImageBase64,
        imageMode,
        mode,
        imagePromptRef.current,
        bgmPromptRef.current
      );

      const baseUrl = import.meta.env.VITE_MINIO_ENDPOINT ?? "";
      const imageUrl = result.image_url ? baseUrl + result.image_url : null;
      const videoUrl = result.video_url ? baseUrl + result.video_url : null;
      const audioUrl = result.audio_url ? baseUrl + result.audio_url : null;

      updateTempMessage(msgId, {
        loading: false,
        content:
          mode === "video"
            ? "🎬 동영상 생성 완료!"
            : mode === "image"
            ? "🖼️ 이미지 생성 완료!"
            : "🎶 이미지 및 음악 생성 완료!",
        ...(mode === "video"
          ? { video: videoUrl }
          : mode === "image"
          ? { img: imageUrl }
          : { img: imageUrl, audio: audioUrl }),
      });

      if (mode === "video") {
        addMessage({
          role: "assistant",
          content: `대화가 종료되었습니다 😊\n원하시면 음성으로 새로운 광고를 시작해주세요!`,
        });
        resetChatFlow();
        return;
      }

      const tempId = Date.now();
      const imgObj = new Image();
      if (!imageUrl) return;
      imgObj.src = imageUrl;

      imgObj.onerror = () => {
        addMessage({
          role: "assistant",
          content: "이미지 로딩에 실패했어요. 다시 시도해주세요 😢",
          fail: true,
        });
      };

      imgObj.onload = async () => {
        if (contentRef.current) {
          const response = await fetch(imageUrl);
          const blob = await response.blob();
          const resultFile = blobToFile(blob, "generated_image.png");

          addMessage({
            tempId,
            role: "assistant",
            content: "📝 생성된 광고 문구를 이미지에 넣어볼까요?",
            captionSelect: true,
            textData: {
              caption: contentRef.current.caption,
              imgWidth: imgObj.width,
              imgHeight: imgObj.height,
              file: resultFile,
            },
          });
          setIsCaptionEditing(true);
        }
      };
    } catch (err) {
      console.error(err);
      updateTempMessage(msgId, {
        content:
          mode === "video"
            ? "동영상 생성 실패! 다시 시도해주세요."
            : "이미지 생성 실패! 다시 시도해주세요.",
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
    await processImageOrVideo();
  };

  const onAudioSend = async (audioBlob: Blob) => {
    if (isResetRef.current) {
      isResetRef.current = false;
    }
    if (isPreviewMode) {
      // 누끼 확인 중에는 음성 입력 막기
      addMessage({
        role: "assistant",
        content: "먼저 현재 이미지 사용 여부를 선택해 주세요 😊",
      });
      return;
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

      if (adRes.final_content) {
        contentRef.current = {
          idea: adRes.final_content.idea,
          caption: adRes.final_content.caption,
          hashtags: adRes.final_content.hashtags,
        };
      }

      // Diffusion 이미지 생성 단계
      imagePromptRef.current = adRes.final_content?.image_prompt || null;
      bgmPromptRef.current = adRes.final_content?.bgm_prompt || null;

      if (imagePromptRef.current && userSelectBgmRef.current) {
        await processImageOrVideo();
      }
    } catch (err) {
      console.error(err);
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
    // 백엔드 uploadImage 호출 X, 우선 누끼 preview만
    setNeedImage(false);
    await requestPreview(file);
  };

  const onSelectMode = (mode: ImageMode) => {
    if (isPreviewMode) {
      // 아직 이미지 사용 여부 안 정했는데 모드부터 선택하는 경우 방지
      addMessage({
        role: "assistant",
        content: "이미지 사용 여부를 먼저 결정해 주세요 😊",
      });
      return;
    }

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
    addMessage({
      role: "assistant",
      content: IMAGE_GUIDE_MESSAGE,
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
      content: `대화가 종료되었습니다 😊\n원하시면 음성으로 새로운 광고를 시작해주세요!`,
    });

    resetChatFlow();
  };

  const lastMsg = messages[messages.length - 1];

  const isUiBlocking =
    isWorking ||
    isPreviewMode || // 🔥 preview 중엔 입력 막기
    needImage ||
    isCaptionEditing ||
    isPreviewMode ||
    isPreviewLoading ||
    (lastMsg?.modeSelect && userSelectBgmRef.current == null) ||
    (lastMsg?.bgmSelect && imageMode == null);

  const resetChatFlow = () => {
    isResetRef.current = true;

    setNeedImage(false);
    setNeedBgmChoice(false);
    setImageMode(null);
    setIsWorking(false);

    setPreviewMode(false);

    sessionKeyRef.current = null;
    pendingQuestionRef.current = null;
    userSelectBgmRef.current = null;
    imagePromptRef.current = null;
    bgmPromptRef.current = null;
    contentRef.current = null;
  };

  // 🔥 Preview 승인 → 다음 단계 이동
  const onConfirmPreview = async (tempId: number) => {
    if (!sessionKeyRef.current || !uploadedImageFile) {
      console.error("업로드할 이미지 또는 세션 키가 없습니다.");
      return;
    }
    setPreviewMode(false);

    updateTempMessage(tempId, {
      previewConfirmed: true,
      previewRejected: false,
    });

    addMessage({ role: "user", content: "이 이미지 사용할게요!" });

    // 업로드 로딩 메시지 추가
    const loadingId = Date.now();
    addMessage({
      role: "assistant",
      tempId: loadingId,
      loading: true,
      content: "이미지를 업로드하고 있어요 📤☁️",
    });

    try {
      await uploadImage(sessionKeyRef.current, uploadedImageFile);

      // 로딩 메시지 종료
      updateTempMessage(loadingId, {
        loading: false,
        content: "업로드 완료! 🎉",
      });

      // 다음 단계 진행
      addMessage({
        role: "assistant",
        tempId: Date.now() + 1,
        content: "좋아요! 어떤 방식의 광고를 원하시나요? 😄",
        modeSelect: true,
      });
    } catch (err) {
      console.error("이미지 업로드 실패:", err);
      updateTempMessage(loadingId, {
        loading: false,
        fail: true,
        content: "업로드 실패! 😢 다시 시도해 주세요",
      });
    }
  };

  // 🔁 Preview 취소 → 다시 업로드 요청
  const onRetryPreview = () => {
    cancelPreview();
    const last = messages[messages.length - 1];
    if (last?.tempId) {
      updateTempMessage(last.tempId, {
        previewRejected: true,
        previewConfirmed: false,
      });
    }

    setNeedImage(true);
  };

  return {
    messages,
    needImage,
    needBgmChoice,
    isWorking,
    isPreviewMode,
    cancelPreview,
    onAudioSend,
    onImageUpload,
    onSelectMode,
    onSelectBgmOption,
    retryProcess,
    resetChatFlow,
    onInsertCaption,
    isCaptionEditing,
    isUiBlocking,
    uploadedImageFile,
    onConfirmPreview,
    onRetryPreview,
    setIsCaptionEditing,
  };
}
