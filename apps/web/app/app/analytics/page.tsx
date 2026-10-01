import type { Metadata } from "next";
import {
  AppPage,
  AppPanel,
  EmptyState,
  PageHeader,
} from "../../../components/app-primitives";
import { AnalyticsIcon } from "../../../components/icons";

export const metadata: Metadata = { title: "Analytics" };

export default function AnalyticsPage() {
  return (
    <AppPage>
      <PageHeader
        title="Analytics"
        description="A view of activity across your organization’s knowledge."
      />
      <AppPanel>
        <EmptyState
          icon={<AnalyticsIcon />}
          title="Analytics will appear as your workspace activity grows."
          description="There is no activity data to show yet."
        />
      </AppPanel>
    </AppPage>
  );
}
