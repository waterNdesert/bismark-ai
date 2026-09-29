import type { Metadata } from "next";
import Link from "next/link";
import {
  AppPage,
  PageHeader,
  AppPanel,
  AppLink,
  StatusBadge,
} from "../../components/app-primitives";
import {
  AskIcon,
  SourcesIcon,
  ConversationsIcon,
  ArrowRightIcon,
} from "../../components/icons";
export const metadata: Metadata = { title: "Overview" };
export default function OverviewPage() {
  return (
    <AppPage>
      <PageHeader
        title="Your knowledge, connected."
        description="A home for your team’s knowledge. Start with the sources that matter."
      />
      <section className="overview-ask">
        <div className="feature-heading">
          <span className="feature-icon">
            <AskIcon />
          </span>
          <StatusBadge>Answering coming soon</StatusBadge>
        </div>
        <h2>What would you like to know?</h2>
        <p>
          Bring a question. Bismark is being built to find the answer in your
          organization’s knowledge.
        </p>
        <Link href="/app/ask" className="composer-entry">
          <span>Explore Ask Bismark</span>
          <ArrowRightIcon />
        </Link>
        <div className="feature-footnote">
          Your knowledge. Clear context. Traceable sources.
        </div>
      </section>
      <div className="overview-grid">
        <AppPanel>
          <div className="section-heading">
            <h2>
              <SourcesIcon />
              Knowledge sources
            </h2>
            <Link href="/app/sources">View sources</Link>
          </div>
          <div className="source-summary">
            <span className="workspace-symbol">
              <SourcesIcon />
            </span>
            <div>
              <h3>Start with your documents</h3>
              <p>
                Manual Upload is the first available source. More integrations
                are on the way.
              </p>
            </div>
          </div>
          <AppLink href="/app/documents" secondary>
            Explore document uploads
          </AppLink>
          <p className="support-note">
            Workspace connection is required before uploading in the app.
          </p>
        </AppPanel>
        <AppPanel>
          <div className="section-heading">
            <h2>
              <ConversationsIcon />
              Recent activity
            </h2>
            <StatusBadge>Coming soon</StatusBadge>
          </div>
          <div className="compact-empty">
            <h3>A place to pick up where you left off</h3>
            <p>
              Your conversation history will live here when answering is
              available.
            </p>
            <Link className="inline-link" href="/app/conversations">
              Explore conversations <ArrowRightIcon />
            </Link>
          </div>
        </AppPanel>
      </div>
      <section className="getting-started">
        <h2>Build a useful knowledge space</h2>
        <div className="onboarding-grid">
          <div>
            <span>1</span>
            <h3>Choose your sources</h3>
            <p>
              Identify the policies, guides and reference files your team relies
              on.
            </p>
          </div>
          <div>
            <span>2</span>
            <h3>Bring them together</h3>
            <p>Manual uploads come first. Connected services will follow.</p>
          </div>
          <div>
            <span>3</span>
            <h3>Ask with context</h3>
            <p>Grounded answers and citations are the next step.</p>
          </div>
        </div>
      </section>
    </AppPage>
  );
}
