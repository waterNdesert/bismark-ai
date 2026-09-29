"use client";
import {
  AppPage,
  PageHeader,
  AppPanel,
  StatusBadge,
  AppLink,
} from "../../../components/app-primitives";
import { useProfile } from "../../../components/app-session";
export default function SettingsPage() {
  const profile = useProfile();
  return (
    <AppPage>
      <PageHeader
        title="Settings"
        description="Your account, workspace and knowledge preferences."
      />
      <div className="settings-layout">
        <nav aria-label="Settings sections">
          {["Account", "Workspace", "Security", "Data & sources", "Plan"].map(
            (name, index) => (
              <a href={`#settings-${index}`} key={name}>
                {name}
              </a>
            ),
          )}
        </nav>
        <div className="settings-sections">
          <AppPanel>
            <h2 id="settings-0">Account</h2>
            <p>Your signed-in identity.</p>
            <dl className="settings-fields">
              <div>
                <dt>Name</dt>
                <dd>{profile?.display_name || "Not set"}</dd>
              </div>
              <div>
                <dt>Email</dt>
                <dd>{profile?.email}</dd>
              </div>
            </dl>
          </AppPanel>
          <AppPanel>
            <h2 id="settings-1">Workspace</h2>
            <p>
              Workspace selection and editing are coming soon. Contact your
              administrator for access to an existing workspace.
            </p>
            <AppLink href="/app/members" secondary>
              View member information
            </AppLink>
          </AppPanel>
          <AppPanel>
            <h2 id="settings-2">Security</h2>
            <p>
              Use the account menu to sign out of this browser. To reset your
              password, sign out and choose “Forgot password?” on the sign-in
              screen.
            </p>
          </AppPanel>
          <AppPanel>
            <h2 id="settings-3">Data & sources</h2>
            <p>Review available upload formats and upcoming integrations.</p>
            <AppLink href="/app/sources" secondary>
              Manage knowledge sources
            </AppLink>
          </AppPanel>
          <AppPanel>
            <div className="section-heading">
              <h2 id="settings-4">Plan & billing</h2>
              <StatusBadge>Coming soon</StatusBadge>
            </div>
            <p>No plan, billing or payment controls are available yet.</p>
          </AppPanel>
        </div>
      </div>
    </AppPage>
  );
}
