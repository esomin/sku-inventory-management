import * as React from "react"
import { cn } from "@/lib/utils"

const NativeSelect = React.forwardRef<
    HTMLSelectElement,
    React.SelectHTMLAttributes<HTMLSelectElement>
>(({ className, children, ...props }, ref) => {
    return (
        <select
            ref={ref}
            className={cn(
                "flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
                className
            )}
            {...props}
        >
            {children}
        </select>
    )
})
NativeSelect.displayName = "NativeSelect"

const NativeSelectOption = React.forwardRef<
    HTMLOptionElement,
    React.OptionHTMLAttributes<HTMLOptionElement>
>(({ className, ...props }, ref) => {
    return (
        <option
            ref={ref}
            className={cn("", className)}
            {...props}
        />
    )
})
NativeSelectOption.displayName = "NativeSelectOption"

export { NativeSelect, NativeSelectOption }
