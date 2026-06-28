// Brand glyph: paper-plane reads as a play button. Uses currentColor so it
// tracks the user's accent (see AccentPicker). Same geometry as favicon.svg.
export default function Logo({ className = 'h-7 w-7' }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" className={className} aria-hidden="true">
      <path d="M38 24 13 11 21 24Z" fill="currentColor" />
      <path d="M38 24 21 24 13 37Z" fill="currentColor" fillOpacity={0.6} />
    </svg>
  )
}
