import { useState } from "react";
import { ReactMediaRecorder } from "react-media-recorder";

export default function VoiceRecorder({
  onAudioSend,
  disabled,
}: {
  onAudioSend: (b: Blob) => void;
  disabled: boolean;
}) {
  const [audioURL, setAudioURL] = useState<string | null>(null);

  return (
    <ReactMediaRecorder
      audio
      onStop={(url, blob) => {
        setAudioURL(url);
        onAudioSend(blob);
      }}
      render={({ startRecording, stopRecording, status }) => (
        <div className="flex flex-col items-center gap-3">
          {/* 녹음 완료 후 재생 UI */}
          {/* {status !== "recording" && audioURL && (
            <div className="w-full flex flex-col items-center gap-2">
              <audio src={audioURL} controls className="w-72 rounded-lg shadow-sm" />
            </div>
          )} */}

          {/* 태 표시 */}
          <p className="text-sm text-gray-600 h-4">
            {status === "recording" ? "🎙️ 녹음 중..." : audioURL ? "" : "대기 중"}
          </p>

          {/* 녹음 버튼 UI */}
          <div className="flex items-center justify-center">
            {status !== "recording" && (
              <button
                onClick={startRecording}
                disabled={disabled}
                className="
                  w-20 h-20 rounded-full 
                  bg-blue-500 text-white text-3xl
                  flex items-center justify-center
                  shadow-lg hover:bg-blue-600
                  transition-all active:scale-95
                "
              >
                🎤
              </button>
            )}

            {status === "recording" && (
              <button
                onClick={stopRecording}
                className="
                  w-20 h-20 rounded-full 
                  bg-red-500 text-white text-3xl
                  flex items-center justify-center
                  shadow-lg animate-pulse
                  transition-all active:scale-95
                "
              >
                ⏹️
              </button>
            )}
          </div>
        </div>
      )}
    />
  );
}
