import { useEffect, useState } from "react";
import {
  getTextListRequest,
  insertCaptionPreviewRequest,
  insertCaptionRequest,
} from "../api/generate";
import { blobToBase64 } from "../utils/files";

export function useCaptionEditor() {
  const [caption, setCaption] = useState<string>("");
  const [width, setWidth] = useState<number>(500);
  const [height, setHeight] = useState<number>(500);
  const [fonts, setFonts] = useState<string[]>([]);
  const [fontMode, setFontMode] = useState<string>("default");
  const [mode, setMode] = useState<"top" | "middle" | "bottom">("bottom");
  const [textColor, setTextColor] = useState({ r: 255, g: 255, b: 255 });
  const [imgFile, setImgFile] = useState<File | null>(null);

  const [previewImg, setPreviewImg] = useState<string>();
  const [loading, setLoading] = useState(false);

  //  폰트 목록 초기화
  useEffect(() => {
    async function loadFonts() {
      const res = await getTextListRequest();
      setFonts(res.fonts || []);
    }
    loadFonts();
  }, []);

  const requestPreview = async () => {
    if (!caption) return;

    setLoading(true);
    try {
      const blob = await insertCaptionPreviewRequest(
        caption,
        fontMode,
        mode,
        width,
        height,
        textColor
      );
      const base64 = await blobToBase64(blob);
      setPreviewImg(base64);
    } catch (error) {
      console.error("Caption preview error:", error);
    } finally {
      setLoading(false);
    }
  };

  const requestApply = async (): Promise<{ success: true; data: string } | { success: false }> => {
    setLoading(true);
    try {
      if (!imgFile) {
        return { success: false };
      }
      const blob = await insertCaptionRequest(
        caption,
        fontMode,
        mode,
        width,
        height,
        textColor,
        imgFile
      );
      const base64 = await blobToBase64(blob);

      return { success: true, data: base64 };
    } catch (error) {
      console.error("Caption apply error:", error);
      return { success: false };
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    requestPreview();
  }, [caption, fontMode, mode, textColor]);

  return {
    setCaption,
    fonts,
    fontMode,
    setFontMode,
    mode,
    setMode,
    previewImg: previewImg ?? undefined,
    loading,
    setWidth,
    setHeight,
    textColor,
    setTextColor,
    setImgFile,
    requestApply,
  };
}
