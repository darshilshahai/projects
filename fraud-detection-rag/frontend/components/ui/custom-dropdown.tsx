"use client";

import { Check, ChevronDown } from "lucide-react";
import {
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import { createPortal } from "react-dom";
import type { DropdownOption } from "@/lib/types";
import { useFloatingPosition } from "@/lib/use-floating-position";
import { cn } from "@/lib/utils";

interface CustomDropdownProps {
  label?: string;
  value: string;
  options: DropdownOption[];
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

export function CustomDropdown({
  label,
  value,
  options,
  onChange,
  placeholder = "Select option",
  className,
  disabled = false,
}: CustomDropdownProps) {
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [highlighted, setHighlighted] = useState(0);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const listId = useId();
  const panelStyle = useFloatingPosition(open, triggerRef);

  const selected = options.find((option) => option.value === value);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      const target = event.target as Node;

      if (
        triggerRef.current?.contains(target) ||
        panelRef.current?.contains(target)
      ) {
        return;
      }

      setOpen(false);
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (open) {
      const index = options.findIndex((option) => option.value === value);
      setHighlighted(index >= 0 ? index : 0);
    }
  }, [open, options, value]);

  function selectOption(index: number) {
    const option = options[index];
    if (!option) return;
    onChange(option.value);
    setOpen(false);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (disabled) return;

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      setOpen((current) => !current);
      return;
    }

    if (!open) return;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setHighlighted((current) => (current + 1) % options.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setHighlighted(
        (current) => (current - 1 + options.length) % options.length,
      );
    } else if (event.key === "Enter") {
      event.preventDefault();
      selectOption(highlighted);
    } else if (event.key === "Escape") {
      setOpen(false);
    }
  }

  const panel =
    open && mounted ? (
      <div
        ref={panelRef}
        id={listId}
        role="listbox"
        style={panelStyle}
        className="animate-scale-in overflow-hidden rounded-2xl border border-border bg-card-elevated p-1.5 shadow-[var(--shadow-lg)]"
      >
        {options.map((option, index) => {
          const isSelected = option.value === value;
          const isHighlighted = index === highlighted;

          return (
            <button
              key={option.value}
              type="button"
              role="option"
              aria-selected={isSelected}
              onMouseEnter={() => setHighlighted(index)}
              onClick={() => selectOption(index)}
              className={cn(
                "flex w-full items-start justify-between gap-3 rounded-xl px-3 py-2.5 text-left transition-colors",
                isHighlighted && "bg-primary-soft",
                isSelected && "bg-primary-soft/80",
              )}
            >
              <div>
                <p className="text-sm font-medium text-foreground">
                  {option.label}
                </p>
                {option.description ? (
                  <p className="mt-0.5 text-xs text-muted">
                    {option.description}
                  </p>
                ) : null}
              </div>
              {isSelected ? (
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
              ) : null}
            </button>
          );
        })}
      </div>
    ) : null;

  return (
    <div className={cn(className)}>
      {label ? (
        <label className="mb-2 block text-sm font-medium text-foreground">
          {label}
        </label>
      ) : null}

      <button
        ref={triggerRef}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        disabled={disabled}
        onClick={() => setOpen((current) => !current)}
        onKeyDown={handleKeyDown}
        className={cn(
          "flex h-11 w-full items-center justify-between rounded-xl border border-border bg-card px-4 text-left text-sm transition-colors focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)]",
          open && "border-primary shadow-sm",
          disabled && "cursor-not-allowed opacity-60",
        )}
      >
        <span className={cn(!selected && "text-muted")}>
          {selected?.label ?? placeholder}
        </span>
        <ChevronDown
          className={cn(
            "h-4 w-4 text-muted transition-transform duration-200",
            open && "rotate-180 text-primary",
          )}
        />
      </button>

      {mounted && panel ? createPortal(panel, document.body) : null}
    </div>
  );
}
