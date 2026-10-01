import type { Metadata } from "next";
import {
  AppPage,
  PageHeader,
  AppPanel,
  EmptyState,
  StatusBadge,
} from "../../../components/app-primitives";
import { DocumentsIcon } from "../../../components/icons";
import { UploadAction } from "../../../components/upload-action";
export const metadata: Metadata = { title: "Documents" };
export default function DocumentsPage() {
  return (
    <AppPage>
      <PageHeader
        title="Documents"
        description="The reference material behind your workspace knowledge."
        actions={<UploadAction buttonLabel="Upload document" />}
      />
      <AppPanel className="library-panel">
        <div className="section-heading">
          <h2>Document library</h2>
          <StatusBadge>Listing coming soon</StatusBadge>
        </div>
        <EmptyState
          icon={<DocumentsIcon />}
          title="A home for your reference material"
          description="Uploads are stored for this workspace. The persistent document list is not available in this view yet."
        />
        <div className="library-footer">
          <span>PDF · DOCX · TXT · Markdown · HTML</span>
          <span>Private, workspace-scoped storage</span>
        </div>
      </AppPanel>
    </AppPage>
  );
}
