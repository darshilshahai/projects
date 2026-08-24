import { DashboardShell } from "@/components/dashboard/dashboard-shell";
import { InvestigationPanel } from "@/components/dashboard/investigation-panel";

export default function DashboardPage() {
  return (
    <DashboardShell>
      <InvestigationPanel />
    </DashboardShell>
  );
}
