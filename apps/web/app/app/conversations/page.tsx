import type { Metadata } from "next";
import {
  AppPage,
  PageHeader,
  AppPanel,
  EmptyState,
  AppLink,
  StatusBadge,
} from "../../../components/app-primitives";
import { ConversationsIcon } from "../../../components/icons";
export const metadata: Metadata = { title: "Conversations" };
export default function ConversationsPage() {
  return (
    <AppPage>
      <PageHeader
        title="Conversations"
        description="Keep useful questions and their context close at hand."
      />
      <AppPanel className="library-panel">
        <div className="section-heading">
          <h2>Conversation history</h2>
          <StatusBadge>Coming soon</StatusBadge>
        </div>
        <EmptyState
          icon={<ConversationsIcon />}
          title="Make room for your next discovery"
          description="Saved questions, referenced sources and conversation history will live here. Answering and history aren’t available yet."
          action={
            <AppLink href="/app/ask" secondary>
              Explore Ask Bismark
            </AppLink>
          }
        />
      </AppPanel>
    </AppPage>
  );
}
