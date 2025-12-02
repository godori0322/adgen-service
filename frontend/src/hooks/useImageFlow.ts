// src/hooks/useImageFlow.ts
import { useState } from "react";
import { segmentationPreviewRequest } from "../api/generate";
import { IMAGE_GUIDE_MESSAGE } from "../constants/chat";
import { useChat } from "../context/ChatContext";
import { fileToBase64 } from "../utils/files";

export function useImageFlow() {
  const { messages, addMessage, updateTempMessage } = useChat();

  const [uploadedImageFile, setUploadedImageFile] = useState<File | null>(null);
  const [previewCutImage, setPreviewCutImage] = useState<string | null>(null);
  const [previewMessage, setPreviewMessage] = useState<string | null>(null);
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);

  // 이미지 업로드 시, 누끼 preview만 요청
  const requestPreview = async (file: File) => {
    setIsPreviewLoading(true);
    setUploadedImageFile(file);

    try {
      const base64Img = await fileToBase64(file);

      // 유저가 올린 원본 이미지 버블
      addMessage({
        role: "user",
        content: "",
        img: base64Img,
      });

      const loadingTempId = Date.now();
      addMessage({
        role: "assistant",
        content: `이미지를 분석하고 있어요 🔍\n잠시만 기다려주세요!`,
        tempId: loadingTempId,
        loading: true,
      });

      // 누끼 미리보기 요청
      const res = await segmentationPreviewRequest(file);

      setPreviewCutImage(res.cutout_image);
      setPreviewMessage(res.message);
      setIsPreviewMode(true);

      // 어시스턴트 버블에 누끼 미리보기 + 메시지
      updateTempMessage(loadingTempId, {
        img: res.cutout_image,
        content: (res.message || "").replace(/\./, ".\n\n"),
        previewSelect: true,
        loading: false,
      });
    } catch (err) {
      console.error("이미지 분석 실패:", err);
      const last = messages[messages.length - 1];
      if (last.tempId) {
        updateTempMessage(last.tempId, {
          content: "😢 이미지 분석에 실패했어요! 다시 업로드 해주세요.",
          fail: true,
        });
      }
    } finally {
      setIsPreviewLoading(false);
    }
  };

  // "다시 업로드" 선택 시
  const cancelPreview = () => {
    setUploadedImageFile(null);
    setPreviewCutImage(null);
    setPreviewMessage(null);
    setIsPreviewMode(false);
  };

  // 외부에서 preview 모드만 끄고 싶을 때 사용
  const setPreviewMode = (flag: boolean) => {
    setIsPreviewMode(flag);
  };

  return {
    // 상태
    uploadedImageFile,
    previewCutImage,
    previewMessage,
    isPreviewMode,
    isPreviewLoading,
    // 액션
    requestPreview,
    cancelPreview,
    setPreviewMode,
  };
}
