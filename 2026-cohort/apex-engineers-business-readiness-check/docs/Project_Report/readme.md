# Project Report: Small Business Tech-Stack Diagnostic Tool

## Team Apex Engineers

**Assigned Project Topic:** Small Business Tech-Stack Diagnostic Tool

**Alignment:** UN SDG Goal 9: Industry, Innovation, and Infrastructure

**Problem Statement:** Traditional retail storefronts lack an automated methodology to audit and modernize legacy administrative software, resulting in significant operational inefficiencies.

**Implemented solution:** Business Readiness Check

---

## 1.0 Executive Summary

This report outlines a comprehensive modernization blueprint designed to transition independent retail storefronts from fragmented legacy systems to integrated digital infrastructures. Through four phases—Market Research, Data Auditing, Impact Analysis, and Solution Development—this project establishes a structured diagnostic framework to automate the modernization path for small-scale enterprises.

## 2.0 Market Research & Problem Definition

Empirical research indicates that independent retailers face critical disadvantages due to technological gaps. Key findings reveal that these businesses often experience lower monthly revenue and credit scores than tech-forward competitors. Operationally, the reliance on manual processes hinders their ability to compete with large-scale logistics and limits customer personalization capabilities.

## 3.0 Data Auditing & Methodology

To demonstrate what a modernized data infrastructure looks like and validate the proposed solution, a raw global e-commerce dataset (encompassing transactions, customers, inventory, products, marketing, and supplier costs) was systematically audited and cleaned. This methodology involved three primary stages:

- **Environment Initialization:** Core datasets were duplicated to preserve integrity during the transformation process.
- **Data Standardization:** Deduplication and formatting ensured consistent dates and text casing across all records.
- **Validation:** Flagging invalid entries and applying grid standards created an actionable foundation for analysis.

## 4.0 Impact Analysis: The Fragmentation Tax

Analysis of the cleaned data identified a "Fragmentation Tax" — the hidden costs associated with disconnected systems:

- **Inventory Discrepancy (The Manual Reconciling Trap):** 12% of the catalog is currently at risk of stockouts. Without automated communication between physical registers and online storefronts, businesses rely on manual updates, which practically guarantees overselling errors and logistical failure.

- **Payment Friction (Hidden Transaction Friction):** Failure to support modern digital wallets (like Apple Pay) risks alienating a growing customer base. Although traditional credit cards dominate, digital wallets already account for over 10,000 transactions; failing to modernize these checkout methods increases cart abandonment and loses potential revenue.

- **Marketing Silos (Ghost Customers):** Disconnected POS systems lead to "Ghost Customers" — 8.65% of the customer base with unverified or missing email addresses. These disconnected profiles account for over $3.9 million in inaccessible revenue, as legacy systems fail to pipe data into marketing engines for automated retention or win-back campaigns.

- **Service Silos (Service Calendaring Silos):** Manual booking processes in high-revenue categories (e.g., Health & Beauty, which generated over $2.6M) create extreme customer friction. A lack of 24/7 digital booking integration prevents efficient scheduling and negatively impacts revenue in these service-dependent categories.

<p align="center">
<img src="Img/4painpoints.png" title="4 Pain Points" alt="4 Pain Points"> </p>

**[Click here to view interactive dashboard](https://public.tableau.com/views/SmallBusinessTech-StackDiagnosticToolbyTeamApexEngineer/SmallBusinessTech-StackDiagnosticTool?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)**

## 5.0 Solution: Diagnostic Tool Framework

We have built a Python and Streamlit diagnostic tool for small-business owners. This tool evaluates key operational and security areas to calculate a weighted risk score, identify the highest-priority technology gap, and generate a practical modernization roadmap.

**[Click here to view the diagnostic tool](https://business-readiness-check.onrender.com/)**

### Cybersecurity Considerations

**Information Collection Guidelines:** The tool explicitly limits data collection to business type, calculated risk scores, and the seven diagnostic answers. The collection of passwords, personally identifiable information (PII), or customer records is strictly prohibited. Furthermore, IP addresses are not intentionally stored within the application database.

**Assessment Answer Storage:** Processing is entirely in-memory and session-based, with an automatic cleanup trigger after 30 minutes of inactivity. As per our privacy notice: *"Assessment responses are used for the current assessment session and are not persisted by the application."*

**Input Validation & Error Handling:** All user inputs are validated against expected Boolean values and defined score ranges (0-14). We implement a strategy for graceful error handling, with system logs maintained for 30 days to facilitate troubleshooting without compromising session privacy.

**Secure Deployment:** The application is deployed using HTTPS/TLS encryption. To ensure a stable and secure environment, we utilize dependency version pinning and manage all application secrets exclusively through environment variables.

**Future Enhancements:** We have developed a strategy for file upload protection (including malware scanning and extension filtering) to be implemented if file-sharing features are added in later iterations.

#### NIST CSF 2.0 Alignment

The diagnostic tool aligns with the NIST Cybersecurity Framework 2.0 by helping users **Govern** their tech strategy, **Identify** technical gaps, **Protect** assets through recommended controls, **Detect** vulnerabilities in current workflows, and establish protocols to **Respond** to and **Recover** from operational disruptions.

## 6.0 Conclusion

The developed Python and Streamlit diagnostic tool directly addresses the operational inefficiencies and "Fragmentation Tax" identified in our research. By automating the auditing of legacy systems and providing a weighted risk-assessment framework, this solution enables small-scale retailers to identify critical technology and cybersecurity gaps efficiently. With a design rooted in NIST CSF 2.0 principles and a commitment to data privacy — ensuring no sensitive information persists beyond the active session — the tool offers a secure, actionable roadmap for modernization. This framework empowers independent businesses to move beyond manual processing and fragmented data, converting operational challenges into measurable growth, competitive resilience, and long-term customer loyalty.

## 7.0 Supporting Research

In parallel with the quantitative analysis, the team logged external sources validating the pain points against published research on mom-and-pop retailers.

- **[Lendio Study](https://www.lendio.com/blog/study-mom-and-pop-businesses):** Mom-and-pop businesses trail in average revenue and credit scores.
- **[Entrepreneur.com](https://www.entrepreneur.com/leadership/what-big-brands-can-learn-from-mom-and-pop-stores-to/470830):** Analyzes personalization and technology gaps in retail.
- **[Accurate Blog](https://www.accurate.com/blog/how-mom-and-pops-can-compete-with-big-retail/):** Explores competitive logistics strategies for small-scale retailers.
- **[SBE Council Survey](https://sbecouncil.org/wp-content/uploads/2026/03/SBE-Technology-Use-Survey-March-2026-Final-2.pdf):** Data on limited technology awareness among small businesses.

**Team composition:**
- Ramya Kota (Data Analytics)
- Dennys Antunish (IT Automation with Python)
- Sukanya Karri (Cybersecurity)
- Aishat Omolabake Ajibola (Advanced Data Analytics)
