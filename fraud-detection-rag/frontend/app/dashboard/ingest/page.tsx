import { DashboardShell } from "@/components/dashboard/dashboard-shell";
import { IngestPanel } from "@/components/dashboard/ingest-panel";

export default function IngestPage() {
  return (
    <DashboardShell>
      <IngestPanel />
    </DashboardShell>
  );
}
