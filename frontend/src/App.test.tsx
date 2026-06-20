import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders the app title', () => {
    render(<App />)
    expect(screen.getByText('Video-Matic')).toBeTruthy()
  })

  it('displays scaffold ready message', () => {
    render(<App />)
    expect(screen.getByText('Frontend scaffold ready.')).toBeTruthy()
  })
})
