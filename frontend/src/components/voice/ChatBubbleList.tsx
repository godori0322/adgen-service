import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useChat, type ChatMessage } from "../../context/ChatContext";
import ShareImageButton from "../common/ShareImageButton";
import SkeletonBubble from "../common/SkeletonBubble";
import BgmSelectBubble from "./BgmSelectBubble";
import CaptionEditor from "./CaptionEditor";
import type { ImageMode } from "./ImageModeSelectorBubble";
import ImageModeSelectorBubble from "./ImageModeSelectorBubble";
import ImageGuideBubble from "./ImageGuideBubble";

export default function ChatBubbleList({
  messages,
  onSelectMode,
  onSelectBgmOption,
  retryProcess,
  onInsertCaption,
  onConfirmPreview,
  onRetryPreview,
  setIsCaptionEditing,
}: {
  messages: ChatMessage[];
  onSelectMode: (mode: ImageMode) => void;
  onSelectBgmOption: (opt: "video" | "image" | "separate") => void;
  retryProcess: () => void;
  onInsertCaption: (choice: boolean, tempId?: number) => void;
  onConfirmPreview: (tempId: number) => void;
  onRetryPreview: () => void;
  setIsCaptionEditing: (value: boolean) => void;
}) {
  const { addMessage, updateTempMessage } = useChat();

  const downloadMedia = async (fileUrl: string, filename: string) => {
    const response = await fetch(fileUrl);
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(objectUrl);
  };

  const handleSave = async (msg: ChatMessage) => {
    try {
      if (msg.video) await downloadMedia(msg.video, `adgen-video-${Date.now()}.mp4`);
      if (msg.img) await downloadMedia(msg.img, `adgen-image-${Date.now()}.png`);
      if (msg.audio) await downloadMedia(msg.audio, `adgen-audio-${Date.now()}.wav`);
    } catch (err) {
      console.error("저장 오류:", err);
      alert("파일 저장 중 오류가 발생했습니다 😢");
    }
  };

  return (
    <div className="mt-4 space-y-3">
      {messages.map((msg, idx) => {
        const isUser = msg.role === "user";

        return (
          <div
            key={idx}
            className={`
              w-fit max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow 
              ${
                isUser
                  ? "ml-auto bg-blue-500 text-white rounded-br-none"
                  : "mr-auto bg-gray-200 text-gray-900 rounded-bl-none"
              }
              ${msg.fail ? "border-red-300 bg-red-50 rounded-xl text-red-700" : ""}
            `}
          >
            {/* 🔥 로딩 */}
            {msg.loading && <SkeletonBubble text={msg.content || "처리 중..."} />}

            {/* ❌ 실패 UI */}
            {!msg.loading && msg.fail && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">❌</span>
                  <span>{msg.content}</span>
                </div>

                <button
                  onClick={() => retryProcess()}
                  className="w-full bg-red-500 hover:bg-red-600 text-white font-semibold py-2 rounded-lg transition-all duration-200 shadow"
                >
                  🔄 다시 시도
                </button>
              </div>
            )}

            {/* 🔥 정상 메시지 UI */}
            {!msg.loading && !msg.fail && (
              <>
                {/* 텍스트 */}
                {msg.content && (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {(msg.content || "").replace(/\\n/g, "\n")}
                  </ReactMarkdown>
                )}
                {msg.imageGuide && <ImageGuideBubble />}
                {/* 오디오 */}
                {msg.audio && (
                  <audio controls className="w-full mt-3 rounded-lg">
                    <source src={msg.audio} type="audio/mpeg" />
                  </audio>
                )}

                {/* 이미지 (생성 결과) */}
                {msg.img && !msg.previewSelect && (
                  <img src={msg.img} alt="generated" className="rounded-lg max-w-full mt-3" />
                )}

                {/* 비디오 */}
                {msg.video && (
                  <video controls className="rounded-lg max-w-full mt-3">
                    <source src={msg.video} />
                  </video>
                )}

                {/* 저장/공유 버튼 */}
                {(msg.img || msg.audio || msg.video) &&
                  !msg.previewSelect &&
                  msg.role === "assistant" && (
                    <div className="flex gap-2 mt-3 justify-center">
                      <ShareImageButton imageUrl={msg.img ?? msg.video ?? ""} />
                      <button
                        onClick={() => handleSave(msg)}
                        className="bg-gray-700 hover:bg-gray-800 text-white rounded-md px-3 py-2 text-sm font-medium shadow mt-2"
                      >
                        ⬇️ 저장
                      </button>
                    </div>
                  )}

                {/* 캡션 삽입 여부 */}
                {msg.captionSelect && (
                  <div className="flex gap-2 mt-2">
                    <button
                      onClick={() => {
                        addMessage({ role: "user", content: "이미지에 문구를 넣을게요 ✍️" });
                        addMessage({
                          role: "assistant",
                          content: "",
                          textData: msg.textData,
                          tempId: Date.now(),
                          captionEditor: true,
                        });
                      }}
                      className="bg-blue-500 text-white px-3 py-1 rounded-lg text-xs"
                    >
                      네! 넣을게요 ✍️
                    </button>

                    <button
                      onClick={() => {
                        addMessage({ role: "user", content: "아니요 괜찮아요 👌" });
                        onInsertCaption(false);
                      }}
                      className="bg-gray-300 text-gray-800 px-3 py-1 rounded-lg text-xs"
                    >
                      아니요 👌
                    </button>
                  </div>
                )}

                {/* 캡션 UI */}
                {msg.captionEditor && (
                  <CaptionEditor
                    textData={msg.textData}
                    onComplete={(finalImg) => {
                      updateTempMessage(msg.tempId!, {
                        captionSelect: false,
                        captionEditor: false,
                        content: "문구 삽입 완료! 🎉",
                        img: finalImg,
                      });
                      setIsCaptionEditing(false);
                    }}
                  />
                )}

                {/* 광고 모드 선택 */}
                {msg.modeSelect && <ImageModeSelectorBubble onSelect={onSelectMode} />}

                {/* BGM 선택 */}
                {msg.bgmSelect && <BgmSelectBubble onSelect={onSelectBgmOption} />}

                {/* segmentation preview 선택 */}
                {msg.previewSelect && (
                  <div className="flex flex-col items-center gap-2 mt-2">
                    {msg.img && <img src={msg.img} className="rounded-lg w-full max-w-xs" />}

                    <div className="flex gap-2 mt-3">
                      {/* 👍 이대로 */}
                      <button
                        className={`
                          px-4 py-2 rounded-lg shadow transition text-white font-semibold bg-green-500
                          ${msg.previewConfirmed ? "ring-4 ring-yellow-300" : "hover:bg-green-600"}
                          ${
                            msg.previewRejected
                              ? "opacity-40 cursor-not-allowed pointer-events-none"
                              : ""
                          }
                        `}
                        disabled={msg.previewConfirmed || msg.previewRejected}
                        onClick={() => onConfirmPreview(msg.tempId!)}
                      >
                        👍 이대로 사용
                      </button>

                      {/* 🔄 다시 */}
                      <button
                        className={`
                        px-4 py-2 rounded-lg shadow transition font-semibold bg-gray-400
                        ${msg.previewRejected ? "ring-4 ring-yellow-300" : "hover:bg-gray-500"}
                        ${
                          msg.previewConfirmed
                            ? "opacity-40 cursor-not-allowed pointer-events-none"
                            : ""
                        }
                      `}
                        disabled={msg.previewConfirmed || msg.previewRejected}
                        onClick={onRetryPreview}
                      >
                        🔄 다시 선택
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}
