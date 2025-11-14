import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Button from "../../components/common/Button";
import TextInput from "../../components/common/TextInput";
import { PageTitle } from "../../components/common/Title";

export default function SignupPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    userId: "",
    password: "",
    confirmPassword: "",
    name: "",
    storeType: "",
    address: "",
  });

  const [loading, setLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { id, value } = e.target;
    setForm((prev) => ({ ...prev, [id]: value }));
  };
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.userId || !form.password || !form.name || !form.storeType || !form.address) {
      setFormError("⚠️ 모든 항목을 입력해주세요!");
      return;
    }
    try {
      setLoading(true);
      // const res = await registerUser(form);
      // console.log("✅ 회원가입 요청:", form, res);
      console.log("✅ 회원가입 요청:", form);
      await new Promise((res) => setTimeout(res, 1500));

      // 완료 후 로그인 페이지 이동
      navigate("/login", { state: { registered: true } });
    } catch (err: any) {
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-lg border border-gray-200">
        <PageTitle>회원가입</PageTitle>

        {/* 회원가입 폼 */}
        <form className="space-y-4" onSubmit={handleSubmit}>
          <TextInput
            id="userId"
            label="아이디"
            placeholder="아이디"
            value={form.userId}
            onChange={handleChange}
          />
          <TextInput
            id="password"
            label="비밀번호"
            placeholder="8자 이상 입력해주세요"
            type="password"
            value={form.password}
            onChange={handleChange}
          />

          <TextInput
            id="name"
            label="이름"
            placeholder="홍길동"
            value={form.name}
            onChange={handleChange}
          />
          <TextInput
            id="storeType"
            label="가게업종"
            placeholder="카페"
            value={form.storeType}
            onChange={handleChange}
          />
          <TextInput
            id="address"
            label="주소"
            placeholder="서울특별시 서대문구"
            value={form.address}
            onChange={handleChange}
          />
          <Button text={loading ? "가임중... " : "회원가입"} type="submit" disabled={loading} />
          <div className="min-h-5 mt-2">
            {formError && (
              <p className="text-xs text-red-600 mt-1" role="alert" aria-live="polite">
                {formError}
              </p>
            )}
          </div>
        </form>
        {/* 구분선 */}
        <div className="flex items-center my-6">
          <div className="flex-grow h-px bg-gray-300" />
          <span className="px-2 text-sm text-gray-500">또는</span>
          <div className="flex-grow h-px bg-gray-300" />
        </div>

        {/* 로그인으로 이동 */}
        <div className="text-center text-sm">
          <span className="text-gray-600">이미 계정이 있나요?</span>{" "}
          <Link to="/login" className="text-blue-600 font-medium hover:underline">
            로그인
          </Link>
        </div>
      </div>
    </>
  );
}
