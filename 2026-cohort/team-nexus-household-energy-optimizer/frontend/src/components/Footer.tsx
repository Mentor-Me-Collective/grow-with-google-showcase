import { ExternalLink } from "lucide-react";

const REPO_URL =
  "https://github.com/PTreasures/grow-with-google-showcase/tree/team-nexus-collaborative";

export function Footer() {
  return (
    <footer className="site-footer">
      <div className="site-footer-row">
        <div className="footer-brand">
          <img src="/favicon.svg" alt="" width={20} height={19} />
          <div>
            <div className="footer-brand-name">Tenant Power Tracker</div>
            <div className="footer-team">Built by Team Nexus Collaborative</div>
          </div>
        </div>
        <a className="footer-link" href={REPO_URL} target="_blank" rel="noreferrer">
          <ExternalLink size={15} strokeWidth={1.75} />
          View on GitHub
        </a>
      </div>
      <p className="footer-disclaimer">
        Figures are estimates benchmarked against sample EIA.gov usage data, not a
        live utility feed. No account, personal, or bill data is stored, everything here runs
        in this browser session only.
      </p>
    </footer>
  );
}
