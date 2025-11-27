import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { registerRequest } from "../../api/auth";
import Button from "../../components/common/Button";
import TextInput from "../../components/common/TextInput";
import TimePicker from "../../components/common/TimePicker";
import { PageTitle } from "../../components/common/Title";
import { isValidEmail, isValidPassword, isValidUsername } from "../../utils/validators";

export default function SignupPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    userName: "",
    password: "",
    email: "",
    confirmPassword: "",
    // name: "",
    businessType: "",
    location: "",
    openTime: "",
    closeTime: "",
    menuItems: [] as string[],
  });
  const [menuInput, setMenuInput] = useState("");
  const [menuError, setMenuError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [userNameError, setUserNameError] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const isDisabled = !!userNameError || !!emailError || !!passwordError;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { id, value } = e.target;
    setForm((prev) => ({ ...prev, [id]: value }));
    // 이메일 검증
    if (id === "email") {
      if (value === "") setEmailError(null);
      else if (!isValidEmail(value)) setEmailError("유효한 이메일 형식이 아닙니다.");
      else setEmailError(null);
    }

    // 비밀번호 8자 체크
    if (id === "password") {
      if (!isValidPassword(value)) setPasswordError("비밀번호는 8자 이상이어야 합니다.");
      else setPasswordError(null);
    }
    // 이메일 유효성 검사
    if (id === "userName") {
      if (value === "") {
        setUserNameError(null);
      } else if (!isValidUsername(value)) {
        setUserNameError("아이디는 영어 소문자, 숫자, _ 만 사용할 수 있습니다.");
      } else {
        setUserNameError(null);
      }
    }
  };

  const handleMenuKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.nativeEvent.isComposing) return;

    if (e.key === "Enter") {
      e.preventDefault();
      const value = menuInput.trim();
      if (value === "") return;

      if (form.menuItems.includes(value)) {
        setMenuError("이미 등록된 메뉴입니다!");
        return;
      }
      setMenuError(null);
      setForm((prev) => ({
        ...prev,
        menuItems: [...prev.menuItems, menuInput],
      }));
      setMenuInput("");
    }
  };
  const removeMenuItem = (index: number) => {
    setForm((prev) => ({
      ...prev,
      menuItems: prev.menuItems.filter((_, idx) => idx !== index),
    }));
  };
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (
      !form.userName ||
      !form.password ||
      // !form.name ||
      !form.businessType ||
      !form.location ||
      !form.openTime ||
      !form.closeTime ||
      form.menuItems.length == 0
    ) {
      setFormError("⚠️ 모든 항목을 입력해주세요!");
      return;
    }
    try {
      setLoading(true);
      const businessHour = `${form.openTime}-${form.closeTime}`;
      const payload = {
        username: form.userName,
        password: form.password,
        email: form.email,
        // name: form.name,
        business_type: form.businessType,
        location: form.location,
        business_hours: businessHour,
        menu_items: form.menuItems,
      };
      await registerRequest(payload);
      setFormError(null);
      setEmailError(null);
      setPasswordError(null);
      navigate("/login", { state: { registered: true } });
    } catch (err: any) {
      setFormError(err.message || "알 수 없는 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-lg border border-gray-200">
        <PageTitle>회원가입</PageTitle>

        {/* 회원가입 폼 */}
        <form
          className="space-y-4"
          onSubmit={handleSubmit}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault(); // 🔥 전체 폼에서 Enter 제출 막기
            }
          }}
        >
          <TextInput
            id="userName"
            label="아이디"
            placeholder="아이디"
            value={form.userName}
            onChange={handleChange}
            error={userNameError}
          />
          <TextInput
            id="password"
            label="비밀번호"
            placeholder="8자 이상 입력해주세요"
            type="password"
            value={form.password}
            onChange={handleChange}
            error={passwordError}
          />
          <TextInput
            id="email"
            label="이메일"
            placeholder="example@owner.com"
            type="text"
            value={form.email}
            onChange={handleChange}
            error={emailError}
          />
          {/* <TextInput
            id="name"
            label="이름"
            placeholder="홍길동"
            value={form.name}
            onChange={handleChange}
          /> */}
          <TextInput
            id="businessType"
            label="가게업종"
            placeholder="카페"
            value={form.businessType}
            onChange={handleChange}
          />
          <TextInput
            id="location"
            label="위치"
            placeholder="서울특별시 서대문구"
            value={form.location}
            onChange={handleChange}
          />
          <div className="flex gap-3">
            <TimePicker
              label="오픈시간"
              value={form.openTime}
              onChange={(v) => setForm((prev) => ({ ...prev, openTime: v }))}
            />

            <TimePicker
              label="마감시간"
              value={form.closeTime}
              onChange={(v) => setForm((prev) => ({ ...prev, closeTime: v }))}
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-600">메뉴 리스트</label>
            <input
              type="text"
              placeholder="메뉴 입력 후 엔터 (예: 아메리카노)"
              value={menuInput}
              onChange={(e) => setMenuInput(e.target.value)}
              onKeyDown={handleMenuKeyDown}
              className="w-full mt-1 px-3 py-2 border rounded-lg"
            />
            {menuError && <p className="mt-1 text-xs text-red-500">{menuError}</p>}
            {/* 태그 리스트 */}
            <div className="flex flex-wrap gap-2 mt-2">
              {form.menuItems.map((item, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm flex items-center gap-1"
                >
                  {item}
                  <button
                    type="button"
                    onClick={() => removeMenuItem(idx)}
                    className="text-xs text-red-500"
                  >
                    ✕
                  </button>
                </span>
              ))}
            </div>
          </div>
          <Button
            text={loading ? "가입중... " : "회원가입"}
            type="submit"
            disabled={loading || isDisabled}
          />
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
