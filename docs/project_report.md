# ACADEMIC MINI PROJECT REPORT

## EMI MANAGEMENT SYSTEM
**Third Year Computer Engineering (Semester VI)**  
**Course**: Web Technology Mini Project  

---

### CERTIFICATE OF COMPLETION

This is to certify that the project entitled **"EMI MANAGEMENT SYSTEM"** is a bonafide work carried out by the student in partial fulfillment of the requirements for the Third Year Computer Engineering curriculum of Mumbai University / Autonomous Institute during the academic year.

**Evaluator / Internal Guide**: _______________________  
**Head of Department**: _______________________  
**Date**: _______________________  

---

## TABLE OF CONTENTS
1. [Abstract](#1-abstract)
2. [Introduction & Background](#2-introduction--background)
3. [Problem Formulation & Objectives](#3-problem-formulation--objectives)
4. [Literature Survey & Existing Systems](#4-literature-survey--existing-systems)
5. [Requirement Analysis & System Specifications](#5-requirement-analysis--system-specifications)
6. [Design & Methodology](#6-design--methodology)
   - 6.1 Architecture & Flowcharts
   - 6.2 Relational Database Schema & ER Diagram
   - 6.3 Mathematical Modeling of Reducing Balance EMI
7. [Implementation Details](#7-implementation-details)
   - 7.1 Backend Services & Flask Blueprints
   - 7.2 Frontend User Experience & Chart.js Integration
   - 7.3 Security Measures (Auth, CSRF, IDOR Prevention)
8. [Results & Screen Captures](#8-results--screen-captures)
9. [Conclusion & Future Work](#9-conclusion--future-work)
10. [References](#10-references)

---

## 1. Abstract
The **EMI Management System** is a full-stack financial management web portal developed to simplify debt servicing and amortization tracking for modern borrowers. Combining Python Flask on the backend with a structured MySQL relational database, SQLAlchemy ORM, and Bootstrap 5 on the frontend, the system allows registered users to log loans, calculate mathematically verified reducing-balance EMIs, generate month-end compliant schedules, track partial/full settlements across varied payment modes, and analyze liabilities using interactive Chart.js visualizations.

---

## 2. Introduction & Background
With increasing consumer loans (education, mortgages, automobile, and consumer durables), individuals often balance multiple loan agreements across multiple banks and NBFCs simultaneously. Each creditor features distinctive interest rates, tenures, and monthly repayment dates. Missing an EMI payment induces penalty charges and downgrades the borrower’s credit score. 

The Web Technology mini project requires understanding client-side programming, server-side processing, database management, and asynchronous data transfer. This project bridges these academic concepts by implementing an enterprise-grade banking interface adhering to strict MVC/MSRT architectural principles.

---

## 3. Problem Formulation & Objectives
### 3.1 Problem Statement
Most web-based loan calculators are static, browser-only widgets that calculate an estimated figure without storing loan records or tracking payments over time. Conversely, comprehensive banking apps require direct linking of bank credentials, raising security and privacy concerns. There is an absence of a secure, lightweight, self-managed web ledger that manages end-to-end loan amortization, tracks repayments, reconciles pennies on final installments, and prevents silent schedule corruption.

### 3.2 Objectives
1. **User Authentication & Privacy**: Secure user management using PBKDF2 SHA-256 password hashing and session isolation.
2. **Authoritative Amortization Engine**: Server-side reducing balance EMI calculations ensuring exact balance zeroing on final tenure.
3. **Multi-Transaction Ledger**: Support multiple partial and full payment transactions per instalment while preventing overpayment.
4. **Interactive Dashboard**: Consolidated financial KPIs, loan progress bars, and Chart.js analytics.
5. **Data Export**: Sanitized CSV ledger export restricted to authenticated user records.

---

## 4. Literature Survey & Existing Systems
| System | Advantages | Limitations |
| :--- | :--- | :--- |
| **Traditional Spreadsheets (Excel / Google Sheets)** | Flexible formulas | Prone to accidental cell corruption, lacks multi-device authentication, no automated overdue notifications. |
| **Online Banking Portals** | Official payment processing | Restricted only to loans issued by that specific institution; no multi-bank consolidation. |
| **Generic Online Calculators** | Fast computation | Ephemeral session; cannot record payments, progress, or overdue statuses. |
| **Proposed EMI Management System** | Consolidated multi-bank tracking, exact reducing balance math, safe edit policies, strict user isolation, CSV exports. | Simulated payments (does not initiate live money transfers). |

---

## 5. Requirement Analysis & System Specifications
### 5.1 Software Requirements
- **Web Server / Backend Framework**: Python 3.9+ with Flask 3.1.3
- **Database**: MySQL Server 8.0 / 5.7 (InnoDB engine, utf8mb4 encoding)
- **Database Driver & ORM**: PyMySQL 1.2, SQLAlchemy 2.0, Flask-SQLAlchemy 3.1
- **Frontend Core**: HTML5, CSS3, JavaScript (ES6)
- **CSS Framework**: Bootstrap 5.3.3 & Bootstrap Icons
- **Data Visualization**: Chart.js 4.4.1
- **Testing Engine**: pytest 8.4.2

### 5.2 Functional Requirements
- **FR1 (Auth)**: Register account with email uniqueness validation, log in with password verification, and securely log out.
- **FR2 (Loan CRUD)**: Add loan, list user loans, view loan schedule, update loan (subject to safe edit policy), and delete loan with cascading cleanup.
- **FR3 (EMI Engine)**: Calculate monthly reducing-balance installments and reconcile pennies.
- **FR4 (Payment Tracking)**: Log full or partial payments, validate payment bounds, and update statuses dynamically.
- **FR5 (Analytics & Reporting)**: Real-time dashboard KPI summaries, overdue highlights, distribution charts, and CSV report export.

---

## 6. Design & Methodology

### 6.1 Architectural Workflow
The application follows a modular Model-Service-Route-Template architecture:
1. **Routes (Controllers)**: Receive HTTP requests, validate session and CSRF tokens, and invoke business services.
2. **Services (Business Logic)**: Contain financial formulas, database transaction boundaries, validation rules, and data aggregation.
3. **Models (Entities)**: Define SQLAlchemy relational schemas, cascade rules, and computed properties.
4. **Templates (Presentation)**: Render clean, accessible Jinja2 templates styled with Bootstrap 5 and animated with Chart.js.

### 6.2 Relational Database Schema & ER Model
The database consists of 4 normalized relational tables in 3NF:
- `users`: User identity and password credentials.
- `loans`: Loan parameters (principal, rate, tenure, start date, status) linked to user via foreign key.
- `emi_schedule`: Individual monthly payment schedules linked to loans with unique constraint `(loan_id, installment_number)`.
- `payments`: Individual recorded payment transactions referencing `emi_schedule`.

```
[ users ] (1) <---------> (N) [ loans ] (1) <---------> (N) [ emi_schedule ] (1) <---------> (N) [ payments ]
```

### 6.3 Mathematical Model of Reducing Balance EMI
The reducing-balance formula utilized:

$$EMI = P \times r \times \frac{(1 + r)^n}{(1 + r)^n - 1}$$

- $P$: Principal loan amount.
- $r = \frac{\text{Annual Interest Rate}}{12 \times 100}$: Monthly interest rate in decimal.
- $n$: Tenure in months.

**Zero-Interest Special Case**: When annual interest rate is 0%:
$$EMI = \frac{P}{n}$$

**Month-End Date Progression**:
When loans commence on month-end dates (e.g. 31st January), standard 30-day offsets produce erroneous dates. The system utilizes `calendar.monthrange` to snap dates to destination month limits (Jan 31 $\rightarrow$ Feb 28/29 $\rightarrow$ Mar 31 $\rightarrow$ Apr 30).

---

## 7. Implementation Details

### 7.1 Safe Edit Policy
To prevent ledger corruption after repayments have been logged:
- If a loan has no payments recorded: Full update permitted; the previous schedule is safely deleted and a new schedule is created.
- If payments exist: Financial parameters ($P, r, n$, start date) are locked to maintain historical integrity. Only the loan name and lender name can be edited.

### 7.2 Multi-Tenant Security & IDOR Mitigation
Every database query explicitly enforces user ownership:
```python
# Verifies complete relationship chain: EMI -> Loan -> User
installment = EMISchedule.query.join(Loan).filter(
    EMISchedule.emi_id == emi_id,
    Loan.user_id == current_user.user_id
).first()
```
If a malicious user tampers with the URL parameters (`/loans/999` or `/payments/record/888`), the system returns a 404 or access denied error without revealing another user's data.

---

## 8. Testing & Validation
The system was validated using an automated test suite executed with `pytest`:
- **Total Test Cases**: 26 automated tests
- **Passing Rate**: 100% (26 passed, 0 failed, 0 warnings)
- **Key Modules Tested**:
  1. `test_auth.py`: Registration, duplicate emails, password mismatches, authentication, and route guards.
  2. `test_emi_calculator.py`: Standard calculation, zero interest, negative input rejection, penny reconciliation, and month-end dates.
  3. `test_loans.py`: Loan CRUD, schedule generation, safe edit policy before and after payments, cascading deletions, cross-user isolation.
  4. `test_payments.py`: Full settlement, partial payment, multiple payments, excess payment rejection, zero/negative rejection, cross-user payment blocking, dashboard totals, and CSV export authorization.

---

## 9. Conclusion & Future Enhancements
The **EMI Management System** provides an accurate, dependable, and user-friendly solution for individual debt management. The project successfully fulfills all curriculum requirements for Third Year Web Technology, demonstrating expertise in full-stack architecture, relational database engineering, financial algorithms, asynchronous user interfaces, and automated quality assurance.

Future enhancements include automated email alerts before due dates, multi-currency support, and refinancing simulations.

---

## 10. References
1. Grinberg, Miguel. *Flask Web Development: Developing Web Applications with Python*. O'Reilly Media.
2. Duckett, Jon. *HTML and CSS: Design and Build Websites*. John Wiley & Sons.
3. W3Schools Online Web Tutorials: Bootstrap 5, JavaScript, SQL.
4. Chart.js Documentation: https://www.chartjs.org/
5. SQLAlchemy 2.0 Unified Tutorial: https://docs.sqlalchemy.org/
