import {
  Brand,
  CopyButton,
  SectionLabel,
  StatusDot,
  TechnicalLabel,
} from "@/components/shared";
import { PreviewChart } from "./preview-chart";
import { SectionReveal } from "./section-reveal";

const MOCK_SQL = `SELECT
  region,
  SUM(revenue) AS total_revenue
FROM dataset
GROUP BY region
ORDER BY total_revenue DESC;`;

const MOCK_COLUMNS = ["region", "total_revenue"] as const;
const MOCK_ROWS = [
  { region: "North", total_revenue: 515000 },
  { region: "West", total_revenue: 340000 },
  { region: "South", total_revenue: 299000 },
] as const;

export function ProductPreview() {
  return (
    <SectionReveal>
      <section className="border-b border-border-subtle">
        <div className="mx-auto max-w-7xl px-6 py-20 md:px-10 md:py-28">
          <SectionLabel index="04" trailing="WORKSPACE PREVIEW">
            PRODUCT PREVIEW
          </SectionLabel>

          <div className="mt-10 border border-border-subtle bg-background-panel">
            <div className="flex flex-col gap-2 border-b border-border-subtle px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
              <Brand compact />
              <div className="font-mono text-[10px] tracking-[0.12em] text-muted-strong uppercase">
                SALES.CSV / 10 ROWS / 7 COLUMNS
              </div>
              <StatusDot tone="online" label="ENGINE ONLINE" />
            </div>

            <div className="grid lg:grid-cols-[280px_minmax(0,1fr)]">
              <aside className="border-b border-border-subtle p-5 lg:border-r lg:border-b-0">
                <TechnicalLabel tone="accent">DATASET / ACTIVE</TechnicalLabel>
                <p className="mt-4 font-sans text-sm text-foreground">sales.csv</p>

                <dl className="mt-6 space-y-2 font-mono text-[11px] tracking-[0.08em] text-muted-strong">
                  <div className="flex justify-between gap-4">
                    <dt className="text-muted uppercase">Rows</dt>
                    <dd>10</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-muted uppercase">Columns</dt>
                    <dd>7</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-muted uppercase">Size</dt>
                    <dd>482B</dd>
                  </div>
                </dl>

                <div className="mt-8 border-t border-border-subtle pt-5">
                  <TechnicalLabel>SCHEMA / 07</TechnicalLabel>
                  <ul className="mt-4 divide-y divide-border-subtle">
                    {[
                      ["order_id", "BIGINT"],
                      ["order_date", "VARCHAR"],
                      ["region", "VARCHAR"],
                      ["revenue", "BIGINT"],
                    ].map(([name, type]) => (
                      <li
                        key={name}
                        className="flex items-baseline justify-between gap-3 py-2"
                      >
                        <span className="text-sm text-foreground">{name}</span>
                        <span className="font-mono text-[10px] tracking-widest text-muted uppercase">
                          {type}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </aside>

              <div className="p-5 md:p-6">
                <div className="space-y-6">
                  <div className="space-y-3 border border-border-subtle p-4">
                    <TechnicalLabel tone="muted">ASK YOUR DATA</TechnicalLabel>
                    <p className="text-sm text-muted-strong">
                      Show total revenue by region as a bar chart.
                    </p>
                  </div>

                  <div className="space-y-4 border border-border-subtle p-5">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <SectionLabel index={1}>ANALYSIS</SectionLabel>
                      <StatusDot tone="online" label="EXECUTED" />
                    </div>

                    <p className="text-sm text-muted">
                      Show total revenue by region as a bar chart.
                    </p>

                    <div className="space-y-1">
                      <p className="text-display text-4xl text-foreground md:text-5xl">
                        North
                      </p>
                      <p className="font-mono text-2xl tracking-[-0.02em] text-accent md:text-3xl">
                        ₹515,000
                      </p>
                      <p className="text-sm text-muted-strong">
                        generated the highest revenue.
                      </p>
                    </div>
                  </div>

                  <PreviewChart />

                  <div className="space-y-3 border border-border-subtle">
                    <div className="flex items-center justify-between gap-3 border-b border-border-subtle px-4 py-3">
                      <TechnicalLabel>EXECUTED QUERY</TechnicalLabel>
                      <CopyButton value={MOCK_SQL} label="COPY SQL" />
                    </div>
                    <pre className="overflow-x-auto px-4 py-4 font-mono text-xs leading-relaxed text-muted-strong">
                      <code>{MOCK_SQL}</code>
                    </pre>
                  </div>

                  <div className="border border-border-subtle">
                    <div className="overflow-x-auto">
                      <table className="min-w-full border-collapse text-left">
                        <thead>
                          <tr className="border-b border-border-subtle">
                            {MOCK_COLUMNS.map((column) => (
                              <th
                                key={column}
                                className="px-4 py-3 font-mono text-[10px] tracking-[0.12em] text-muted uppercase"
                              >
                                {column}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {MOCK_ROWS.map((row) => (
                            <tr key={row.region} className="border-b border-border-subtle">
                              <td className="px-4 py-3 text-sm text-foreground">
                                {row.region}
                              </td>
                              <td className="px-4 py-3 text-right font-mono text-sm text-muted-strong tabular-nums">
                                {row.total_revenue}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <div className="border-t border-border-subtle px-4 py-2 font-mono text-[10px] tracking-[0.12em] text-muted uppercase">
                      3 ROWS RETURNED
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </SectionReveal>
  );
}
