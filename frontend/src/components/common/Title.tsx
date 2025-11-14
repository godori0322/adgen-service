
interface PageTitleProps {
  children: React.ReactNode;
  variant?: "simple" | "section";
}

export function PageTitle({ children, variant = "simple" }: PageTitleProps) {
  if (variant === "section") {
    return (
      <div className="bg-gray-50 py-10 border-b border-gray-200">
        <h1 className="text-2xl font-bold text-gray-800 text-center">{children}</h1>
      </div>
    );
  }

  // 폼, 로그인/회원가입용 (심플)
  return <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">{children}</h1>;
}

export function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h2 className="text-lg font-semibold text-gray-700 mt-6 mb-3">{children}</h2>;
}