Baki Cybersecurity Strategy


1. Purpose


This document defines the cybersecurity strategy for the Baki surplus-food redistribution platform developed by the Catalyst Alliance team.


The objective is to protect the confidentiality, integrity and availability of the application's data, users and services while ensuring that security is incorporated into the application throughout the development lifecycle.


2. Security Objectives


The cybersecurity implementation will focus on:




Protecting vendor, NGO and community-user information.


Preventing unauthorised access to application functionality and data.


Protecting the application against malicious or invalid input.


Preventing abuse of public application endpoints.


Protecting personal information from unnecessary public exposure.


Maintaining the integrity of food listings and matching information.


Securing application dependencies and deployment infrastructure.


Detecting suspicious activity through logging and monitoring.


Testing the application for security vulnerabilities.


Establishing an incident-response process.




3. Security Principles


Baki will follow these security principles:


Least Privilege


Users and application components should only receive the permissions required to perform their functions.


Defence in Depth


Security should not depend on a single control. Multiple layers of protection should be implemented across the frontend, backend, API, database and deployment environment.


Secure by Design


Security requirements should be considered during development rather than added only after the application has been completed.


Data Minimisation


Only information required for the application's legitimate functions should be collected and exposed.


Never Trust User Input


All information received from users or external requests must be treated as untrusted and validated on the server.


Fail Securely


Unexpected errors should not expose sensitive information or place the application into an insecure state.


4. Key Security Controls


The following controls will be implemented and tested:




Server-side input validation.


Cross-Site Scripting (XSS) protection.


Cross-Site Request Forgery (CSRF) protection.


Rate limiting.


Authentication.


Role-Based Access Control (RBAC).


Secure handling of personal information.


Security HTTP headers.


Secure production configuration.


Secure database storage.


Secrets management.


Security logging and monitoring.


Dependency vulnerability scanning.


Static Application Security Testing (SAST).


Dynamic Application Security Testing (DAST).


Container security scanning.


Incident response.




5. Security Standards


The project will use the OWASP Top 10 as a primary reference for identifying and addressing common web-application security risks.


The project will also use the OWASP Application Security Verification Standard (ASVS) as a reference for defining appropriate application-security controls.


6. Security Development Process


Security activities will follow this lifecycle:


Identify Assets
      ↓
Identify Threats
      ↓
Assess Risk
      ↓
Implement Security Controls
      ↓
Security Testing
      ↓
Remediation
      ↓
Retesting
      ↓
Continuous Monitoring



7. Security Priorities


The initial implementation will prioritise:


Critical / High Priority




Disable Flask debug mode.


Implement server-side input validation.


Implement rate limiting.


Implement CSRF protection.


Reduce unnecessary exposure of vendor contact information.


Secure production deployment.


Implement authentication and authorisation.




Medium Priority




Security headers.


Secure database storage.


Security logging.


Dependency scanning.


Container hardening.




Continuous Security




Vulnerability scanning.


Dependency updates.


Security testing.


Monitoring.


Incident response.


Periodic security reviews.




8. Security Responsibility


The Cybersecurity function is responsible for:




Identifying application security risks.


Maintaining the security risk register.


Recommending security controls.


Supporting secure implementation.


Performing security testing.


Documenting vulnerabilities and remediation.


Reviewing security configuration.


Supporting incident-response planning.




Development team members remain responsible for implementing and maintaining security controls within the components they develop.


9. Security Definition of Done


A security-related feature will be considered complete when:




The security requirement has been implemented.


The implementation has been reviewed.


Appropriate security testing has been performed.


Identified vulnerabilities have been addressed.


The result has been documented.


The change does not introduce a known critical or high-severity vulnerability.




10. Current Security Status


The Baki application is currently an MVP/prototype.


Security hardening is therefore being performed before the application is considered ready for a production environment.


The security branch for this work is:


cybersecurity-hardening

