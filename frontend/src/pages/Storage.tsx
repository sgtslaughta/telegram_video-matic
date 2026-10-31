import { Page, PageHeader } from '@/components/shared/PageHeader'

// ponytail: placeholder so the route exists; the storage agent replaces it.
export default function Storage() {
  return (
    <Page>
      <PageHeader title="Storage" description="Disk usage, cleanup preview and files the app doesn’t track." />
    </Page>
  )
}
