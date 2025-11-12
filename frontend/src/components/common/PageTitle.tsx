
interface PageTitleProps {
  children: React.ReactNode;
}

export default function PageTitle({children}: PageTitleProps) {
  return (
    <h1 className="text-xl bg-gray-50 pt-4 pb-28">
      {children}
    </h1>
  )
}