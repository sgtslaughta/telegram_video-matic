import { Routes, Route } from 'react-router-dom'
import Shell from '@/components/layout/Shell'
import Login from '@/pages/Login'
import Overview from '@/pages/Overview'
import Connect from '@/pages/Connect'
import SubscriptionsList from '@/pages/SubscriptionsList'
import SubscriptionEditor from '@/pages/SubscriptionEditor'
import Browse from '@/pages/Browse'
import Downloads from '@/pages/Downloads'
import MediaDetail from '@/pages/MediaDetail'
import Activity from '@/pages/Activity'
import Settings from '@/pages/Settings'
import Storage from '@/pages/Storage'

export default function Router() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<Shell />}>
        <Route path="/" element={<Overview />} />
        <Route path="/connect" element={<Connect />} />
        <Route path="/subscriptions" element={<SubscriptionsList />} />
        <Route path="/subscriptions/:id" element={<SubscriptionEditor />} />
        <Route path="/browse" element={<Browse />} />
        <Route path="/downloads" element={<Downloads />} />
        <Route path="/media/:id" element={<MediaDetail />} />
        <Route path="/activity" element={<Activity />} />
        <Route path="/storage" element={<Storage />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}
