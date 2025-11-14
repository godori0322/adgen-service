import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { loginRequest } from "../../api/authApi";
import Button from "../../components/common/Button";
import TextInput from "../../components/common/TextInput";
import { PageTitle } from "../../components/common/Title";
import Toast from "../../components/common/Toast";
import { useAuth } from "../../context/AuthContext";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    if (location.state?.registered) {
      setToast("🎉 회원가입이 완료되었습니다!");
      // 1.5초 뒤 자동으로 사라짐
      setTimeout(() => setToast(null), 1500);
    }
  }, [location.state]);
  // 상태관리
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  // 에러상태 관리
  const [userIdErr, setUserIdErr] = useState<string | null>(null);
  const [pwErr, setPwErr] = useState<string | null>(null);
  const [touched, setTouched] = useState({ userId: false, password: false });
  const [formError, setFormError] = useState<string | null>(null);

  const validateUserId = (v: string) => {
    if (!v) return "아이디를 입력해주세요.";
    return null;
  };
  const validatePassword = (v: string) => {
    if (!v) return "비밀번호를 입력해주세요.";
    return null;
  };

  const onChangePassword = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    setPassword(v);
    if (touched.password) {
      setPwErr(validatePassword(v));
    }
    if (formError) setFormError(null);
  };

  const onBlurPassword = () => {
    if (!touched.password) setTouched((t) => ({ ...t, password: true }));
    setPwErr(validatePassword(password));
  };

  // 로그인 처리
  const handleLogin = async (e?: React.FormEvent) => {
    e?.preventDefault();

    // 최종 검증
    const eErr = validateUserId(userId);
    const pErr = validatePassword(password);
    setUserIdErr(eErr);
    setPwErr(pErr);

    if (eErr || pErr) return;

    setLoading(true);
    try {
      const data = await loginRequest(userId, password);
      login(data.token, data.user);
      navigate("/");
    } catch (err: any) {
      setFormError(err?.message ?? "로그인 실패");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-lg border border-gray-200">
        {/* 로고 or 타이틀 */}
        <PageTitle>로그인</PageTitle>

        <form onSubmit={handleLogin} noValidate>
          {/* 이메일 입력 */}
          <TextInput
            id="userId"
            label="아이디"
            type="userId"
            value={userId}
            placeholder="userId"
            onChange={(e) => setUserId(e.target.value)}
            onBlur={() => setUserIdErr(validateUserId(userId))}
            error={userIdErr}
          />

          {/* 비밀번호 입력 */}
          <TextInput
            id="password"
            label="비밀번호"
            type="password"
            value={password}
            placeholder="••••••••"
            onChange={onChangePassword}
            onBlur={onBlurPassword}
            error={pwErr}
          />

          {/* 로그인 버튼 */}
          <Button
            type="submit"
            text="로그인"
            loading={loading}
            disabled={loading || !userId || !password || !!userIdErr || !!pwErr}
          />
          <div className="min-h-5 mt-2">
            {formError && (
              <p className="text-xs text-red-600 mt-1" role="alert" aria-live="polite">
                {formError}
              </p>
            )}
          </div>
        </form>

        {/* 구분 라인 */}
        <div className="flex items-center my-4">
          <div className="flex-grow h-px bg-gray-300"></div>
          <span className="px-2 text-sm text-gray-500">또는</span>
          <div className="flex-grow h-px bg-gray-300"></div>
        </div>

        {/* 회원가입 */}
        <div className="text-center text-sm">
          <span className="text-gray-600">아직 계정이 없나요?</span>{" "}
          <Link to="/signup" className="text-blue-600 font-medium hover:underline">
            회원가입
          </Link>
        </div>
      </div>
      {toast && <Toast message={toast} />}
    </>
  );
}
