import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { resetPasswordRequest } from "../../api/auth";
import Button from "../../components/common/Button";
import TextInput from "../../components/common/TextInput";
import ResultModal from "../../components/common/ResultModal";
import { isValidPassword } from "../../utils/validators";

export default function ResetPasswordPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const username = location.state?.username; // findAccount에서 넘겨준 값

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [confirmPasswordError, setConfirmPasswordError] = useState<string | null>(null);

  const [loading, setLoading] = useState(false);

  const [modal, setModal] = useState<null | {
    title: string;
    message: string;
    primaryText: string;
    onPrimary: () => void;
  }>(null);

  const handlePasswordChange = (value: string) => {
    setPassword(value);

    if (!isValidPassword(value)) setPasswordError("비밀번호는 8자 이상이어야 합니다.");
    else setPasswordError(null);

    if (confirmPassword && value !== confirmPassword) {
      setConfirmPasswordError("비밀번호가 일치하지 않습니다.");
    } else {
      setConfirmPasswordError(null);
    }
  };

  const handleConfirmChange = (value: string) => {
    setConfirmPassword(value);

    if (value !== password) {
      setConfirmPasswordError("비밀번호가 일치하지 않습니다.");
    } else {
      setConfirmPasswordError(null);
    }
  };

  const disabled =
    !password || !confirmPassword || !!passwordError || !!confirmPasswordError || loading;

  const handleSubmit = async () => {
    try {
      setLoading(true);
      await resetPasswordRequest(username, password);

      setModal({
        title: "비밀번호 변경 완료 🎉",
        message: "새로운 비밀번호로 로그인해주세요!",
        primaryText: "로그인으로 이동",
        onPrimary: () => navigate("/login"),
      });
    } catch (err: any) {
      setModal({
        title: "오류 발생",
        message: err.message || "비밀번호 변경 실패",
        primaryText: "확인",
        onPrimary: () => setModal(null),
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto bg-white p-8 rounded-2xl shadow-lg border border-gray-200">
      <h2 className="text-2xl font-bold text-center mb-8">비밀번호 재설정</h2>

      {!username ? (
        <p className="text-center text-red-600">접근 오류 — 계정 정보를 먼저 확인해주세요.</p>
      ) : (
        <>
          <TextInput
            id="password"
            type="password"
            label="새 비밀번호"
            value={password}
            placeholder="8자 이상 입력해주세요"
            onChange={(e) => handlePasswordChange(e.target.value)}
            error={passwordError}
          />

          <TextInput
            id="confirmPassword"
            type="password"
            label="비밀번호 확인"
            value={confirmPassword}
            placeholder="한 번 더 입력해주세요"
            onChange={(e) => handleConfirmChange(e.target.value)}
            error={confirmPasswordError}
          />

          <Button
            text={loading ? "변경 중..." : "비밀번호 변경"}
            onClick={handleSubmit}
            disabled={disabled}
          />
        </>
      )}

      {modal && <ResultModal {...modal} onClose={() => setModal(null)} />}
    </div>
  );
}
