import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Routes, Route } from 'react-router-dom';
import Shell from '@/components/layout/Shell';
import Login from '@/pages/Login';
import Overview from '@/pages/Overview';
import Connect from '@/pages/Connect';
import SubscriptionsList from '@/pages/SubscriptionsList';
import SubscriptionEditor from '@/pages/SubscriptionEditor';
import Browse from '@/pages/Browse';
import Downloads from '@/pages/Downloads';
import MediaDetail from '@/pages/MediaDetail';
import Activity from '@/pages/Activity';
import Settings from '@/pages/Settings';
import Storage from '@/pages/Storage';
export default function Router() {
    return (_jsxs(Routes, { children: [_jsx(Route, { path: "/login", element: _jsx(Login, {}) }), _jsxs(Route, { element: _jsx(Shell, {}), children: [_jsx(Route, { path: "/", element: _jsx(Overview, {}) }), _jsx(Route, { path: "/connect", element: _jsx(Connect, {}) }), _jsx(Route, { path: "/subscriptions", element: _jsx(SubscriptionsList, {}) }), _jsx(Route, { path: "/subscriptions/:id", element: _jsx(SubscriptionEditor, {}) }), _jsx(Route, { path: "/browse", element: _jsx(Browse, {}) }), _jsx(Route, { path: "/downloads", element: _jsx(Downloads, {}) }), _jsx(Route, { path: "/media/:id", element: _jsx(MediaDetail, {}) }), _jsx(Route, { path: "/activity", element: _jsx(Activity, {}) }), _jsx(Route, { path: "/storage", element: _jsx(Storage, {}) }), _jsx(Route, { path: "/settings", element: _jsx(Settings, {}) })] })] }));
}
