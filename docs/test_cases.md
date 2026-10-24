# TEST CASES SPECIFICATION & EXECUTION REPORT

## Project: EMI Management System
**Test Suite Framework**: `pytest 8.4.2`  
**Execution Environment**: Python 3.9.6, SQLite (In-Memory Isolation) & MySQL Compatible  
**Total Automated Tests**: 26 Passed, 0 Failed, 0 Warnings  

---

## 1. Test Summary Matrix

| Module | Test Case ID | Description | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Authentication** | `TC-AUTH-01` | Register new user with valid details | User record created, password hashed with PBKDF2 SHA-256 | **PASS** |
| | `TC-AUTH-02` | Reject registration with existing email | Validation error: "already exists", HTTP 200/Flash | **PASS** |
| | `TC-AUTH-03` | Reject registration when passwords mismatch | Validation error: "passwords do not match" | **PASS** |
| | `TC-AUTH-04` | Log in with valid credentials | User authenticated, session populated with user ID & name | **PASS** |
| | `TC-AUTH-05` | Log in with invalid password or email | Authentication rejected: "invalid email or password" | **PASS** |
| | `TC-AUTH-06` | Access protected routes without login | Immediate redirect (HTTP 302) to `/login` | **PASS** |
| | `TC-AUTH-07` | Full login and logout session flow | Session cleared on logout, subsequent protected requests redirected | **PASS** |
| **EMI Engine** | `TC-EMI-01` | Calculate standard reducing-balance EMI | P=100,000, r=12%, n=12 months yields exact EMI = ₹8,884.88 | **PASS** |
| | `TC-EMI-02` | Calculate zero-interest loan EMI | P=60,000, r=0%, n=12 yields exact EMI = ₹5,000.00 | **PASS** |
| | `TC-EMI-03` | Validate negative/zero principal | Rejected with descriptive `ValueError` | **PASS** |
| | `TC-EMI-04` | Validate negative interest rate | Rejected with descriptive `ValueError` | **PASS** |
| | `TC-EMI-05` | Validate zero/negative tenure | Rejected with descriptive `ValueError` | **PASS** |
| | `TC-EMI-06` | Reconcile sum of principal components | Sum of scheduled principal equals original principal exactly | **PASS** |
| | `TC-EMI-07` | Month-end calendar date progression | Jan 31 + 1 mo = Feb 28/29, + 2 mos = Mar 31, + 3 mos = Apr 30 | **PASS** |
| | `TC-EMI-08` | Loan summary helper calculations | Total payable equals total principal + total interest | **PASS** |
| **Loan Management** | `TC-LOAN-01` | Loan creation and schedule generation | Loan saved, exact n instalments created in `emi_schedule` | **PASS** |
| | `TC-LOAN-02` | Cross-user loan isolation | User B cannot view or delete User A's loan | **PASS** |
| | `TC-LOAN-03` | Safe edit policy before payments | Full modification permitted, schedule regenerated | **PASS** |
| | `TC-LOAN-04` | Safe edit policy after payments | Financial term edits blocked to protect recorded payments | **PASS** |
| | `TC-LOAN-05` | Cascading loan deletion | Deleting loan cascades and deletes all schedules & payments | **PASS** |
| **Payment Ledger** | `TC-PAY-01` | Record full instalment settlement | Payment recorded, remaining balance = 0, status = "Paid" | **PASS** |
| | `TC-PAY-02` | Record partial instalment payment | Payment recorded, remaining updated, status = "Partially Paid" | **PASS** |
| | `TC-PAY-03` | Multiple partial payments on 1 instalment | Multiple transactions logged, cumulative amount accurate | **PASS** |
| | `TC-PAY-04` | Reject payment exceeding remaining balance | Transaction rejected: "exceeds remaining balance" | **PASS** |
| | `TC-PAY-05` | Reject zero or negative payments | Transaction rejected: "greater than zero" | **PASS** |
| | `TC-PAY-06` | Prevent cross-user payment recording | User B cannot log payment against User A's instalment | **PASS** |
| | `TC-PAY-07` | Real-time dashboard KPI updates | Dashboard figures immediately reflect new payment amounts | **PASS** |
| | `TC-PAY-08` | CSV export authorization | CSV contains only authenticated user's records | **PASS** |

---

## 2. Test Execution Command & Terminal Output

```bash
$ ./venv/bin/pytest -v
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0 -- venv/bin/python3
cachedir: .pytest_cache
rootdir: /Users/sailakal/Desktop/wt/emi_management-
configfile: pytest.ini
testpaths: tests
collected 26 items

tests/test_auth.py::test_user_registration PASSED                        [  3%]
tests/test_auth.py::test_duplicate_email_rejection PASSED                [  7%]
tests/test_auth.py::test_password_mismatch_rejection PASSED              [ 11%]
tests/test_auth.py::test_successful_login PASSED                         [ 15%]
tests/test_auth.py::test_invalid_login PASSED                            [ 19%]
tests/test_auth.py::test_protected_routes_redirect_unauthenticated PASSED [ 23%]
tests/test_auth.py::test_client_login_and_logout_flow PASSED             [ 26%]
tests/test_emi_calculator.py::test_standard_emi_calculation PASSED       [ 30%]
tests/test_emi_calculator.py::test_zero_interest_loan_calculation PASSED [ 34%]
tests/test_emi_calculator.py::test_invalid_calculator_inputs PASSED      [ 38%]
tests/test_emi_calculator.py::test_amortization_schedule_principal_reconciliation PASSED [ 42%]
tests/test_emi_calculator.py::test_month_end_date_progression PASSED     [ 46%]
tests/test_emi_calculator.py::test_calculation_summary PASSED            [ 50%]
tests/test_loans.py::test_loan_creation_and_schedule_generation PASSED   [ 53%]
tests/test_loans.py::test_loan_ownership_isolation PASSED                [ 57%]
tests/test_loans.py::test_safe_edit_policy_before_payments PASSED        [ 61%]
tests/test_loans.py::test_safe_edit_policy_after_payments PASSED         [ 65%]
tests/test_loans.py::test_loan_deletion_cascades_safely PASSED           [ 69%]
tests/test_payments.py::test_successful_full_payment PASSED              [ 73%]
tests/test_payments.py::test_partial_payment PASSED                      [ 76%]
tests/test_payments.py::test_multiple_payments_on_single_installment PASSED [ 80%]
tests/test_payments.py::test_excess_payment_rejection PASSED             [ 84%]
tests/test_payments.py::test_zero_and_negative_payment_rejection PASSED  [ 88%]
tests/test_payments.py::test_cross_user_payment_prevention PASSED        [ 92%]
tests/test_payments.py::test_dashboard_totals_after_payment PASSED       [ 96%]
tests/test_payments.py::test_csv_export_authorization PASSED             [100%]

============================== 26 passed in 6.80s ==============================
```
