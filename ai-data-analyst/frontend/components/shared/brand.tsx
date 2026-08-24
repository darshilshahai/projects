import Link from "next/link";
import { SITE_NAME } from "@/lib/constants/site";
import { cn } from "@/lib/utils/cn";

type BrandProps = {
  href?: string;
  compact?: boolean;
  className?: string;
};

export function Brand({
  href = "/",
  compact = false,
  className,
}: BrandProps) {
  return (
    <Link
      href={href}
      className={cn(
        "inline-flex items-baseline font-sans font-semibold tracking-[-0.04em] text-foreground transition-colors duration-150 hover:text-accent",
        compact ? "text-xs" : "text-sm",
        className,
      )}
      aria-label={`${SITE_NAME} home`}
    >
      Query<span className="text-accent">Mint</span>
    </Link>
  );
}
