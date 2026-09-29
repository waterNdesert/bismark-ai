import type { Metadata } from "next";
import {
  AppPage,
  PageHeader,
  AppPanel,
  EmptyState,
  AppButton,
  StatusBadge,
} from "../../../components/app-primitives";
import { MembersIcon } from "../../../components/icons";
export const metadata: Metadata = { title: "Members" };
export default function MembersPage() {
  return (
    <AppPage>
      <PageHeader
        title="Members"
        description="The people who can access your workspace knowledge."
        actions={
          <AppButton disabled variant="secondary">
            Invitations coming soon
          </AppButton>
        }
      />
      <AppPanel className="library-panel">
        <div className="section-heading">
          <h2>Workspace access</h2>
          <StatusBadge>Directory coming soon</StatusBadge>
        </div>
        <EmptyState
          icon={<MembersIcon />}
          title="Knowledge works better together"
          description="A member directory and invitation controls are on the way. This view does not yet show your organization’s existing memberships."
        />
        <div className="library-footer">
          Workspace roles: admin and member. Contact your administrator to
          manage current access.
        </div>
      </AppPanel>
    </AppPage>
  );
}
