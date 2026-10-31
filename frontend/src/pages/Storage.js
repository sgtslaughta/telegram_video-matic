import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Page, PageHeader } from '@/components/shared/PageHeader';
import { Skeleton } from '@/components/ui/skeleton';
import { useStorage } from '@/hooks/useStorage';
import { DiskUsage } from '@/components/storage/DiskUsage';
import { PausedPanel } from '@/components/storage/PausedPanel';
import { PreviewTable } from '@/components/storage/PreviewTable';
import { FoldersTable } from '@/components/storage/FoldersTable';
import { UntrackedTable } from '@/components/storage/UntrackedTable';
export default function Storage() {
    const { data, isLoading, error } = useStorage();
    const head = _jsx(PageHeader, { title: "Storage", description: "Disk usage, cleanup preview and files the app doesn\u2019t track." });
    if (error) {
        return _jsxs(Page, { children: [head, _jsxs("p", { className: "text-[13px] text-muted-foreground", children: ["Storage couldn\u2019t load (", error.message, "). It retries every minute."] })] });
    }
    if (isLoading || !data) {
        return _jsxs(Page, { children: [head, _jsx("div", { className: "space-y-4", children: [0, 1, 2].map((i) => _jsx(Skeleton, { className: "h-32 w-full" }, i)) })] });
    }
    return (_jsxs(Page, { children: [head, _jsxs("div", { className: "space-y-4", children: [_jsx(DiskUsage, { s: data }), data.paused && (_jsx(PausedPanel, { count: data.paused.count, gb: data.paused.gb, onReview: () => document.getElementById('cleanup-preview')?.scrollIntoView({ behavior: 'smooth' }) })), _jsx(PreviewTable, { preview: data.preview }), _jsx(FoldersTable, { folders: data.folders }), _jsx(UntrackedTable, { untracked: data.untracked })] })] }));
}
