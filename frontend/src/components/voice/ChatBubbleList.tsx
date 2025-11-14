

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  img?: string;
}

export default function ChatBubbleList({ messages }: { messages: ChatMessage[] }) {
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
          {msg.img && <img src={msg.img} alt="생성된 이미지" className="rounded-lg mt-2" />}
        </div>
      ))}
    </div>
  );
}