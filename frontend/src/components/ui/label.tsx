import { clsx } from 'clsx'

interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {}

export function Label({ className, ...props }: LabelProps) {
  return (
    <label className={clsx('block text-sm font-medium text-gray-700', className)} {...props} />
  )
}
