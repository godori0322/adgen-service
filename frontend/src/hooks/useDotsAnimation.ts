import { useRef } from "react";
import { useChat } from "../context/ChatContext";

export function useDotsAnimation() {
  const { updateTempMessage } = useChat();
  const timerRef = useRef<number | null>(null);
  const stepRef = useRef(0);

  const startDots = (tempId: number) => {
    const frames = [".", "..", "..."];
    timerRef.current = window.setInterval(() => {
      stepRef.current = (stepRef.current + 1) % frames.length;
      updateTempMessage(tempId, {
        content: frames[stepRef.current],
      });
    }, 400);
  };

  const stopDots = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
      stepRef.current = 0;
    }
  };

  return { startDots, stopDots };
}
