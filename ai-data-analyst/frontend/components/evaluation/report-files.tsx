import { TechnicalLabel } from "@/components/shared";

export function ReportFiles() {
  return (
    <section className="space-y-4 border border-border-subtle p-5 md:p-6">
      <TechnicalLabel>GENERATED REPORTS</TechnicalLabel>

      <div className="space-y-4">
        <div>
          <p className="font-mono text-xs text-foreground">evaluation_report.json</p>
          <p className="mt-1 text-sm text-muted-strong">
            Machine-readable benchmark output
          </p>
          <p className="mt-2 font-mono text-[10px] tracking-[0.1em] text-muted uppercase">
            reports/evaluation_report.json
          </p>
        </div>

        <div className="border-t border-border-subtle pt-4">
          <p className="font-mono text-xs text-foreground">evaluation_report.csv</p>
          <p className="mt-1 text-sm text-muted-strong">
            Spreadsheet-friendly case report
          </p>
          <p className="mt-2 font-mono text-[10px] tracking-[0.1em] text-muted uppercase">
            reports/evaluation_report.csv
          </p>
        </div>
      </div>
    </section>
  );
}
