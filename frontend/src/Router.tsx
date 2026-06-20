import { Routes, Route } from 'react-router-dom'
import Shell from '@/components/layout/Shell'
import Login from '@/pages/Login'
import Dashboard from '@/pages/Dashboard'
import Connect from '@/pages/Connect'
import SubscriptionsList from '@/pages/SubscriptionsList'
import SubscriptionEditor from '@/pages/SubscriptionEditor'
import Browse from '@/pages/Browse'
import MediaDetail from '@/pages/MediaDetail'
import Activity from '@/pages/Activity'
import Settings from '@/pages/Settings'

export default function Router() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<Shell />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/connect" element={<Connect />} />
        <Route path="/subscriptions" element={<SubscriptionsList />} />
        <Route path="/subscriptions/:id" element={<SubscriptionEditor />} />
        <Route path="/browse" element={<Browse />} />
        <Route path="/media/:id" element={<MediaDetail />} />
        <Route path="/activity" element={<Activity />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}
