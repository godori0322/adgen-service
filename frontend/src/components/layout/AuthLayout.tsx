import { Outlet } from "react-router-dom";
import AuthHeader from "../header/AuthHeader";

export default function AuthLayout() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-100">
      <header className="sticky top-0 z-50 bg-white shadow-sm border-b">
        <AuthHeader />
      </header>
      <main className="flex flex-1 items-center justify-center max-w-md mx-auto w-full px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
