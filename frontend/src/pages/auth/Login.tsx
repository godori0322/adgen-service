import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { loginRequest } from "../../api/authApi";
import AuthLayout from "../../components/layout/AuthLayout";
import { useAuth } from "../../context/AuthContext";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/i;

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  // 상태관리
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  // 에러상태 관리
  const [emailErr, setEmailErr] = useState<string | null>(null);
  const [pwErr, setPwErr] = useState<string | null>(null);
  const [touched, setTouched] = useState({ email: false, password: false });
  const [formError, setFormError] = useState<string | null>(null);

  const validateEmail = (v: string) => {
    if (!v) return "이메일을 입력해주세요.";
    if (!EMAIL_PATTERN.test(v)) return "올바른 이메일 형식이 아닙니다.";
    return null;
  };
  const validatePassword = (v: string) => {
    if (!v) return "비밀번호를 입력해주세요.";
    return null;
  };
  // 입력 핸들러
  const onChangeEmail = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    setEmail(v);
    if (touched.email) {
      setEmailErr(validateEmail(v));
    }
    if (formError) setFormError(null);
  };

  const onChangePassword = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    setPassword(v);
    if (touched.password) {
      setPwErr(validatePassword(v));
    }
    if (formError) setFormError(null);
  };

  const onBlurEmail = () => {
    if (!touched.email) setTouched((t) => ({ ...t, email: true }));
    setEmailErr(validateEmail(email));
  };
  const onBlurPassword = () => {
    if (!touched.password) setTouched((t) => ({ ...t, password: true }));
    setPwErr(validatePassword(password));
  };

  // 로그인 처리
  const handleLogin = async (e?: React.FormEvent) => {
    e?.preventDefault();

    // 최종 검증
    const eErr = validateEmail(email);
    const pErr = validatePassword(password);
    setEmailErr(eErr);
    setPwErr(pErr);

    if (eErr || pErr) return;

    setLoading(true);
    try {
      const data = await loginRequest(email, password);
      login(data.token, data.user);
      navigate("/");
    } catch (err: any) {
      setFormError(err?.message ?? "로그인 실패");
    } finally {
      setLoading(false);
    }
  };

  const isDisabled = loading || !!emailErr || !!pwErr || !email || !password;

  return (
    <>
      <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-lg border border-gray-200">
        {/* 로고 or 타이틀 */}
        <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">로그인</h1>

        <form onSubmit={handleLogin} noValidate>
          {/* 이메일 입력 */}
          <div className="mb-5">
            <label htmlFor="email" className="block text-sm font-medium text-gray-600 mb-1">
              이메일
            </label>
            <input
              id="email"
              name="email"
              type="email"
              placeholder="example@email.com"
              value={email}
              onChange={onChangeEmail}
              onBlur={onBlurEmail}
              aria-invalid={!!emailErr}
              aria-describedby="email-error"
              className={`
                w-full px-4 py-3 rounded-lg border
                ${
                  emailErr
                    ? "border-red-500 focus:ring-red-400"
                    : "border-gray-300 focus:ring-blue-400"
                }
                focus:outline-none focus:ring-2 transition-all
              `}
            />
            {emailErr && (
              <p id="email-error" className="mt-1 text-xs text-red-600">
                {emailErr}
              </p>
            )}
          </div>

          {/* 비밀번호 입력 */}
          <div className="mb-6">
            <label htmlFor="password" className="block text-sm font-medium text-gray-600 mb-1">
              비밀번호
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="new-password"
              placeholder="••••••••"
              value={password}
              onChange={onChangePassword}
              onBlur={onBlurPassword}
              aria-invalid={!!pwErr}
              aria-describedby="password-error"
              className={`
                w-full px-4 py-3 rounded-lg border
                ${
                  pwErr
                    ? "border-red-500 focus:ring-red-400"
                    : "border-gray-300 focus:ring-blue-400"
                }
                focus:outline-none focus:ring-2 transition-all
              `}
            />
            {pwErr && (
              <p id="password-error" className="mt-1 text-xs text-red-600">
                {pwErr}
              </p>
            )}
          </div>

          {/* 로그인 버튼 */}
          <button
            type="submit"
            disabled={isDisabled}
            className={`
              w-full text-white font-semibold py-3 rounded-lg transition shadow-md hover:shadow-lg
              ${isDisabled ? "bg-blue-300 cursor-not-allowed" : "bg-blue-500 hover:bg-blue-600"}
            `}
          >
            {loading ? "로그인 중..." : "로그인"}
          </button>
          <div className="min-h-5 mt-2">
            {formError && (
              <p className="text-xs text-red-600 mt-1" role="alert" aria-live="polite">
                {formError}
              </p>
            )}
          </div>
        </form>

        {/* 구분 라인 */}
        <div className="flex items-center my-6">
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
    </>
  );
}
