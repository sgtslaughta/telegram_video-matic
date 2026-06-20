import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  useSubscriptions,
  useUpdateSubscription,
  useDeleteSubscription,
  useScanSubscription,
} from '@/hooks/useSubscriptions'
import { ConfirmDialog, EmptyState, StatusBadge } from '@/components/shared'
import type { SubscriptionRead } from '@/lib/types'

export default function SubscriptionsList() {
  const navigate = useNavigate()
  const { data: subscriptions = [], isLoading } = useSubscriptions()
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [scanId, setScanId] = useState<number | null>(null)
  const [toggleId, setToggleId] = useState<number | null>(null)

  // ponytail: hooks called once per sub at top level
  const deleteMut = useDeleteSubscription(deleteId || 0)
  const scanMut = useScanSubscription(scanId || 0)
  const updateMut = useUpdateSubscription(toggleId || 0)

  const handleToggle = (sub: SubscriptionRead) => {
    setToggleId(sub.id)
    updateMut.mutate({ enabled: !sub.enabled })
  }

  const handleDelete = async () => {
    if (deleteId) {
      await deleteMut.mutateAsync()
      setDeleteId(null)
    }
  }

  const handleScan = (id: number) => {
    setScanId(id)
    scanMut.mutate()
  }

  const truncate = (text: string, len: number = 40) =>
    text.length > len ? text.slice(0, len) + '...' : text

  if (isLoading) return <div className="p-6">Loading...</div>

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Subscriptions</h1>
        <button
          onClick={() => navigate('/subscriptions/new')}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Add Subscription
        </button>
      </div>

      {subscriptions.length === 0 ? (
        <EmptyState
          title="No subscriptions yet"
          message="Create your first subscription to start downloading media."
          action={{
            label: 'Add Subscription',
            onClick: () => navigate('/subscriptions/new'),
          }}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {subscriptions.map((sub) => (
            <div
              key={sub.id}
              className="flex flex-col rounded-lg border border-gray-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900"
            >
              <div className="mb-3 flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    Channel {sub.channel_id}
                  </h3>
                  {sub.topic_id && (
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Topic {sub.topic_id}
                    </p>
                  )}
                </div>
                <StatusBadge status={sub.enabled ? 'enabled' : 'disabled'} />
              </div>

              {sub.filter_regex && (
                <p className="mb-2 text-xs text-gray-500 dark:text-gray-500">
                  Filter: {truncate(sub.filter_regex)}
                </p>
              )}

              <p className="mb-4 text-xs text-gray-500 dark:text-gray-500">
                Last scan:{' '}
                {sub.updated_at
                  ? new Date(sub.updated_at).toLocaleDateString()
                  : 'Never'}
              </p>

              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => handleToggle(sub)}
                  className="flex-1 rounded px-2 py-1 text-xs font-medium text-white bg-gray-600 hover:bg-gray-700"
                >
                  {sub.enabled ? 'Disable' : 'Enable'}
                </button>
                <button
                  onClick={() => navigate(`/subscriptions/${sub.id}`)}
                  className="flex-1 rounded px-2 py-1 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleScan(sub.id)}
                  className="flex-1 rounded px-2 py-1 text-xs font-medium text-white bg-green-600 hover:bg-green-700"
                >
                  Scan
                </button>
                <button
                  onClick={() => setDeleteId(sub.id)}
                  className="flex-1 rounded px-2 py-1 text-xs font-medium text-white bg-red-600 hover:bg-red-700"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <ConfirmDialog
        isOpen={deleteId !== null}
        title="Delete Subscription"
        description="This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </div>
  )
}
