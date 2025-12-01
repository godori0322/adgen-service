// src/hooks/useDotsAnimation.ts
import { useRef } from "react";
import { useChat } from "../context/ChatContext";

export function useDotsAnimation() {
  const { updateTempMessage } = useChat();

  // tempId 별 타이머 / 단계 저장
  const timersRef = useRef<Record<number, number>>({});
  const stepsRef = useRef<Record<number, number>>({});

  const startDots = (tempId: number) => {
    const frames = [".", "..", "..."];

    stepsRef.current[tempId] = 0;

    // setInterval이 number를 반환하도록 단언
    const id = window.setInterval(() => {
      const next = ((stepsRef.current[tempId] ?? 0) + 1) % frames.length;
      stepsRef.current[tempId] = next;

      updateTempMessage(tempId, {
        content: frames[next],
      });
    }, 400);

    timersRef.current[tempId] = id;
  };

  /**
   * tempId를 넘기면 해당 버블만 정지,
   * 인자를 안 넘기면 모든 로딩 버블 정지
   */
  const stopDots = (tempId?: number) => {
    if (typeof tempId === "number") {
      const timer = timersRef.current[tempId];
      if (timer) {
        clearInterval(timer);
        delete timersRef.current[tempId];
        delete stepsRef.current[tempId];
      }
      return;
    }

    // 전체 비우기 - 안전하게 check
    Object.values(timersRef.current ?? {}).forEach((t) => clearInterval(t));
    timersRef.current = {};
    stepsRef.current = {};
  };

  return { startDots, stopDots };
}
