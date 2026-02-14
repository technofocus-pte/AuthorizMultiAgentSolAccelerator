"use client";

import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

interface ConfidenceBarProps {
  value: number; // 0-100
  className?: string;
  showLabel?: boolean;
}

export function ConfidenceBar({
  value,
  className,
  showLabel = true,
}: ConfidenceBarProps) {
  const color =
    value >= 80
      ? "[&>[data-slot=progress-indicator]]:bg-green-600"
      : value >= 50
        ? "[&>[data-slot=progress-indicator]]:bg-amber-500"
        : "[&>[data-slot=progress-indicator]]:bg-destructive";

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Progress value={value} className={cn("h-2 flex-1", color)} />
      {showLabel && (
        <span className="text-xs font-medium tabular-nums text-muted-foreground w-10 text-right">
          {Math.round(value)}%
        </span>
      )}
    </div>
  );
}
