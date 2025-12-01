import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useChat, type ChatMessage } from "../../context/ChatContext";
import ShareImageButton from "../common/ShareImageButton";
import BgmSelectBubble from "./BgmSelectBubble";
import CaptionEditor from "./CaptionEditor";
import type { ImageMode } from "./ImageModeSelectorBubble";
import ImageModeSelectorBubble from "./ImageModeSelectorBubble";

export default function ChatBubbleList({
  messages,
  onSelectMode,
  onSelectBgmOption,
  retryProcess,
  onInsertCaption,
}: {
  messages: ChatMessage[];
  onSelectMode: (mode: ImageMode) => void;
  onSelectBgmOption: (opt: "video" | "image" | "separate") => void;
  retryProcess: () => void;
  onInsertCaption: (choice: boolean, tempId?: number) => void;
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
      if (msg.video) {
        await downloadMedia(msg.video, `adgen-video-${Date.now()}.mp4`);
      }

      if (msg.img) {
        await downloadMedia(msg.img, `adgen-image-${Date.now()}.png`);
      }

      if (msg.audio) {
        await downloadMedia(msg.audio, `adgen-audio-${Date.now()}.wav`);
      }
    } catch (err) {
      console.error("저장 오류:", err);
      alert("파일 저장 중 오류가 발생했습니다 😢");
    }
  };

  return (
    <div className="mt-4 space-y-3">
      {messages.map((msg, idx) => (
        <div
          key={idx}
          className={`
            w-fit max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow 
            ${
              msg.role === "user"
                ? "ml-auto bg-blue-500 text-white rounded-br-none"
                : "mr-auto bg-gray-200 text-gray-900 rounded-bl-none"
            }
            ${msg.fail ? "border-red-300 bg-red-50 rounded-xl text-red-700" : ""}
          `}
        >
          {/* 실패 메시지 */}
          {msg.fail ? (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">❌</span>
                <span>{msg.content}</span>
              </div>
              <button
                onClick={() => retryProcess()}
                className="w-full bg-red-500 hover:bg-red-600 text-white font-semibold 
                 py-2 rounded-lg transition-all duration-200 shadow"
              >
                🔄 다시 시도
              </button>
            </div>
          ) : (
            <>
              {/* 텍스트 */}
              {msg.content && (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {(msg.content || "").replace(/\\n/g, "\n")}
                </ReactMarkdown>
              )}

              {/* 오디오 */}
              {msg.audio && (
                <audio controls className="w-full mt-3 rounded-lg">
                  <source src={msg.audio} type="audio/mpeg" />
                </audio>
              )}

              {/* 이미지 */}
              {msg.img && (
                <img src={msg.img} alt="생성된 이미지" className="rounded-lg max-w-full mt-3" />
              )}

              {/* 비디오 */}
              {msg.video && (
                <video controls className="rounded-lg max-w-full mt-3">
                  <source src={msg.video} />
                </video>
              )}

              {/* 저장/공유 버튼 (Assistant 메시지일 때만) */}
              {(msg.img || msg.audio || msg.video) && msg.role === "assistant" && (
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

              {/* 캡션 삽입 여부 선택 */}
              {msg.captionSelect && (
                <div className="flex gap-2 mt-2">
                  <button
                    onClick={() => {
                      addMessage({ content: "이미지에 문구를 넣을게요 ✍️", role: "user" });
                      addMessage({
                        role: "assistant",
                        content: "",
                        textData: msg.textData || { caption: "" },
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
                      addMessage({
                        content: "아니요 괜찮아요 👌",
                        role: "user",
                      });
                      onInsertCaption(false);
                    }}
                    className="bg-gray-300 text-gray-800 px-3 py-1 rounded-lg text-xs"
                  >
                    아니요 괜찮아요 👌
                  </button>
                </div>
              )}

              {/* 캡션 입력 UI */}
              {msg.captionEditor && (
                <CaptionEditor
                  textData={msg.textData || ""}
                  onComplete={(finalImg) => {
                    updateTempMessage(msg.tempId!, {
                      captionSelect: false,
                      content: "이미지에 문구 삽입이 완료되었습니다! 🎉",
                      img: finalImg,
                      captionEditor: false,
                    });
                  }}
                />
              )}

              {/* 모드 선택 */}
              {msg.modeSelect && <ImageModeSelectorBubble onSelect={onSelectMode} />}

              {/* BGM 선택 */}
              {msg.bgmSelect && <BgmSelectBubble onSelect={onSelectBgmOption} />}
            </>
          )}
        </div>
      ))}
    </div>
  );
}
