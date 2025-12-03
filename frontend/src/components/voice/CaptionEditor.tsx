import { useEffect, useState } from "react";
import { useCaptionEditor } from "../../hooks/useCaptionEditor";
import AlertModal from "../common/AlertModal";
import ColorSelector from "../common/ColorSelector";

interface Props {
  textData: any;
  onComplete: (finalImg: string) => void;
}

export default function CaptionEditor({ textData, onComplete }: Props) {
  const {
    fonts,
    fontMode,
    mode,
    previewImg,
    setCaption,
    setFontMode,
    setMode,
    setWidth,
    setHeight,
    textColor,
    loading,
    setTextColor,
    setImgFile,
    requestApply,
  } = useCaptionEditor();
  const ratio = (textData.imgHeight / textData.imgWidth) * 100;
  const [alert, setAlert] = useState<string | null>(null);
  useEffect(() => {
    setWidth(textData.imgWidth);
    setHeight(textData.imgHeight);
    setCaption(textData.caption);
    setImgFile(textData.file);
  }, [textData]);
  const positions = [
    { value: "top", label: "위" },
    { value: "middle", label: "중간" },
    { value: "bottom", label: "아래" },
  ];
  return (
    <>
      <div className="p-5 mt-2 space-y-6 bg-white rounded-2xl shadow-md border border-gray-100">
        {/* 📌 이미지 프리뷰 */}
        <div
          className="relative w-full rounded-xl overflow-hidden shadow-inner bg-gray-200"
          style={{ paddingBottom: `${ratio}%` }}
        >
          {!loading ? (
            <img
              src={previewImg}
              alt="preview"
              className="absolute top-0 left-0 w-full h-full object-contain transition-all"
            />
          ) : (
            <div className="absolute inset-0 bg-gray-300 animate-pulse grid place-items-center text-gray-500">
              미리보기 로딩...
            </div>
          )}
        </div>

        {/* 📌 옵션 영역 */}
        <div className="flex flex-col sm:flex-row gap-6">
          {/* 좌측: 폰트 / 위치 */}
          <div className="flex-1 flex flex-col gap-6">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-gray-700">폰트 선택</label>
              <select
                className="w-full p-3 rounded-lg border border-gray-300 text-gray-800 font-medium focus:ring-2 focus:ring-blue-500"
                value={fontMode}
                onChange={(e) => setFontMode(e.target.value)}
              >
                {fonts.map((font) => (
                  <option key={font} value={font}>
                    {font}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-gray-700">텍스트 위치</label>
              <div className="grid grid-cols-3 gap-2">
                {positions.map((position) => (
                  <button
                    key={position.value}
                    onClick={() => setMode(position.value as any)}
                    className={`py-2 rounded-lg border text-sm font-semibold transition-all
                      ${
                        mode === position.value
                          ? "bg-blue-600 text-white shadow-md scale-105"
                          : "bg-white text-gray-700 hover:bg-blue-50"
                      }`}
                  >
                    {position.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 우측: 텍스트 색상 */}
          <div className="flex-1 flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-gray-700">텍스트 색상</label>
            <ColorSelector color={textColor} onChange={setTextColor} />
          </div>
        </div>

        {/* 📌 버튼 영역 (항상 아래 풀폭) */}
        <div className="pt-2">
          <button
            onClick={async () => {
              const res = await requestApply();
              if (!res.success) {
                setAlert("문구 삽입에 실패했어요! 다시 시도해주세요 😥");
                return;
              }
              onComplete(res.data);
            }}
            className="w-full bg-green-500 hover:bg-green-600 text-white px-4 py-3 rounded-xl font-bold shadow-md transition"
          >
            캡션 적용하기 💡
          </button>
        </div>
      </div>

      {/* 오류 Modal */}
      {alert && <AlertModal onClose={() => setAlert(null)} title="오류 발생" message={alert} />}
    </>
  );
}
