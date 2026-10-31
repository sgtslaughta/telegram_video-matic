import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Fragment, useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTgStatus, useTgSetCredentials, useTgLoginPhone, useTgLoginCode, useTgLoginPassword, useTgLogout } from '@/hooks/useTgStatus';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AccountStatus } from '@/lib/types';
export default function TelegramLoginFlow({ onConnected }) {
    const tgStatus = useTgStatus();
    const setCreds = useTgSetCredentials();
    const loginPhone = useTgLoginPhone();
    const loginCode = useTgLoginCode();
    const loginPassword = useTgLoginPassword();
    const logout = useTgLogout();
    const [apiId, setApiId] = useState('');
    const [apiHash, setApiHash] = useState('');
    const [editCreds, setEditCreds] = useState(false);
    // Manual (backward) step choice, valid only while the backend status is unchanged.
    const [ovr, setOvr] = useState(null);
    const stepOverride = ovr && ovr.status === tgStatus.data?.status ? ovr.step : null;
    const setStepOverride = (step) => setOvr(step ? { step, status: tgStatus.data?.status } : null);
    const [phone, setPhone] = useState('');
    const [code, setCode] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    // Determine current step based on status
    const getStep = () => {
        if (!tgStatus.data)
            return 'phone';
        // No API credentials yet (or user chose to change them) → credentials step
        if (!tgStatus.data.configured || editCreds)
            return 'credentials';
        switch (tgStatus.data.status) {
            case AccountStatus.DISCONNECTED:
                return 'phone';
            case AccountStatus.WAITING_PHONE:
                return 'phone';
            case AccountStatus.WAITING_CODE:
                return 'code';
            case AccountStatus.WAITING_PASSWORD:
                return 'password';
            case AccountStatus.CONNECTED:
                return 'confirmation';
            default:
                return 'phone';
        }
    };
    // Step ordering for clamping manual (backward) navigation.
    const STEP_ORDER = {
        credentials: 0, phone: 1, code: 2, password: 3, confirmation: 4,
    };
    const STEPPER = [
        { step: 'phone', label: 'Phone', n: 1 },
        { step: 'code', label: 'Code', n: 2 },
        { step: 'password', label: 'Auth', n: 3 },
    ];
    const derivedStep = getStep();
    // Allow jumping back to an earlier step (corrections); never skip ahead.
    const currentStep = stepOverride && STEP_ORDER[stepOverride] <= STEP_ORDER[derivedStep]
        ? stepOverride
        : derivedStep;
    // A stepper number is reachable only if it's at or before the real progress.
    const goToStep = (target) => {
        if (STEP_ORDER[target] <= STEP_ORDER[derivedStep])
            setStepOverride(target);
    };
    // Call onConnected when status becomes CONNECTED
    useEffect(() => {
        if (tgStatus.data?.status === AccountStatus.CONNECTED) {
            onConnected?.();
        }
    }, [tgStatus.data?.status, onConnected]);
    const handleCredentialsSubmit = async (e) => {
        e.preventDefault();
        setError('');
        if (!apiId.trim() || !apiHash.trim())
            return;
        try {
            await setCreds.mutateAsync({ apiId: apiId.trim(), apiHash: apiHash.trim() });
            setEditCreds(false);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Telegram request failed');
        }
    };
    const handlePhoneSubmit = async (e) => {
        e.preventDefault();
        setError('');
        if (!phone.trim())
            return;
        try {
            await loginPhone.mutateAsync(phone);
            setStepOverride(null);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Telegram request failed');
        }
    };
    const handleCodeSubmit = async (e) => {
        e.preventDefault();
        setError('');
        if (!code.trim())
            return;
        try {
            await loginCode.mutateAsync(code);
            setStepOverride(null);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Telegram request failed');
        }
    };
    const handlePasswordSubmit = async (e) => {
        e.preventDefault();
        setError('');
        if (!password.trim())
            return;
        try {
            await loginPassword.mutateAsync(password);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Telegram request failed');
        }
    };
    const handleLogout = async () => {
        try {
            await logout.mutateAsync();
            setPhone('');
            setCode('');
            setPassword('');
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Telegram request failed');
        }
    };
    const stepVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: {
            opacity: 1,
            y: 0,
            transition: { duration: 0.3 },
        },
        exit: {
            opacity: 0,
            y: -20,
            transition: { duration: 0.2 },
        },
    };
    return (_jsxs("div", { className: "w-full", children: [currentStep !== 'credentials' && (_jsx("div", { className: "mb-5 flex items-center justify-between", children: STEPPER.map((s, i) => {
                    const reached = STEP_ORDER[derivedStep] >= STEP_ORDER[s.step];
                    const active = STEP_ORDER[currentStep] >= STEP_ORDER[s.step];
                    return (_jsxs(Fragment, { children: [i > 0 && (_jsx("div", { className: `mx-2 h-px flex-1 ${active ? 'bg-brand' : 'bg-border'}` })), _jsxs("div", { className: "flex items-center gap-2", children: [_jsx("button", { type: "button", onClick: () => goToStep(s.step), disabled: !reached, "aria-label": `Go to ${s.label} step`, className: `flex h-6 w-6 items-center justify-center rounded-full text-[12px] font-semibold transition-colors ${active ? 'bg-brand text-primary-foreground' : 'bg-muted text-muted-foreground'} ${reached ? 'cursor-pointer hover:opacity-90' : 'cursor-default'}`, children: s.n }), _jsx("div", { className: "text-[12px] text-muted-foreground", children: s.label })] })] }, s.step));
                }) })), _jsx("div", { className: "rounded-lg border border-border bg-card p-5", children: _jsxs("div", { children: [_jsxs(AnimatePresence, { mode: "wait", children: [currentStep === 'credentials' && (_jsxs(motion.form, { variants: stepVariants, initial: "hidden", animate: "visible", exit: "exit", onSubmit: handleCredentialsSubmit, className: "space-y-4", children: [_jsxs("div", { children: [_jsx("h2", { className: "mb-1.5 text-[15px] font-semibold", children: "Telegram API credentials" }), _jsxs("p", { className: "mb-4 text-[12px] text-muted-foreground", children: ["Get these from", ' ', _jsx("a", { href: "https://my.telegram.org/apps", target: "_blank", rel: "noreferrer", className: "text-brand hover:underline", children: "my.telegram.org/apps" }), ": log in with your phone \u2192 ", _jsx("span", { className: "font-medium", children: "API development tools" }), " \u2192 create an app (any title) \u2192 copy your ", _jsx("span", { className: "font-medium", children: "api_id" }), " and", ' ', _jsx("span", { className: "font-medium", children: "api_hash" }), "."] }), _jsxs("div", { className: "space-y-3", children: [_jsxs("div", { className: "space-y-2", children: [_jsx(Label, { className: "text-[13px]", htmlFor: "api_id", children: "api_id" }), _jsx(Input, { id: "api_id", inputMode: "numeric", value: apiId, onChange: (e) => setApiId(e.target.value.replace(/\D/g, '')), disabled: setCreds.isPending, placeholder: "1234567", autoFocus: true })] }), _jsxs("div", { className: "space-y-2", children: [_jsx(Label, { className: "text-[13px]", htmlFor: "api_hash", children: "api_hash" }), _jsx(Input, { id: "api_hash", value: apiHash, onChange: (e) => setApiHash(e.target.value), disabled: setCreds.isPending, placeholder: "0123456789abcdef0123456789abcdef" })] })] })] }), _jsx(Button, { type: "submit", disabled: setCreds.isPending || !apiId.trim() || !apiHash.trim(), className: "w-full", children: setCreds.isPending ? 'Saving...' : 'Continue' })] }, "credentials")), currentStep === 'phone' && (_jsxs(motion.form, { variants: stepVariants, initial: "hidden", animate: "visible", exit: "exit", onSubmit: handlePhoneSubmit, className: "space-y-4", children: [_jsxs("div", { children: [_jsx("h2", { className: "mb-3 text-[15px] font-semibold", children: "Enter phone number" }), _jsxs("div", { className: "space-y-2", children: [_jsx(Label, { className: "text-[13px]", htmlFor: "phone", children: "Phone" }), _jsx(Input, { id: "phone", type: "tel", value: phone, onChange: (e) => setPhone(e.target.value), disabled: loginPhone.isPending, placeholder: "+1 234 567 8900", autoFocus: true }), _jsx("p", { className: "text-[12px] text-muted-foreground", children: "Include country code (e.g., +1 for US)" })] })] }), _jsx(Button, { type: "submit", disabled: loginPhone.isPending || !phone.trim(), className: "w-full", children: loginPhone.isPending ? 'Sending...' : 'Next' }), _jsx("button", { type: "button", onClick: () => setEditCreds(true), className: "w-full text-center text-[12px] text-muted-foreground underline-offset-2 hover:underline", children: "Change API credentials" })] }, "phone")), currentStep === 'code' && (_jsxs(motion.form, { variants: stepVariants, initial: "hidden", animate: "visible", exit: "exit", onSubmit: handleCodeSubmit, className: "space-y-4", children: [_jsxs("div", { children: [_jsx("h2", { className: "mb-3 text-[15px] font-semibold", children: "Enter SMS code" }), _jsxs("div", { className: "space-y-2", children: [_jsx(Label, { className: "text-[13px]", htmlFor: "code", children: "Code" }), _jsx(Input, { id: "code", type: "text", value: code, onChange: (e) => setCode(e.target.value.replace(/\D/g, '')), disabled: loginCode.isPending, placeholder: "123456", maxLength: 6, className: "tracking-widest", autoFocus: true }), _jsx("p", { className: "text-[12px] text-muted-foreground", children: "Check your Telegram for the code" })] })] }), _jsx(Button, { type: "submit", disabled: loginCode.isPending || code.length < 5, className: "w-full", children: loginCode.isPending ? 'Verifying...' : 'Next' })] }, "code")), currentStep === 'password' && (_jsxs(motion.form, { variants: stepVariants, initial: "hidden", animate: "visible", exit: "exit", onSubmit: handlePasswordSubmit, className: "space-y-4", children: [_jsxs("div", { children: [_jsx("h2", { className: "mb-3 text-[15px] font-semibold", children: "Two-factor password" }), _jsxs("div", { className: "space-y-2", children: [_jsx(Label, { className: "text-[13px]", htmlFor: "password", children: "Password" }), _jsx(Input, { id: "password", type: "password", value: password, onChange: (e) => setPassword(e.target.value), disabled: loginPassword.isPending, placeholder: "Enter your 2FA password", autoFocus: true })] })] }), _jsx(Button, { type: "submit", disabled: loginPassword.isPending || !password.trim(), className: "w-full", children: loginPassword.isPending ? 'Verifying...' : 'Connect' })] }, "password")), currentStep === 'confirmation' && tgStatus.data && (_jsxs(motion.div, { variants: stepVariants, initial: "hidden", animate: "visible", exit: "exit", className: "space-y-4 text-center", children: [_jsxs("div", { className: "mb-6", children: [_jsx("h2", { className: "text-[15px] font-semibold", children: "Connected!" }), _jsx("p", { className: "mt-3 text-[24px] font-semibold tracking-tight text-foreground", children: tgStatus.data.username
                                                        ? `@${tgStatus.data.username}`
                                                        : tgStatus.data.display_name || 'User' }), tgStatus.data.phone && (_jsx("p", { className: "mt-2 text-[13px] text-muted-foreground", children: tgStatus.data.phone }))] }), _jsxs(Badge, { className: "inline-flex items-center gap-1.5 bg-ok/10 text-ok hover:bg-ok/10", children: [_jsx("span", { className: "h-1.5 w-1.5 rounded-full bg-ok" }), "Account verified"] }), _jsx(Button, { onClick: handleLogout, disabled: logout.isPending, variant: "outline", className: "w-full mt-6", children: logout.isPending ? 'Logging out...' : 'Logout' })] }, "confirmation"))] }), error && _jsx("p", { role: "alert", className: "mt-3 text-[12px] text-err", children: error })] }) })] }));
}
