# Business Readiness Check: Project Tracker and Data Sources

This document records the datasets, research materials, project tracking, and
analytical insights used to develop the **Business Readiness Check**, the team's
implementation of the assigned Small Business Tech-Stack Diagnostic Tool topic.

---

## 📋 Project Review Tracker (Week 1 – Week 4)

| Team Member | Task(s) | Status | Notes |
| :--- | :--- | :--- | :--- |
| **Ramya Kota** | • Create Project Folder on Google Drive<br>• Source for datasets | Completed | Created the folder on Google Drive. Sourced e-commerce sales, admin, and mom-and-pop store datasets on Kaggle. Completed cleaning and analyzing data through Google Sheets. |
| **Aishat Omolabake Ajibola** | • Maintain PACE document<br>• Advanced data analysis and dashboard | Completed | Maintained the PACE workflow, analyzed the global dataset, and documented the Tableau dashboard. |
| **Dennys** | • Manage GitHub repository<br>• Design and implement project framework | Completed | Managed the repository and implemented the Python and Streamlit Business Readiness Check, automated scoring and report generation, tests, deployment, core documentation, and the completed team walkthrough video. |
| **Sukanya** | • Explore security angle for project | Completed | Prepared the cybersecurity review, NIST CSF 2.0 alignment, security roadmap, and supporting visualizations. |

---

## 📂 Datasets & Research Inventory

The inventory preserves every dataset and report considered during research.
The **Completed** status records that the sourcing or review task was completed;
it does not mean every listed dataset was combined into the final analysis. The
implemented dashboard and diagnostic use the **Global E-Commerce & Supply
Chain** dataset as the selected analytical dataset. Its raw CSV tables and
cleaned `Global Dataset.xlsx` workbook are included in this repository. The
other entries remain research candidates or supporting context.

| File Name | Dataset Link | Description | Status |
| :--- | :--- | :--- | :--- |
| **ecommerce_sales_analytics_5000.csv** | [Kaggle Link](https://www.kaggle.com/datasets/abbas829/ecommerce-sales-dataset/data) | **E-Commerce Sales Analytics (5,000 Records)**<br>Contains 5,000 unique rows and 15 analytical columns tracking the end-to-end lifecycle of retail orders. Suitable for data cleaning to complex ML modeling. | Completed |
| **online_sales_dataset.csv** | [Kaggle Link](https://www.kaggle.com/datasets/yusufdelikkaya/online-sales-dataset?select=online_sales_dataset.csv) | Anonymized sales transaction data detailing product purchases, customer details, discounts, payment methods, and shipment providers. | Completed |
| **Sales Transaction v.4a.csv** | [Kaggle Link](https://www.kaggle.com/datasets/gabrielramos87/an-online-shop-business) | **UK-Based Online Retail (500K rows)**<br>One year of transaction data from a UK gift and homeware shop. Includes order numbers, stock codes, prices, quantities, customer numbers, and cancellation reasons. | Completed |
| **Global E-Commerce & Supply Chain** | [Kaggle Link](https://www.kaggle.com/datasets/parsakh/global-e-commerce-and-supply-chain-database) | Relational database (8 interconnected CSVs) covering backend retail metrics: sales ledger, customer profiles, product catalogs, price histories, warehouse inventory, supplier costs, and marketing spend. | Completed |
| **retail_customer_churn_100k.csv** | [Kaggle Link](https://www.kaggle.com/datasets/noopurbhatt/retail-intelligence-customer-churn-dataset) | **100,000 Retail Customers Dataset**<br>Simulates behavioral signals, engagement metrics, loyalty scores, cart abandonment, and ML-ready flags for predicting churn. | Completed |
| **saas_feature_matrix_2026.csv** | [Kaggle Link](https://www.kaggle.com/datasets/comparedge/saas-pricing-plans-2026) | Binary feature matrix covering 331 SaaS and AI tools across 378 normalized feature flags. Ideal for tool recommendation systems and feature clustering. | Completed |
| **smb_cyberthreats.csv** | [Kaggle Link](https://www.kaggle.com/datasets/emmanuelubong/cyber-threats-for-small-and-medium-businesses) | 1,000 records tracking 26 features related to cyber threats against SMBs across 20+ SaaS categories (financial loss, downtime, attack vectors, MFA usage). | Completed |
| **SBE Technology Use Survey (March 2026)** | [PDF Report](https://sbecouncil.org/wp-content/uploads/2026/03/SBE-Technology-Use-Survey-March-2026-Final-2.pdf) | Insights on how small businesses (2–99 employees) integrate AI, digital marketing, and automated pricing, while maintaining physical storefront operations. | Completed |
| **Luxury Cosmetics Pop-Up** | [Kaggle Link](https://www.kaggle.com/datasets/pratyushpuri/payment-card-fraud-detection-with-ml-models-2025) | 2,133 transactional records across 20 global pop-up locations specifically curated for credit card fraud detection analysis. | Completed |
| **Ecommerce_Customer_Behavior_Dataset.csv** | [Kaggle Link](https://www.kaggle.com/datasets/roshaaann30/e-commerce-customer-behavior-dataset) | Large-scale synthetic dataset containing 150,000 records simulating customer interactions, browsing sessions, CLV metrics, marketing engagement, and fraud risk. | Completed |
| **Top 500 AI Tools (2026)** | [Kaggle Link](https://www.kaggle.com/datasets/nudratabbas/top-100-ai-tools-2026) | Ranks AI tools by market impact, community ratings, pricing models, and "Agentic Capability Scores" (measuring autonomy). | Completed |
| **shopify_sales_dataset_ml_eda.csv** | [Kaggle Link](https://www.kaggle.com/datasets/aliiihussain/shopify-sales-dataset-for-ml-and-eda) | Structured transaction dataset capturing traffic acquisition channels, payment types, product categories, and global geographic distributions. | Completed |
| **Global E-Commerce Dataset (1M Records)** | [Kaggle Link](https://www.kaggle.com/datasets/akrambelha/global-e-commerce-dataset-1m-records-20242026) | 1,000,000+ synthetic transaction records covering 62 columns from Feb 2024 to Feb 2026. Perfect for large-scale EDA and dashboarding. | Completed |
| **Mom and Pop Store Global Market Report** | [Report Link](https://www.thebusinessresearchcompany.com/report/mom-and-pop-store-global-market-report) | Market survey analyzing global mom-and-pop storefront trends. | Completed |
| **UN Global MSMEs Report 2024** | [PDF Report](https://www.un.org/sites/un2.un.org/files/globalmsmesreport2024.pdf) | UN report on micro, small, and medium-sized enterprises (MSMEs). | Completed |

---

## 📑 Articles & Industry Resources

* [What Big Brands Can Learn From Mom & Pop Shops](https://www.entrepreneur.com/leadership/what-big-brands-can-learn-from-mom-and-pop-stores-to/470830) (*Entrepreneur*)
* [How Mom-and-Pops Can Compete with Big Retail](https://www.accurate.com/blog/how-mom-and-pops-can-compete-with-big-retail/) (*Accurate*)
* [Upgrades Can Help Mom & Pop Stores Compete](https://www.gsb.stanford.edu/insights/upgrades-can-help-mom-pop-stores-compete-big-retail) (*Stanford Graduate School of Business*)
* [Small Business Technology Use Survey](https://sbecouncil.org/wp-content/uploads/2026/03/SBE-Technology-Use-Survey-March-2026-Final-2.pdf) (*SBE Council*)

---

## 🎯 Problem Statement & Core Insights

### Problem
Traditional mom-and-pop retail storefronts lack a simple, automated path to audit and modernize their legacy administrative software.

### Goal
Build the **Business Readiness Check** by using transactional data and industry
research to identify operational pain points and provide practical
modernization guidance.

---

### Potential Pain Points Considered

The items below are research-informed conditions the team considered while
defining the diagnostic. They are not claims that every mom-and-pop business
experiences the same conditions or outcomes.

#### 1. Financial & Funding Challenges
* **Lower Revenue & Credit Scores:** Mom-and-pop operators may face lower monthly revenue and credit scores, restricting access to affordable growth loans ([Lendio Study](https://www.lendio.com/blog/study-mom-and-pop-businesses)).
* **Tight Profit Margins:** Daily operational costs, taxes, and software fees can reduce already-limited margins.

#### 2. Logistics & Operational Pressures
* **Shipping Disadvantages:** Difficulty absorbing shipping fees or offering fast delivery can make it harder to compete with major online retailers.
* **Fulfillment Errors:** Manual entry and fragmented tracking across legacy spreadsheets can contribute to inaccurate inventory records.

#### 3. Marketing & Technology Gaps
* **The Personalization Gap:** Limited budgets can restrict access to advanced merchandising or targeted-advertising tools.
* **Platform Risks:** Payment-configuration errors or account interruptions can disrupt store operations.

---

### The "Fragmentation Tax"

The team used the term "fragmentation tax" for potential costs and manual work
created when business tools do not exchange information reliably:

1. **The Manual Reconciling Trap (Inventory & Sales Gaps):**
   Manually updating spreadsheets to match storefront and online inventory can contribute to **phantom stockouts** or overselling.
2. **Hidden Transaction Friction (Payment Gaps):**
   Missing guest checkout or modern digital-wallet options can add customer friction.
3. **Ghost Customers (Email & Tracking Gaps):**
   Disconnected register and marketing systems can limit automated retention, win-back, or abandoned-cart workflows.
4. **Service Calendaring Silos (Booking Gaps):**
   Phone-only scheduling can prevent customers from booking outside business hours.
