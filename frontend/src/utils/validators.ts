// 이메일 정규식
export const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// 아이디 정규식 (영어 소문자 + 숫자 + _)
export const usernameRegex = /^[a-z0-9_]+$/;

// 비밀번호 정규식 
export const passwordMinLength = 8;

export const isValidEmail = (email: string) => emailRegex.test(email);
export const isValidUsername = (name: string) => usernameRegex.test(name);
export const isValidPassword = (pw: string) => pw.length >= passwordMinLength;
