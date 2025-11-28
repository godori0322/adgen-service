import ReactMarkdown from "react-markdown";
import type { ChatMessage } from "../../hooks/useVoiceChat";
import ShareImageButton from "../common/ShareImageButton";
import type { ImageMode } from "./ImageModeSelectorBubble";
import ImageModeSelectorBubble from "./ImageModeSelectorBubble";
import remarkGfm from "remark-gfm";

export default function ChatBubbleList({
  messages,
  onSelectMode,
}: {
  messages: ChatMessage[];
  onSelectMode: (mode: ImageMode) => void;
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
          className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow 
            ${
              msg.role === "user"
                ? "ml-auto bg-blue-500 text-white rounded-br-none max-w-[70%]"
                : "mr-auto bg-gray-200 text-gray-900 rounded-bl-none max-w-[80%]"
            }`}
        >
          {msg.content && (
            <>
              {/* <pre className="whitespace-pre-wrap font-sans text-sm">{msg.content}</pre> */}
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {(msg.content || "").replace(/\\n/g, "\n")}
              </ReactMarkdown>
            </>
          )}

          {msg.img && (
            <div className="w-full flex flex-col items-center gap-3 mt-2">
              <img src={msg.img} alt="생성된 이미지" className="rounded-lg" />
              {msg.role == "assistant" && (
                <div className="flex gap-2">
                  <ShareImageButton imageUrl={msg.img} />
                  <button
                    onClick={() => downloadImage(msg.img!, `adgen-image-${Date.now()}.png`)}
                    className="bg-gray-600 hover:bg-gray-700 text-white rounded-lg px-4 py-2 mt-2"
                  >
                    ⬇️ 저장하기
                  </button>
                </div>
              )}
            </div>
          )}

          {msg.modeSelect && <ImageModeSelectorBubble onSelect={onSelectMode} />}
        </div>
      ))}
    </div>
  );
}
