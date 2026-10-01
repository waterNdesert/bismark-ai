"use client";

import { AppPanel } from "../../../components/app-primitives";
import { useProfile } from "../../../components/app-session";

export function AccountDetails() {
  const profile = useProfile();
  return (
    <AppPanel>
      <h2>Profile</h2>
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
      <p>Sign out from the account menu.</p>
    </AppPanel>
  );
}
