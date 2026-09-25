import Account from "../components/account";

export default function Home() {
  return (
    <main className="account-layout">
      <header className="brand">Bismark AI</header>
      <div className="account-content">
        <section className="introduction" aria-labelledby="intro-heading">
          <div className="document-mark" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
          <h1 id="intro-heading">A place for your organization’s knowledge.</h1>
          <p>
            Start with your account. Bring your team’s knowledge together as
            your workspace takes shape.
          </p>
        </section>
        <Account />
      </div>
      <footer>Knowledge with context. Answers with sources.</footer>
    </main>
  );
}
