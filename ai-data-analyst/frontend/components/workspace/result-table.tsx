import { formatNumber } from "@/lib/utils/format";
import { cn } from "@/lib/utils/cn";

type ResultTableProps = {
  columns: string[];
  rows: Record<string, unknown>[];
  rowCount: number;
  className?: string;
};

export function ResultTable({
  columns,
  rows,
  rowCount,
  className,
}: ResultTableProps) {
  return (
    <div className={cn("border border-border-subtle", className)}>
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-border-subtle">
              {columns.map((column) => (
                <th
                  key={column}
                  className="sticky top-0 bg-background-panel px-4 py-3 font-mono text-[10px] tracking-[0.12em] text-muted uppercase"
                >
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr
                key={`row-${rowIndex}`}
                className="border-b border-border-subtle last:border-b-0"
              >
                {columns.map((column) => (
                  <td
                    key={`${rowIndex}-${column}`}
                    className={cn(
                      "px-4 py-3 text-sm text-muted-strong",
                      typeof row[column] === "number" &&
                        "text-right font-mono tabular-nums",
                    )}
                  >
                    {formatCellValue(row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="border-t border-border-subtle px-4 py-2 font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
        {formatNumber(rowCount)} {rowCount === 1 ? "row" : "rows"} returned
      </div>
    </div>
  );
}

function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "—";
  }

  if (typeof value === "number") {
    return formatNumber(value);
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
}
