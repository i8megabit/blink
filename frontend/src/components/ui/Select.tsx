import * as React from "react"
import { ChevronDown } from "lucide-react"
import { cn } from "../../lib/utils"

interface SelectProps {
  value?: string
  onValueChange?: (value: string) => void
  children: React.ReactNode
  className?: string
}

interface SelectTriggerProps {
  children: React.ReactNode
  className?: string
}

interface SelectContentProps {
  children: React.ReactNode
  className?: string
}

interface SelectItemProps {
  value: string
  children: React.ReactNode
  className?: string
}

interface SelectValueProps {
  placeholder?: string
  className?: string
}

const SelectContext = React.createContext<{
  value: string
  onValueChange: (value: string) => void
  open: boolean
  setOpen: (open: boolean) => void
} | null>(null)

const Select: React.FC<SelectProps> = ({ value, onValueChange, children, className }) => {
  const [internalValue, setInternalValue] = React.useState("")
  const [open, setOpen] = React.useState(false)
  
  const currentValue = value !== undefined ? value : internalValue
  const handleValueChange = onValueChange || setInternalValue

  return (
    <SelectContext.Provider value={{ 
      value: currentValue, 
      onValueChange: handleValueChange,
      open,
      setOpen
    }}>
      <div className={cn("relative", className)}>
        {children}
      </div>
    </SelectContext.Provider>
  )
}

const SelectTrigger: React.FC<SelectTriggerProps> = ({ children, className }) => {
  const context = React.useContext(SelectContext)
  if (!context) throw new Error("SelectTrigger must be used within Select")

  return (
    <button
      className={cn(
        "flex h-10 w-full items-center justify-between rounded-md border border-gray-200 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-800 dark:bg-gray-950 dark:ring-offset-gray-950 dark:placeholder:text-gray-400 dark:focus:ring-gray-300",
        className
      )}
      onClick={() => context.setOpen(!context.open)}
    >
      {children}
      <ChevronDown className="h-4 w-4 opacity-50" />
    </button>
  )
}

const SelectContent: React.FC<SelectContentProps> = ({ children, className }) => {
  const context = React.useContext(SelectContext)
  if (!context) throw new Error("SelectContent must be used within Select")

  if (!context.open) return null

  return (
    <div className="absolute top-full left-0 right-0 z-50 mt-1">
      <div className={cn(
        "rounded-md border border-gray-200 bg-white p-1 shadow-md dark:border-gray-800 dark:bg-gray-950",
        className
      )}>
        {children}
      </div>
    </div>
  )
}

const SelectItem: React.FC<SelectItemProps> = ({ value, children, className }) => {
  const context = React.useContext(SelectContext)
  if (!context) throw new Error("SelectItem must be used within Select")

  const isSelected = context.value === value

  return (
    <button
      className={cn(
        "relative flex w-full cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none focus:bg-gray-100 focus:text-gray-900 data-[disabled]:pointer-events-none data-[disabled]:opacity-50 dark:focus:bg-gray-800 dark:focus:text-gray-50",
        isSelected && "bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-50",
        className
      )}
      onClick={() => {
        context.onValueChange(value)
        context.setOpen(false)
      }}
    >
      {children}
    </button>
  )
}

const SelectValue: React.FC<SelectValueProps> = ({ placeholder, className }) => {
  const context = React.useContext(SelectContext)
  if (!context) throw new Error("SelectValue must be used within Select")

  return (
    <span className={cn("block truncate", className)}>
      {context.value || placeholder}
    </span>
  )
}

export { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } 