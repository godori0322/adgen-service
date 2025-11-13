
interface AuthFormProps {
  onSubmit: (email: string, password: string, name: string) => void;
  loading?: boolean;
  error?: string | null;
}


// export function AuthForm({onSubmit, loading, error}: AuthFormProps) {
  
// }