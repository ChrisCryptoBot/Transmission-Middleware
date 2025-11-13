/**
 * VEGUS Professional Badge Component
 * Status indicators with glassmorphism design
 */

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-lg px-3 py-1 text-xs font-semibold transition-all duration-200",
  {
    variants: {
      variant: {
        default:
          "glass border border-indigo-500/50 text-indigo-200 bg-indigo-500/10",
        secondary:
          "glass border border-neutral-500/50 text-neutral-200 bg-neutral-500/10",
        success:
          "glass border border-green-500/50 text-green-200 bg-green-500/10",
        destructive:
          "glass border border-red-500/50 text-red-200 bg-red-500/10",
        warning:
          "glass border border-amber-500/50 text-amber-200 bg-amber-500/10",
        outline:
          "border border-white/20 text-neutral-300 bg-transparent",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
