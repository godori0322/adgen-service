export default function Toast({ message }: { message: string }) {
  return (
    <div className="fixed bottom-8 left-1/2 -translate-x-1/2 bg-blue-500 text-white px-6 py-3 rounded-xl shadow-lg animate-bounce">
      {message}
    </div>
  );
}
