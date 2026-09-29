import type { Metadata } from "next";
import {
  AppPage,
  PageHeader,
  AppPanel,
  StatusBadge,
} from "../../../components/app-primitives";
export const metadata: Metadata = { title: "Usage" };
export default function UsagePage() {
  return (
    <AppPage>
      <PageHeader
        title="Usage"
        description="Understand how your team uses its knowledge space."
      />
      <div className="usage-notice">
        <StatusBadge>Reporting coming soon</StatusBadge>
        <p>
          Usage measurement is not connected. No activity or limits are
          estimated here.
        </p>
      </div>
      <div className="usage-grid">
        {[
          {
            title: "Questions",
            text: "Questions asked across your workspace.",
          },
          {
            title: "Documents processed",
            text: "Files prepared for search and answers.",
          },
          { title: "Storage", text: "Space used by your original documents." },
          {
            title: "AI usage",
            text: "Processing and answer-generation activity.",
          },
        ].map((item) => (
          <AppPanel key={item.title}>
            <h2>{item.title}</h2>
            <div className="unavailable-value">Not available</div>
            <p>{item.text}</p>
          </AppPanel>
        ))}
      </div>
    </AppPage>
  );
}
