import type { Metadata } from "next";
import { AppPage, PageHeader } from "../../../components/app-primitives";
import { AccountDetails } from "./account-details";

export const metadata: Metadata = { title: "Account" };

export default function AccountPage() {
  return (
    <AppPage>
      <PageHeader
        title="Account"
        description="Your signed-in Bismark identity."
      />
      <AccountDetails />
    </AppPage>
  );
}
