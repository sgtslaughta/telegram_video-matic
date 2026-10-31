import { useId } from 'react'

// TGVM mark: Telegram-style plane over "TG" (Telegram blue) + "VM" (emerald)
// on a bevelled cream (light) / slate (dark) disc. Same artwork as
// public/favicon.svg; colours switch with the app theme via the .dark class.
// Letters are Inter Black, outlined so the mark never depends on loaded fonts.
const PLANE = 'M10.6 23.1 34.9 13.7c1.1-.4 2.1.3 1.8 1.9l-4.1 19.4c-.3 1.4-1.1 1.7-2.3 1.1l-6.3-4.6-3 2.9c-.3.3-.6.6-1.3.6l.5-6.4 11.6-10.5c.5-.5-.1-.7-.8-.3L16.7 26.9l-6.2-1.9c-1.3-.4-1.4-1.3.1-1.9z'
const TG = 'M-0.16 29.6V26.8H10.96V29.6H7.14V39.6H3.67V29.6ZM16.02 39.77Q14.15 39.77 12.74 38.98Q11.33 38.18 10.54 36.71Q9.75 35.24 9.75 33.22Q9.75 31.11 10.59 29.64Q11.44 28.16 12.86 27.39Q14.27 26.62 16 26.62Q17.51 26.62 18.73 27.19Q19.96 27.75 20.72 28.74Q21.49 29.73 21.62 31.02H18.12Q17.95 30.36 17.42 30.01Q16.89 29.65 16.07 29.65Q14.76 29.65 14.04 30.58Q13.32 31.5 13.32 33.17Q13.32 34.86 14.01 35.8Q14.7 36.75 16.05 36.75Q17.21 36.75 17.81 36.26Q18.4 35.77 18.43 34.92H16.11V32.45H21.78V34.22Q21.78 35.97 21.04 37.22Q20.3 38.46 19 39.11Q17.69 39.77 16.02 39.77Z'
const VM = 'M24.81 39.6 20.52 26.8H24.45L25.94 31.76Q26.3 32.97 26.61 34.19Q26.92 35.41 27.21 36.67Q27.48 35.41 27.77 34.19Q28.07 32.97 28.41 31.76L29.83 26.8H33.72L29.56 39.6ZM32.64 39.6V26.8H38.12L39.27 30.8Q39.41 31.27 39.58 32.03Q39.74 32.79 39.92 33.66Q40.09 34.54 40.23 35.38Q40.38 34.54 40.55 33.66Q40.72 32.79 40.89 32.03Q41.06 31.27 41.19 30.8L42.32 26.8H47.81V39.6H44.31V34.65Q44.31 34.16 44.33 33.31Q44.36 32.47 44.39 31.47Q44.42 30.48 44.44 29.55Q44.23 30.52 43.99 31.5Q43.76 32.48 43.54 33.3Q43.32 34.13 43.16 34.65L41.68 39.6H38.79L37.28 34.65Q37.12 34.15 36.91 33.36Q36.69 32.57 36.46 31.64Q36.23 30.71 36.02 29.76Q36.04 30.67 36.07 31.62Q36.09 32.57 36.12 33.37Q36.14 34.18 36.14 34.65V39.6Z'

export default function Logo({ className = 'h-7 w-7', title }: { className?: string; title?: string }) {
  const id = useId().replace(/:/g, '')
  return (
    <svg viewBox="0 0 48 48" className={className} role={title ? 'img' : undefined} aria-hidden={title ? undefined : true}>
      {title && <title>{title}</title>}
      <defs>
        <linearGradient id={`r${id}`} x1=".15" y1="0" x2=".85" y2="1">
          <stop offset="0" className="[stop-color:#FFFFFF] dark:[stop-color:#3B4A63]" />
          <stop offset="1" className="[stop-color:#C9BFAA] dark:[stop-color:#0B1220]" />
        </linearGradient>
        <linearGradient id={`i${id}`} x1=".85" y1="1" x2=".15" y2="0">
          <stop offset="0" stopOpacity=".55" className="[stop-color:#FFFFFF] dark:[stop-color:#3B4A63]" />
          <stop offset=".5" stopOpacity="0" className="[stop-color:#FFFFFF] dark:[stop-color:#3B4A63]" />
        </linearGradient>
        <clipPath id={`c${id}`}><circle cx="24" cy="24" r="21.8" /></clipPath>
      </defs>
      <circle cx="24" cy="24" r="24" fill={`url(#r${id})`} />
      <circle cx="24" cy="24" r="23.75" fill="none" strokeOpacity=".5" strokeWidth=".5" className="stroke-[#B3A88F] dark:stroke-[#0B1220]" />
      <circle cx="24" cy="24" r="21.8" className="fill-[#F5F0E6] dark:fill-[#1E293B]" />
      <g clipPath={`url(#c${id})`}>
        <path transform="translate(6.6 -2.4) scale(0.75)" d={PLANE} className="fill-[#1E293B] dark:fill-[#F5F0E6]" />
        <path d={TG} fill="#229ED9" />
        <path d={VM} fill="#10B981" />
      </g>
      <circle cx="24" cy="24" r="21.5" fill="none" strokeWidth=".6" stroke={`url(#i${id})`} />
    </svg>
  )
}
