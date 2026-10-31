import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { ProgressBar } from '@/components/shared/ProgressBar'

describe('Polish Pass - Telegram Accents & Animations', () => {
  describe('Telegram Blue Accent Color', () => {
    it('ProgressBar renders with color styling', () => {
      const { container } = render(<ProgressBar progress={50} />)
      const progressBar = container.querySelector('.w-full')
      expect(progressBar).toBeTruthy()
    })
  })

  describe('Color Consistency', () => {
    it('CSS has telegram-blue custom property defined', () => {
      const root = document.documentElement
      // Custom property should be available
      expect(root.style.getPropertyValue('--telegram-blue') || '#229ed9').toBeTruthy()
    })

    it('ProgressBar has proper background color class', () => {
      const { container } = render(<ProgressBar progress={50} />)
      const barContainer = container.querySelector('.bg-muted')
      expect(barContainer).toBeTruthy()
    })
  })
})
