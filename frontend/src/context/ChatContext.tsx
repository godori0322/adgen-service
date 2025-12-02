import { createContext, useContext, useEffect, useState } from "react";
import { useAuth } from "./AuthContext";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  img?: string;
  video?: string;
  audio?: string;
  tempId?: number;
  modeSelect?: boolean;
  bgmSelect?: boolean;
  textData?: {
    caption?: string;
    imgWidth?: number;
    imgHeight?: number;
    file?: File;
  };
  caption?: string;
  fail?: boolean;
  captionSelect?: boolean;
  captionEditor?: boolean;
  previewSelect?: boolean;
  previewConfirmed?: boolean;
  previewRejected?: boolean;
  loading?: boolean;
}

interface ChatContextValue {
  messages: ChatMessage[];
  addMessage: (message: ChatMessage) => void;
  updateTempMessage: (tempId: number, update: Partial<ChatMessage>) => void;
  resetMessages: () => void;
}

const ChatContext = createContext<ChatContextValue | null>(null);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const { isLogin } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  // 로그인 시 복원
  useEffect(() => {
    if (isLogin) {
      const saved = sessionStorage.getItem("chatMessages");
      if (saved) setMessages(JSON.parse(saved));
    } else {
      setMessages([]);
    }
  }, [isLogin]);

  // 로그인 중에만 저장
  useEffect(() => {
    if (isLogin) {
      const lightMessages = messages.map(({ img, video, audio, textData, ...rest }) => rest);
      sessionStorage.setItem("chatMessages", JSON.stringify(lightMessages));
    }
  }, [messages, isLogin]);

  const addMessage = (msg: ChatMessage) => {
    setMessages((prev) => [...prev, msg]);
  };

  const updateTempMessage = (tempId: number, update: Partial<ChatMessage>) => {
    setMessages((prev) => prev.map((m) => (m.tempId === tempId ? { ...m, ...update } : m)));
  };

  const resetMessages = () => {
    setMessages([]);
    sessionStorage.removeItem("chatMessages");
  };

  return (
    <ChatContext.Provider value={{ messages, addMessage, updateTempMessage, resetMessages }}>
      {children}
    </ChatContext.Provider>
  );
}

export const useChat = () => {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be used within ChatProvider");
  return ctx;
};
