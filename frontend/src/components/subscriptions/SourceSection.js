import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useChannels, useTopics } from '@/hooks/useChannels';
import { Input } from '@/components/ui/input';
import { Combobox } from '@/components/ui/combobox';
import { Field, Section } from './Section';
export function SourceSection({ s, update }) {
    const channels = useChannels();
    const topics = useTopics(s.channelId);
    return (_jsxs(Section, { title: "Source", description: "Where new videos are picked up from.", children: [_jsx(Field, { label: "Name", htmlFor: "name", hint: "Shown in the list. Defaults to the channel name.", children: _jsx(Input, { id: "name", value: s.name, onChange: (e) => update('name', e.target.value), placeholder: "e.g. Premiership matches" }) }), _jsxs("div", { className: "grid gap-4 sm:grid-cols-2", children: [_jsx(Field, { label: "Channel", children: _jsx(Combobox, { value: s.channelId?.toString() || '', onChange: (v) => { update('channelId', v ? parseInt(v) : null); update('topicId', null); }, placeholder: "Select channel", searchPlaceholder: "Search channels\u2026", options: (channels.data ?? []).map((ch) => ({ value: ch.id.toString(), label: ch.title })) }) }), _jsx(Field, { label: "Topic", hint: "The forum topic to capture.", children: _jsx(Combobox, { value: s.topicId?.toString() || '', onChange: (v) => update('topicId', v ? parseInt(v) : null), disabled: !s.channelId, placeholder: "Select topic", searchPlaceholder: "Search topics\u2026", options: (topics.data ?? []).map((t) => ({ value: t.id.toString(), label: t.title })) }) })] })] }));
}
