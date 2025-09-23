import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-blue-600 text-white shadow-md hover:bg-blue-700 hover:shadow-lg active:bg-blue-800",
        destructive:
          "bg-red-600 text-white shadow-md hover:bg-red-700 hover:shadow-lg active:bg-red-800",
        outline:
          "border border-slate-300 bg-white shadow-sm hover:bg-slate-50 hover:border-slate-400 hover:shadow-md text-slate-700",
        secondary:
          "bg-slate-100 text-slate-700 shadow-sm hover:bg-slate-200 hover:shadow-md active:bg-slate-300",
        ghost: "text-slate-600 hover:bg-slate-100 hover:text-slate-900 active:bg-slate-200",
        link: "text-blue-600 underline-offset-4 hover:underline hover:text-blue-700",
        success: "bg-green-600 text-white shadow-md hover:bg-green-700 hover:shadow-lg active:bg-green-800",
        warning: "bg-amber-600 text-white shadow-md hover:bg-amber-700 hover:shadow-lg active:bg-amber-800",
      },
      size: {
        default: "h-10 px-4 py-2 text-sm",
        sm: "h-8 px-3 text-xs",
        lg: "h-12 px-6 text-base font-semibold",
        xl: "h-14 px-8 text-lg font-semibold",
        icon: "h-9 w-9",
        "icon-sm": "h-8 w-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }