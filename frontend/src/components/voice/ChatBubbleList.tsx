import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "../../hooks/useVoiceChat";
import ShareImageButton from "../common/ShareImageButton";
import BgmSelectBubble from "./BgmSelectBubble";
import type { ImageMode } from "./ImageModeSelectorBubble";
import ImageModeSelectorBubble from "./ImageModeSelectorBubble";

export default function ChatBubbleList({
  messages,
  onSelectMode,
  onSelectBgmOption,
  retryProcess,
}: {
  messages: ChatMessage[];
  onSelectMode: (mode: ImageMode) => void;
  onSelectBgmOption: (opt: "video" | "image" | "separate") => void;
  retryProcess: (type: "image" | "video" | "audio") => void;
}) {
  const downloadImage = (base64Url: string, filename: string) => {
    const link = document.createElement("a");
    link.href = base64Url;
    link.download = filename;
    link.click();
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
            ${msg.retryType ? "border-red-300 bg-red-50 rounded-xl text-red-700 text-sm" : ""}
          `}
        >
          {/* 실패 시 재시도 UI */}
          {msg.retryType ? (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">❌</span>
                <span>{msg.content}</span>
              </div>
              <button
                onClick={() => retryProcess(msg.retryType!)}
                className="w-full bg-red-500 hover:bg-red-600 text-white font-semibold 
                 py-2 rounded-lg transition-all duration-200 shadow 
                 flex justify-center items-center gap-1"
              >
                🔄 다시 시도
              </button>
            </div>
          ) : (
            <>
              {/* 텍스트 */}
              {msg.content && (
                <div className="whitespace-pre-wrap break-words">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {(msg.content || "").replace(/\\n/g, "\n")}
                  </ReactMarkdown>
                </div>
              )}

              {/* 이미지 */}
              {msg.img && (
                <div className="w-full flex flex-col items-center gap-3 mt-2">
                  <img src={msg.img} alt="생성된 이미지" className="rounded-lg max-w-full" />
                  {msg.role === "assistant" && (
                    <div className="flex gap-2">
                      <ShareImageButton imageUrl={msg.img} />
                      <button
                        onClick={() => downloadImage(msg.img!, `adgen-image-${Date.now()}.png`)}
                        className="bg-gray-600 hover:bg-gray-700 text-white rounded-md px-3 py-1 text-xs shadow mt-2"
                      >
                        ⬇️ 저장
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* 동영상 */}
              {msg.video && (
                <div className="mt-3">
                  <video controls src={msg.video} className="rounded-lg max-w-full" />
                </div>
              )}

              {/* 오디오 */}
              {msg.audio && (
                <div className="w-full flex flex-col items-center gap-2 mt-2">
                  <audio controls className="w-full">
                    <source src={msg.audio} type="audio/mpeg" />
                  </audio>
                </div>
              )}

              {/* 이미지 모드 선택 */}
              {msg.modeSelect && <ImageModeSelectorBubble onSelect={onSelectMode} />}

              {/* BGM 선택 */}
              {msg.bgmSelect && <BgmSelectBubble onSelect={(opt) => onSelectBgmOption(opt)} />}
            </>
          )}
        </div>
      ))}
    </div>
  );
}
