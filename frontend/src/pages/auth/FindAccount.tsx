import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { findPasswordRequest, findUsernameRequest } from "../../api/auth";
import ResultModal from "../../components/common/ResultModal";
import Button from "../../components/common/Button";
import TextInput from "../../components/common/TextInput";
import { isValidEmail } from "../../utils/validators";

export default function FindAccountPage() {
  const navigate = useNavigate();

  const [modal, setModal] = useState<null | {
    title: string;
    message: string;
    primaryText: string;
    secondaryText?: string;
    onPrimary: () => void;
    onSecondary?: () => void;
  }>(null);

  // 아이디 찾기
  const [findEmail, setFindEmail] = useState("");
  const [findEmailError, setFindEmailError] = useState<string | null>(null);

  const handleFindUsername = async () => {
    try {
      const res = await findUsernameRequest(findEmail);

      setModal({
        title: "아이디 찾기 완료 🎉",
        message: `가입된 아이디는\n${res.username} 입니다`,
        primaryText: "비밀번호 재설정",
        secondaryText: "로그인하기",
        onPrimary: () => navigate("/reset-password", { state: { username: res.username } }),
        onSecondary: () => navigate("/login"),
      });
    } catch (err: any) {
      setModal({
        title: "찾을 수 없음",
        message: err.message || "해당 이메일로 가입된 계정이 없습니다.",
        primaryText: "확인",
        onPrimary: () => setModal(null),
      });
    }
  };

  // 비밀번호 찾기
  const [pwUser, setPwUser] = useState("");
  const [pwEmail, setPwEmail] = useState("");
  const [pwEmailError, setPwEmailError] = useState<string | null>(null);

  const handleFindPassword = async () => {
    try {
      await findPasswordRequest(pwUser, pwEmail);

      setModal({
        title: "사용자 확인 완료 ✔️",
        message: "비밀번호를 재설정해주세요!",
        primaryText: "바로 이동",
        onPrimary: () => navigate("/reset-password", { state: { username: pwUser } }),
        onSecondary: () => navigate("/login"),
      });
    } catch (err: any) {
      setModal({
        title: "정보 불일치",
        message: err.message || "정보가 일치하지 않습니다.",
        primaryText: "확인",
        onPrimary: () => setModal(null),
      });
    }
  };

  return (
    <div className="w-full max-w-md mx-auto bg-white p-8 rounded-2xl shadow-lg border border-gray-200">
      <h2 className="text-2xl font-bold text-center mb-8">아이디 / 비밀번호 찾기</h2>

      {/* 아이디 찾기 */}
      <section className="pb-6 border-b border-gray-300">
        <h3 className="text-lg font-semibold mb-3">아이디 찾기</h3>
        <TextInput
          id="findEmail"
          type="email"
          value={findEmail}
          placeholder="가입 이메일 입력"
          onChange={(e) => {
            const v = e.target.value;
            setFindEmail(v);
            if (!v) setFindEmailError(null);
            else if (!isValidEmail(v)) setFindEmailError("유효한 이메일을 입력해주세요.");
            else setFindEmailError(null);
          }}
          error={findEmailError}
        />
        <Button
          text="아이디 찾기"
          disabled={!findEmail || !!findEmailError}
          onClick={handleFindUsername}
        />
      </section>

      {/* 비밀번호 찾기 */}
      <section className="pt-6">
        <h3 className="text-lg font-semibold mb-3">비밀번호 찾기</h3>
        <TextInput
          id="pwUser"
          value={pwUser}
          placeholder="아이디 입력"
          onChange={(e) => setPwUser(e.target.value)}
          empty={false}
        />

        <TextInput
          id="pwEmail"
          type="email"
          value={pwEmail}
          placeholder="가입 이메일 입력"
          onChange={(e) => {
            const v = e.target.value;
            setPwEmail(v);
            if (!v) setPwEmailError(null);
            else if (!isValidEmail(v)) setPwEmailError("유효한 이메일을 입력해주세요.");
            else setPwEmailError(null);
          }}
          error={pwEmailError}
        />

        <Button
          text="비밀번호 확인"
          disabled={!pwUser || !pwEmail || !!pwEmailError}
          onClick={handleFindPassword}
        />
      </section>

      {modal && <ResultModal {...modal} onClose={() => setModal(null)} />}
    </div>
  );
}
