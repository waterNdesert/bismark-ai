import type { Metadata } from "next";
import {
  AppPage,
  PageHeader,
  AppPanel,
  StatusBadge,
  AppLink,
} from "../../../components/app-primitives";
import {
  UploadIcon,
  GlobeIcon,
  CloudIcon,
  FolderIcon,
  DocumentsIcon,
  SourcesIcon,
} from "../../../components/icons";
export const metadata: Metadata = { title: "Sources" };
const connectors = [
  {
    name: "Website",
    description: "Bring selected website pages into your knowledge space.",
    icon: GlobeIcon,
  },
  {
    name: "Google Drive",
    description: "Keep team files and shared folders connected.",
    icon: CloudIcon,
  },
  {
    name: "Notion",
    description: "Bring your team’s pages and project knowledge together.",
    icon: DocumentsIcon,
  },
  {
    name: "SharePoint",
    description: "Connect your organization’s document libraries.",
    icon: FolderIcon,
  },
  {
    name: "Dropbox",
    description: "Use shared files as a source of team knowledge.",
    icon: SourcesIcon,
  },
];
export default function SourcesPage() {
  return (
    <AppPage>
      <PageHeader
        title="Knowledge sources"
        description="Bring the places your team keeps knowledge into one shared context."
      />
      <AppPanel className="manual-source">
        <div className="source-summary">
          <span className="source-icon">
            <UploadIcon />
          </span>
          <div>
            <div className="source-title">
              <h2>Manual Upload</h2>
              <StatusBadge variant="active">Available</StatusBadge>
            </div>
            <p>
              Start with the files you already have. PDF, Word, text, Markdown
              and HTML.
            </p>
          </div>
        </div>
        <div className="manual-source-action">
          <AppLink href="/app/documents">View document uploads</AppLink>
          <span>Private storage · Workspace access required</span>
        </div>
      </AppPanel>
      <div className="section-heading integration-heading">
        <h2>Connect your tools</h2>
        <span>More ways to bring knowledge together</span>
      </div>
      <div className="source-grid">
        {connectors.map(({ name, description, icon: Icon }) => (
          <AppPanel key={name} className="connector-card">
            <div className="connector-top">
              <span className="source-icon">
                <Icon />
              </span>
              <StatusBadge variant="coming">Coming soon</StatusBadge>
            </div>
            <h2>{name}</h2>
            <p>{description}</p>
          </AppPanel>
        ))}
      </div>
    </AppPage>
  );
}
