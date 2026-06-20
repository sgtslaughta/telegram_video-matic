import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ConfirmDialog } from './ConfirmDialog'

describe('ConfirmDialog', () => {
  it('calls onConfirm when confirm button is clicked', async () => {
    const onConfirm = vi.fn()
    const onCancel = vi.fn()
    const user = userEvent.setup()

    render(
      <ConfirmDialog
        title="Delete Item"
        description="Are you sure?"
        onConfirm={onConfirm}
        onCancel={onCancel}
        isOpen={true}
      />
    )

    const confirmBtn = screen.getByRole('button', { name: /confirm/i })
    await user.click(confirmBtn)
    expect(onConfirm).toHaveBeenCalledOnce()
  })

  it('calls onCancel when cancel button is clicked', async () => {
    const onConfirm = vi.fn()
    const onCancel = vi.fn()
    const user = userEvent.setup()

    render(
      <ConfirmDialog
        title="Delete Item"
        description="Are you sure?"
        onConfirm={onConfirm}
        onCancel={onCancel}
        isOpen={true}
      />
    )

    const cancelBtn = screen.getByRole('button', { name: /cancel/i })
    await user.click(cancelBtn)
    expect(onCancel).toHaveBeenCalledOnce()
  })
})
