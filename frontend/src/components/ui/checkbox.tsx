import { clsx } from 'clsx'

interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  onCheckedChange?: (checked: boolean) => void
}

export function Checkbox({ onCheckedChange, className, ...props }: CheckboxProps) {
  return (
    <input
      type="checkbox"
      className={clsx('w-4 h-4 rounded border-gray-300 cursor-pointer', className)}
      onChange={(e) => onCheckedChange?.(e.target.checked)}
      {...props}
    />
  )
}
