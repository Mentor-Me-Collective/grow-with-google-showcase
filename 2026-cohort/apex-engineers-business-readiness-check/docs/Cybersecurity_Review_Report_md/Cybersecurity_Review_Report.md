# Cybersecurity Review Report: Business Readiness Check

Assigned project topic: Small Business Tech-Stack Diagnostic Tool

Framework: NIST Cybersecurity Framework 2.0 (Reference Framework)

Alignment: UN SDG Goal 9 - Industry, Innovation, and Infrastructure

## Scope and Implementation Status

This document preserves Sukanya Karri's cybersecurity review and proposed
roadmap. It distinguishes safeguards present in the submitted application from
recommendations that would require future application or organizational work.

**Present in the submitted application:** fixed assessment choices including
Not applicable, required scored answers, length-limited optional text, plain-text
report generation, no application database or accounts, no file uploads or
external APIs, privacy and limitation notices, pinned dependencies, and HTTPS
through the Render deployment.

**Proposed rather than implemented:** three additional security-readiness
questions, a custom inactivity timeout and warning, application security-event
logging and a retention policy, scheduled dependency audits, explicit security
header configuration, and organization-level incident-response and recovery
procedures.

## Executive Summary

This security review examines the Python and Streamlit diagnostic tool for
small-business owners. The tool assesses four technology gaps identified in the
project analysis: inventory synchronization, digital payments, customer email
capture, and online booking capabilities. Research indicates that 56% of US
small businesses experienced cyber attacks in the past year, while Verizon's
2025 DBIR reported ransomware in 88% of breaches affecting SMBs [1][14]. The
submitted application uses a data-minimization approach and does not
intentionally persist assessment responses in an application database.

## Small Business Threat Landscape

![figure-01.png](images/figure-01.png)

*Small Business Cyber Attack Statistics (2026)*

> **Research-visualization note:** Figures 1-5 preserve the contributor's
> original research visuals. Source `[10]`, printed inside some images, is kept
> for provenance but was not independently confirmed during final repository
> review. Values that rely only on that source are contextual research claims,
> not application requirements or scoring evidence. Verified primary-source
> comparisons are identified separately in sources `[14]` and `[15]`.

![figure-02.png](images/figure-02.png)

*Ransomware Impact on Small Businesses. The 88%, 39%, and 44% ransomware
figures align with Verizon's 2025 DBIR [14]. The cost callouts shown in the
image remain original research claims from [10] and are not used by the
application.*

![figure-03.png](images/figure-03.png)

*Small Business Security Posture Gaps*

This data, drawn from current small business cybersecurity research, frames why the controls in this review matter: connected IoT devices are the leading entry point for attacks (30%) [1], and 40% of quick service restaurants had payment card data leaked in the past year [4].

### Attack Progression

![figure-04.png](images/figure-04.png)

*Small Business Attack Chain Analysis. The 241-day global mean for identifying
and containing a breach is supported by IBM's 2025 report [15]. Other numerical
callouts in this contributed visual remain contextual research claims.*

## Project Fragmentation Tax Security Analysis

![figure-05.png](images/figure-05.png)

*Third-Party Risk Exposure. The visual's 55% callout is preserved from the
original contributed source [10]. Verizon's 2025 DBIR independently reported
30% third-party involvement in breaches [14], so the application does not use a
third-party percentage in its scoring or recommendations.*

Third-party dependencies map directly onto this project's four technology gaps: POS integrations relate to the inventory sync gap, payment processors to the digital payments gap, email providers to the customer email gap, and booking platforms to the online booking gap. The table below sets out each gap in full.

| Technology Gap | Business Impact | Risk if “No” | Security Implication |
|---|---|---|---|
| Inventory Sync (Weight 5) | 12% of catalog at or below its reorder point | High | POS system vulnerabilities, credential protection |
| Digital Payments (Weight 4) | Digital wallets already exceed 10,000 transactions | Medium | PCI compliance, payment fraud prevention |
| Customer Email (Weight 3) | 8.65% unverified email status; $3.9M in associated revenue | Medium | Data minimization, privacy controls (breach cost $4.44M) [5] |
| Online Booking (Weight 2) | Beauty & Health revenue exceeds $2.6M; booking need is an assumption | Low-Medium | Account separation, availability controls |

The four identified technology gaps from the project analysis have the specific
security implications above. Their application weights come from the team's
e-commerce analysis and Tableau dashboard rather than from NIST or the
cybersecurity statistics in this report [11].

## Security Questions & Responses

![figure-06.png](images/figure-06.png)

*Security-Enhanced Diagnostic Flow*

The figure combines the submitted assessment flow with proposed security
enhancements. The four technology questions, weighted calculation, gap
identification, recommendations, and security checkpoints are present. The
three additional security questions shown in Layer 1 remain future work.

### 1. Information Collection Guidelines

- COLLECT: Optional business name and general business type, operational status
  (Yes/No/Not applicable responses to four diagnostic questions), and weighted
  risk results (0-14 applicable points before percentage conversion)
- PROHIBITED: Passwords, payment card data, customer PII, API keys, transaction records
- IP ADDRESS POLICY: The application will not intentionally collect or persist IP addresses as part of the diagnostic dataset. Infrastructure-level logs may contain connection metadata depending on the hosting platform.

### 2. Assessment Answer Storage

- Process answers in the active Streamlit session. The application has no
  database and does not intentionally persist assessment responses. The hosting
  platform and Streamlit runtime, rather than application code, control session
  lifecycle and infrastructure logs.
- Current Privacy Notice: "This version does not require an account and does not
  intentionally store your answers. Do not enter passwords, payment-card
  details, customer records, or other sensitive information."
- This data-minimization approach reduces the amount of application data that
  could be exposed and is consistent with the baseline-practice concerns in [3].
- Future option: evaluate a custom inactivity timeout only if the application
  later stores sensitive state or adds accounts.

### 3. Input Validation & Safe Report Generation

- Input Validation: Validate that diagnostic answers map only to Yes, No, or Not
  applicable and that calculated applicable points remain within 0-14
- Weight Calculation: The four defined weights are 5, 4, 3, and 2; scoring
  validation enforces the known questions and answer values
- Business Type Choices: Retail storefront, e-commerce, retail and e-commerce,
  service-based business, or Other; business type is optional and non-scored
- Streamlit Security: Keep user-supplied text out of HTML rendering. The current
  `unsafe_allow_html=True` calls render reviewed static layout markup only, not
  business-name or assessment-answer values [6]

### 4. Privacy and Security Notices

- Current notice: no account is required, answers are not intentionally stored,
  and users must not enter passwords, payment-card details, customer records, or
  other sensitive information
- Current results disclaimer: the output is general guidance rather than a
  formal security, financial, compliance, or technology audit
- Future option: add a session-timeout indicator only if a custom timeout is
  implemented and tested

### 5. Secure Deployment & Dependencies

- HTTPS/TLS: Deploy behind HTTPS/TLS using the hosting platform's supported secure configuration; prefer modern TLS versions and disable obsolete protocols where configurable
- Current Platform: Render Web Service with managed HTTPS/TLS termination
- Dependency Management: Pin exact dependency versions in `requirements.txt`;
  review dependency advisories before releases and consider a scheduled audit
  if the project becomes actively maintained
- Secrets Management: Use environment variables or Streamlit Secrets - never in source control [6]
- Request Protection: Preserve Streamlit's protective CORS and XSRF defaults;
  review explicit configuration only if deployment requirements change

### 6. Error Handling & Logging

- Current behavior: handle expected validation errors in the interface without
  intentionally logging user responses
- Future option: if application security-event logging is added, define events,
  access controls, sensitive-data filtering, retention, and deletion as one
  reviewed operational policy rather than assuming a 30-day period

### 7. File Upload Protection (Future Enhancement)

- Current diagnostic does not require file upload. If introduced later: extension allowlist → 5MB size limit → filename sanitization → malware scanning → sandboxed processing → temporary storage → delete after processing
- Security Note: Streamlit's caching/session mechanisms can involve Python pickle, which should never be used to deserialize untrusted data [6].

## Business Report Security Recommendations

![figure-07.png](images/figure-07.png)

*Technology Gap Risk Prioritization*

| Gap | Modernization | Security Action |
|---|---|---|
| Inventory Sync | POS integration | Credential protection, least privilege, updates |
| Digital Payments | Digital wallets | Reputable providers, no card data storage, MFA |
| Customer Email | Email capture/CRM | Data minimization, access controls, privacy |
| Online Booking | Online calendar | MFA, separate accounts, minimal customer data |

Every modernization recommendation introduces a corresponding security consideration.

## Proposed Cybersecurity Readiness Check

The following three questions are a proposed future enhancement. They are not
part of the submitted application and do not affect its technology-risk score:

- Q1: Do employees use separate accounts rather than sharing one login? (Yes/No)
- Q2: Is important business data backed up regularly? (Yes/No)
- Q3: Is multi-factor authentication enabled for important business accounts? (Yes/No)

Proposed scoring: 3/3 = Strong, 2/3 = Developing, 0-1 = Needs Attention

Top Security Action: Enable MFA for email, payment, and accounting admin accounts. This addresses the 65% MFA adoption gap among SMBs [2].

## NIST CSF 2.0 Framework Alignment

![figure-08.png](images/figure-08.png)

*NIST CSF 2.0 Small Business Implementation*

*This is a reference mapping. Labels for session management, security logging,
incident procedures, and recovery include proposed controls and must not be
read as completed application features.*

| NIST Function | Submitted Application Status |
|---|---|
| Govern | Partial: data-collection boundaries and privacy notices are documented |
| Identify | Partial: operational gaps are identified; this is not a formal NIST risk assessment |
| Protect | Partial: input validation, data minimization, pinned dependencies, and hosted HTTPS are present |
| Detect | Not implemented: no custom security-event monitoring |
| Respond | Not implemented at the application level: expected validation errors are handled, but no incident-response process is included |
| Recover | Not implemented at the application level: provider recovery and organizational continuity remain outside scope |

The security review uses NIST CSF 2.0 as a reference framework [7]. The application does not implement all six NIST functions, as Detect/Respond/Recover are primarily organizational capabilities.

## UN SDG Goal 9 Alignment

- Resilient Infrastructure: Using the NIST Protect function as a reference helps
  the team identify safeguards that can support trust; it does not ensure that
  the diagnostic tool or a participating business is secure
- Inclusive Industrialization: Appropriate security without excessive complexity makes digital modernization accessible to non-technical business owners
- Foster Innovation: Security controls enable safe experimentation with new technologies without exposing businesses to cyber risks

## Security Implementation Roadmap

![figure-09.png](images/figure-09.png)

*Small Business Security Implementation Timeline*

This is the recommended order of implementation, based on the threat data and project analysis above.

## Conclusion

The cybersecurity review fits the Business Readiness Check when it is treated as
a combination of implemented data-minimization safeguards and proposed future
controls. The submitted application stays aligned with the project's four-gap
analysis, supports UN SDG Goal 9, and uses NIST CSF 2.0 as a reference framework
rather than claiming framework compliance. Its lack of accounts, file uploads,
external APIs, and an application database keeps the initial attack surface
small while still delivering the tool's value.

Recommendation: Retain the current safeguards in the current release. Treat the
three-question Cybersecurity Readiness Check, custom session management,
security logging, and organization-level NIST activities as future work that
requires separate design and testing.

## Sources

- [1] Hiscox Cyber Readiness Report 2026: 56% of US small businesses experienced cyber attacks, average 2.38 attempts per business; connected IoT devices are the leading point of entry (30%). [https://www.hiscox.com/documents/Hiscox-Cyber-Readiness-Report-2026.pdf](https://www.hiscox.com/documents/Hiscox-Cyber-Readiness-Report-2026.pdf)
- [2] 2026 SMB Cybersecurity Statistics (Spacelift): 88% of SMB breaches involve ransomware vs. 39% for large organizations; 65% do not use MFA (blocks 99.9% of automated attacks); 43% of all cyberattacks target small businesses; 34% have a formal incident response plan; 11% use AI-powered defenses; 52% rely on untrained staff to manage cybersecurity. [https://spacelift.io/blog/small-business-cybersecurity-statistics](https://spacelift.io/blog/small-business-cybersecurity-statistics)
- [3] SensCy 2026 SMB Benchmark Report: 93% of SMBs fail to follow baseline cybersecurity practices; 107% improvement possible with structured action. [https://senscy.com/new-study-finds-93-of-smbs-fail-to-follow-baseline-cybersecurity-practices/](https://senscy.com/new-study-finds-93-of-smbs-fail-to-follow-baseline-cybersecurity-practices/)
- [4] VikingCloud 2026 Quick Service Restaurant Report: 40% had payment card data leaked, 80% experienced cyber incidents. [https://cybersecuritystats.com/reports/vikingcloud/cyber-risk-supersized-vikingcloud-s-2026-quick-service-fast-casual-restaurant-report](https://cybersecuritystats.com/reports/vikingcloud/cyber-risk-supersized-vikingcloud-s-2026-quick-service-fast-casual-restaurant-report)
- [5] Vantage Point CRM Security Guide 2026: average data breach cost $4.44 million globally, security reduces risk by 70%. [https://vantagepoint.io/blog/sf/crm-data-security-best-practices-2026](https://vantagepoint.io/blog/sf/crm-data-security-best-practices-2026)
- [6] Streamlit Documentation - Trust and Security. [https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/trust-and-security](https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/trust-and-security)
- [7] NIST CSF 2.0 Core Publication. [https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=957258](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=957258)
- [8] NIST CSF Tools Visualizations. [https://csf.tools/visualizations/](https://csf.tools/visualizations/)
- [9] Trend Micro, “Point-of-Sale System Breaches: Threats to the Retail and Hospitality Industries” — memory-scraping malware targets POS terminals globally. [https://documents.trendmicro.com/assets/wp/wp-pos-system-breaches.pdf](https://documents.trendmicro.com/assets/wp/wp-pos-system-breaches.pdf)
- [10] CyFlare, “SMB Threat Landscape Report.” This is the original contributed source for several statistics embedded in figures 1-5. The final repository review could access the page but could not independently confirm its displayed values, so those figures are preserved as contextual research rather than scoring evidence. [https://cyflare.com/smb-threat-landscape-report/](https://cyflare.com/smb-threat-landscape-report/)
- [11] Project Report: Small Business Tech-Stack Diagnostic Tool, Team Apex Engineers, 2026. Fragmentation Tax analysis of 100,000+ e-commerce transactions. Internal project document. Interactive dashboard: [https://public.tableau.com/views/SmallBusinessTech-StackDiagnosticToolbyTeamApexEngineer/SmallBusinessTech-StackDiagnosticTool](https://public.tableau.com/views/SmallBusinessTech-StackDiagnosticToolbyTeamApexEngineer/SmallBusinessTech-StackDiagnosticTool)
- [12] SBE Council Small Business Technology Use Survey, March 2026: found high small-business adoption of digital tools, not low adoption as earlier drafts of this review stated — 82% of employers use AI tools and 90% report confidence adopting new digital tools. Referenced in [11]. [https://sbecouncil.org/wp-content/uploads/2026/03/SBE-Technology-Use-Survey-March-2026-Final-2.pdf](https://sbecouncil.org/wp-content/uploads/2026/03/SBE-Technology-Use-Survey-March-2026-Final-2.pdf)
- [13] Lendio Study: mom-and-pop businesses show an average credit score 30 points lower and monthly revenue about $35,000 lower than other small businesses. Referenced in [11]. [https://www.lendio.com/blog/study-mom-and-pop-businesses](https://www.lendio.com/blog/study-mom-and-pop-businesses)
- [14] Verizon, “2025 Data Breach Investigations Report.” Reports third-party involvement in 30% of breaches, ransomware in 44% of reviewed breaches, ransomware in 39% of large-organization breaches, and ransomware in 88% of SMB breaches. [https://www.verizon.com/business/resources/T850/reports/2025-dbir-data-breach-investigations-report.pdf](https://www.verizon.com/business/resources/T850/reports/2025-dbir-data-breach-investigations-report.pdf)
- [15] IBM, “2025 Cost of a Data Breach Report.” Reports a $4.44 million global average breach cost and a 241-day mean time to identify and contain a breach. [https://www.ibm.com/think/x-force/2025-cost-of-a-data-breach-navigating-ai](https://www.ibm.com/think/x-force/2025-cost-of-a-data-breach-navigating-ai)

The project-specific technology-gap figures are checked against the Tableau
dashboard and Project Report [11]. Cybersecurity statistics are cited separately
and are not used to calculate the Business Readiness Check score.
