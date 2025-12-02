import { Outlet } from "react-router-dom";
import AppHeader from "../header/AppHeader";
import FloatingHubButton from "../common/FloatingHubButton";

export default function MainLayout() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="sticky top-0 z-50 bg-white shadow-sm border-b">
        <AppHeader />
      </header>

      <main className="flex-1 max-w-3xl mx-auto w-full px-4 py-6">
        <Outlet />
      </main>
      <FloatingHubButton />
    </div>
  );
}
