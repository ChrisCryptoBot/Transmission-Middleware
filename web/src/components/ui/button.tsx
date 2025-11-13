/**
 * VEGUS Professional Button Component
 * Glassmorphism design with multiple variants
 */

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none",
  {
    variants: {
      variant: {
        primary: "gradient-primary text-white hover:shadow-lg hover:scale-105 focus-visible:ring-indigo-500",
        secondary: "glass border-2 border-white/20 text-white hover:border-white/40 hover:bg-white/10 focus-visible:ring-purple-500",
        success: "gradient-success text-white hover:shadow-lg hover:scale-105 focus-visible:ring-green-500",
        danger: "gradient-danger text-white hover:shadow-lg hover:scale-105 focus-visible:ring-red-500",
        ghost: "bg-transparent border border-neutral-700 text-neutral-300 hover:bg-white/5 hover:border-neutral-600 focus-visible:ring-neutral-500",
        link: "text-indigo-400 hover:text-indigo-300 underline-offset-4 hover:underline",
      },
      size: {
        default: "h-11 px-6 py-3 rounded-xl text-sm",
        sm: "h-9 px-4 py-2 rounded-lg text-xs",
        lg: "h-13 px-8 py-4 rounded-xl text-base",
        icon: "h-11 w-11 rounded-xl",
      },
    },
    defaultVariants: {
      variant: "primary",
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
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
