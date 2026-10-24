# VIVA VOCE QUESTIONS & CONCISE ANSWERS GUIDE

## Subject: Web Technology (TE Computer Engineering)
**Project Title**: EMI Management System  
**Core Technologies**: Python, Flask, MySQL, SQLAlchemy, Jinja2, Bootstrap 5, JavaScript, Chart.js  

---

### 1. Flask & Web Fundamentals

#### Q1. What is Flask and why is it categorized as a microframework?
**Answer**: Flask is a lightweight Python web framework built upon the Werkzeug WSGI toolkit and Jinja2 template engine. It is termed a "microframework" because it does not enforce particular database engines or form libraries out of the box; instead, it provides core routing, request handling, and extensibility, letting developers pick modular components (e.g., SQLAlchemy, Flask-WTF).

#### Q2. How do HTTP GET and POST methods differ in web applications?
**Answer**:
- **GET**: Requests data from a server. Parameters are visible in the URL query string, cached by browsers, bookmarked, and should be idempotent (causing no side effects on the server).
- **POST**: Submits data to the server within the HTTP request body. It is typically used for state-changing operations (creating loans, registering users, logging payments) and is not cached by default.

#### Q3. What are Flask Blueprints and why did you use them in this project?
**Answer**: Blueprints allow partitioning a Flask application into modular, decoupled component groups (e.g., `auth_bp`, `loan_bp`, `payment_bp`, `report_bp`). Each blueprint manages its own routes and views, enhancing maintainability, collaboration, and project organization over a single monolithic file.

---

### 2. Frontend, Templates & UI/UX

#### Q4. What is Jinja2 and how does template inheritance work?
**Answer**: Jinja2 is Python's templating engine for generating dynamic HTML. Template inheritance uses a master base template (`base.html`) containing common scaffolding (navbar, sidebar, stylesheets, scripts) with named `{% block content %}` placeholders that child templates (`dashboard.html`, `loans.html`) extend and override.

#### Q5. How does Bootstrap 5 achieve responsiveness across varying screen sizes?
**Answer**: Bootstrap 5 employs a 12-column mobile-first flexbox grid system using CSS media query breakpoints:
- `xs` (<576px), `sm` (≥576px), `md` (≥768px), `lg` (≥992px), `xl` (≥1200px), `xxl` (≥1400px).  
Classes like `col-12 col-md-6 col-lg-4` adapt columns dynamically to screen widths.

#### Q6. What is the role of JavaScript and Chart.js in your system?
**Answer**: JavaScript powers client-side interactions including live EMI preview calculations without page reloads, mobile sidebar toggles, and form submission debouncing. Chart.js visualizes dynamic financial data (Paid vs Pending instalments doughnut chart, loan balance distribution bar chart, and repayment trends).

---

### 3. Database & SQL Architecture

#### Q7. What are Primary Keys and Foreign Keys, and how are they used in your schema?
**Answer**:
- **Primary Key (PK)**: A unique identifier for every row in a table (e.g., `user_id` in `users`, `loan_id` in `loans`). It cannot contain NULL values.
- **Foreign Key (FK)**: A column or set of columns in one table referencing the Primary Key of another (e.g., `loans.user_id` references `users.user_id`). It enforces referential integrity between tables.

#### Q8. Why did you use `DECIMAL(12, 2)` instead of `FLOAT` or `DOUBLE` for financial amounts?
**Answer**: `FLOAT` and `DOUBLE` use binary floating-point representation (IEEE 754), which causes precision loss and rounding inaccuracies during arithmetic (e.g., `0.1 + 0.2 = 0.30000000000000004`). `DECIMAL` stores exact fixed-point numerical values, ensuring strict mathematical accuracy for monetary transactions.

#### Q9. What is `ON DELETE CASCADE` and why is it critical in your loan schema?
**Answer**: `ON DELETE CASCADE` ensures that when a parent entity is deleted (e.g., deleting a loan), the database engine automatically removes all associated child records (`emi_schedule` and `payments`). This prevents orphaned rows and keeps the database clean and consistent.

---

### 4. SQLAlchemy ORM

#### Q10. What is an Object-Relational Mapper (ORM) and what advantages does SQLAlchemy provide?
**Answer**: An ORM maps relational database tables to Python classes and rows to class instances. Key benefits:
1. Eliminates repetitive raw SQL queries.
2. Automates parameterization, preventing SQL Injection vulnerabilities.
3. Provides database independence and migrations.
4. Manages database transactions, session lifecycle, and identity maps.

#### Q11. How do you manage database transactions in SQLAlchemy?
**Answer**: Transactions are managed via the SQLAlchemy `db.session`:
- `db.session.add(obj)`: Stages an object.
- `db.session.flush()`: Executes pending SQL to generate autoincrement IDs without committing the transaction.
- `db.session.commit()`: Atomically commits all changes to disk.
- `db.session.rollback()`: Reverts all uncommitted changes if an exception occurs, preserving ACID atomicity.

---

### 5. Authentication, Security & Sessions

#### Q12. How does session management work in Flask?
**Answer**: Flask uses cryptographically signed client-side session cookies. The session data is encoded and signed using the application's `SECRET_KEY`. When the client sends the cookie in subsequent requests, Flask verifies the cryptographic signature to ensure the data was not tampered with.

#### Q13. Why should passwords never be stored in plain text, and how does your app hash them?
**Answer**: Storing plaintext passwords exposes user credentials in the event of a database breach. This system uses Werkzeug's implementation of **PBKDF2 SHA-256** (Password-Based Key Derivation Function 2) with a unique cryptographic salt. It is computationally intensive, resisting rainbow table and brute-force dictionary attacks.

#### Q14. What is Cross-Site Request Forgery (CSRF) and how is it prevented?
**Answer**: CSRF occurs when a malicious website tricks a user's browser into executing an unauthorized state-changing request on a site where they are authenticated. We prevent CSRF by generating a cryptographically secure token stored in the user's session. Every POST form includes this token in a hidden field, which the server verifies before processing the request.

#### Q15. How do you prevent Insecure Direct Object References (IDOR) / cross-user data access?
**Answer**: We never rely solely on client-supplied IDs. Every query for a loan, instalment, or payment joins through the complete relationship chain to verify that the owning `user_id` matches the authenticated `session['user_id']`:
```python
Loan.query.filter_by(loan_id=loan_id, user_id=current_user.user_id).first()
```

---

### 6. Mathematical Financial Modeling

#### Q16. What is the reducing-balance EMI formula and what do its variables represent?
**Answer**:
$$EMI = P \times r \times \frac{(1 + r)^n}{(1 + r)^n - 1}$$
- $P$ = Principal loan amount.
- $r$ = Monthly interest rate in decimal form: $(\text{Annual Rate} / 100) / 12$.
- $n$ = Total tenure in months.  
For a zero-interest loan ($r = 0$), $EMI = P / n$.

#### Q17. How does the system handle penny differences and schedule reconciliation on the final month?
**Answer**: In reducing-balance amortization, dividing fractions of a cent over 12–360 months can leave a discrepancy of a few cents/paise. Our amortization engine computes $n-1$ standard payments and explicitly sets the final month's principal component to the remaining outstanding principal balance:
$$\text{Principal Component}_n = \text{Remaining Balance}_{n-1}$$
This guarantees that the sum of all scheduled principal components equals the original principal amount exactly.

#### Q18. What is the "Safe Edit Policy" implemented in your loan module?
**Answer**: If no payments have been made on a loan, the user may edit all parameters, and the system recalculates the EMI and regenerates the schedule. However, once even a single payment has been recorded, modifying financial terms ($P, r, n$) would invalidate existing payment records. Thus, the system blocks financial alterations and only allows metadata changes (loan name, lender name).
