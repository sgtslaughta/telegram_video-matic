import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLogin } from '@/hooks/useAuth';
import Logo from '@/components/Logo';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
export default function Login() {
    const navigate = useNavigate();
    const login = useLogin();
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        try {
            // Trim so a pasted trailing newline/space doesn't cause a false reject.
            await login.mutateAsync(password.trim());
            navigate('/');
        }
        catch (err) {
            setError(err instanceof Error && err.message ? err.message : 'Login failed. Check the password and try again.');
        }
    };
    return (_jsx("div", { className: "flex min-h-screen items-center justify-center bg-background px-4", children: _jsxs("div", { className: "w-full max-w-sm", children: [_jsxs("div", { className: "mb-6 flex flex-col items-center gap-2", children: [_jsx(Logo, { className: "h-16 w-16", title: "TGVM" }), _jsx("h1", { className: "text-[20px] font-semibold tracking-tight", children: "Login" }), _jsx("p", { className: "text-[13px] text-muted-foreground", children: "Enter the password to open your library." })] }), _jsxs("form", { onSubmit: handleSubmit, className: "space-y-4 rounded-lg border border-border bg-card p-5", children: [_jsxs("div", { className: "space-y-1.5", children: [_jsx(Label, { htmlFor: "password", className: "text-[13px]", children: "Password" }), _jsx(Input, { id: "password", type: "password", autoComplete: "current-password", value: password, onChange: (e) => { setPassword(e.target.value); setError(''); }, disabled: login.isPending, placeholder: "Enter your password", autoFocus: true, "aria-invalid": !!error, "aria-describedby": error ? 'login-error' : undefined }), error && _jsx("p", { id: "login-error", role: "alert", className: "text-[12px] text-err", children: error })] }), _jsx(Button, { type: "submit", disabled: login.isPending || !password, className: "w-full", children: login.isPending ? 'Logging in…' : 'Login' })] })] }) }));
}
