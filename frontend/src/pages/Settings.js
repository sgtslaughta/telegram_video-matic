import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { Page, PageHeader } from '@/components/shared/PageHeader';
import { Skeleton } from '@/components/ui/skeleton';
import { useSettings } from '@/hooks/useSettings';
import { usePlugins } from '@/hooks/usePlugins';
import { GeneralSection, CleanupSection } from '@/components/settings/GeneralCleanup';
import { NotificationsSettings } from '@/components/settings/NotificationsSettings';
import { AppearanceSection } from '@/components/settings/AppearanceSection';
import { PluginsSection } from '@/components/settings/PluginsSection';
import { AccountSection } from '@/components/settings/AccountSection';
import { cn } from '@/lib/utils';
const SECTIONS = [
    ['general', 'General'], ['cleanup', 'Cleanup'], ['notifications', 'Notifications'],
    ['appearance', 'Appearance'], ['plugins', 'Plugins'], ['account', 'Account'],
];
function SectionNav() {
    const [active, setActive] = useState(SECTIONS[0][0]);
    useEffect(() => {
        if (typeof IntersectionObserver === 'undefined')
            return;
        const io = new IntersectionObserver((entries) => entries.forEach((e) => e.isIntersecting && setActive(e.target.id)), { rootMargin: '-10% 0px -80% 0px' });
        SECTIONS.forEach(([id]) => { const el = document.getElementById(id); if (el)
            io.observe(el); });
        return () => io.disconnect();
    }, []);
    return (_jsx("nav", { "aria-label": "Settings sections", className: "flex gap-1 overflow-x-auto pb-3 lg:sticky lg:top-6 lg:flex-col lg:self-start lg:pb-0", children: SECTIONS.map(([id, label]) => (_jsx("a", { href: `#${id}`, "aria-current": active === id ? 'true' : undefined, onClick: (e) => { e.preventDefault(); setActive(id); document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }); }, className: cn('whitespace-nowrap rounded-md px-3 py-1.5 text-[13px] transition-colors', active === id ? 'bg-brand/10 font-medium text-brand' : 'text-muted-foreground hover:bg-accent/60 hover:text-foreground'), children: label }, id))) }));
}
export default function Settings() {
    const { isLoading: l1 } = useSettings();
    const { isLoading: l2 } = usePlugins();
    const loading = l1 || l2;
    return (_jsxs(Page, { children: [_jsx(PageHeader, { title: "Settings", description: "Changes are saved per section." }), _jsxs("div", { className: "grid grid-cols-1 gap-6 lg:grid-cols-[180px_minmax(0,1fr)]", children: [_jsx(SectionNav, {}), loading ? (_jsx("div", { className: "space-y-4", children: [0, 1, 2].map((i) => _jsx(Skeleton, { className: "h-40 w-full" }, i)) })) : (_jsxs("div", { className: "min-w-0 space-y-4", children: [_jsx(GeneralSection, {}), _jsx(CleanupSection, {}), _jsx(NotificationsSettings, {}), _jsx(AppearanceSection, {}), _jsx(PluginsSection, {}), _jsx(AccountSection, {})] }))] })] }));
}
