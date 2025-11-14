interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  img?: string;
}

export default function ChatBubbleList({ messages }: { messages: ChatMessage[] }) {
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
                ? "ml-auto bg-blue-500 text-white rounded-br-none"
                : "mr-auto bg-gray-200 text-gray-900 rounded-bl-none"
            }`}
        >
          <pre className="whitespace-pre-wrap font-sans text-sm">{msg.content}</pre>
          {msg.img && (
            <div className="mt-3 flex flex-col items-start">
              <img src={msg.img} alt="생성된 이미지" className="rounded-lg" />
              <button
                onClick={() => downloadImage(msg.img!, `adgen-image-${Date.now()}.png`)}
                className="mt-2 px-3 py-1.5 bg-blue-600 text-white text-xs rounded-md shadow hover:bg-blue-700 transition"
              >
                이미지 저장 ⬇️
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
