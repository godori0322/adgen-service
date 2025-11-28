// src/components/header/AppHeader.tsx
import { Link } from "react-router-dom";

export default function AuthHeader() {
  return (
    <header className="w-full bg-white shadow-sm px-6 py-4 flex justify-between items-center">
      <Link to="/" className="text-xl font-bold text-blue-600">
        AdGen
      </Link>
    </header>
  );
}
