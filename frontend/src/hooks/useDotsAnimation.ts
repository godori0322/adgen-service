import { useRef } from "react";


export function useDotsAnimation<T extends { tempId?: number; content: string }>(
  setter: React.Dispatch<React.SetStateAction<T[]>>
) {
  const timerRef = useRef<number | null>(null);
  const stepRef = useRef(0);

  const startDots = (tempId: number) => {
    const frames = [".", "..", "..."];
    timerRef.current = window.setInterval(() => {
      stepRef.current = (stepRef.current + 1) % frames.length;
      setter((prev) =>
        prev.map((m: any) => (m.tempId === tempId ? { ...m, content: frames[stepRef.current] } : m))
      );
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