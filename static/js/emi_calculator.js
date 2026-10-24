/**
 * EMI Calculator - Client-side live calculation & AJAX preview
 * Formula: EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
 */

function formatCurrencyINR(amount) {
    const val = Number(amount) || 0;
    return "₹" + val.toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function calculateLiveEMI() {
    const principalInput = document.getElementById("calc_principal");
    const rateInput = document.getElementById("calc_rate");
    const tenureInput = document.getElementById("calc_tenure");
    const tenureUnit = document.getElementById("calc_tenure_unit");

    if (!principalInput || !rateInput || !tenureInput) return;

    const P = parseFloat(principalInput.value);
    const annualRate = parseFloat(rateInput.value);
    let tenure = parseInt(tenureInput.value, 10);

    if (isNaN(P) || P <= 0 || isNaN(annualRate) || annualRate < 0 || isNaN(tenure) || tenure <= 0) {
        return; // Wait for valid input
    }

    if (tenureUnit && tenureUnit.value === "years") {
        tenure = tenure * 12;
    }

    let monthlyEMI = 0;
    let totalPayable = 0;
    let totalInterest = 0;

    if (annualRate === 0) {
        monthlyEMI = P / tenure;
        totalPayable = P;
        totalInterest = 0;
    } else {
        const r = (annualRate / 100) / 12;
        const powFactor = Math.pow(1 + r, tenure);
        monthlyEMI = (P * r * powFactor) / (powFactor - 1);
        totalPayable = monthlyEMI * tenure;
        totalInterest = totalPayable - P;
    }

    // Update display fields if present
    const emiDisplay = document.getElementById("display_emi");
    const principalDisplay = document.getElementById("display_principal");
    const interestDisplay = document.getElementById("display_interest");
    const totalDisplay = document.getElementById("display_total");
    const applyLoanBtn = document.getElementById("btnApplyLoan");

    if (emiDisplay) emiDisplay.textContent = formatCurrencyINR(monthlyEMI);
    if (principalDisplay) principalDisplay.textContent = formatCurrencyINR(P);
    if (interestDisplay) interestDisplay.textContent = formatCurrencyINR(totalInterest);
    if (totalDisplay) totalDisplay.textContent = formatCurrencyINR(totalPayable);

    if (applyLoanBtn) {
        applyLoanBtn.href = `/loans/add?principal=${encodeURIComponent(P)}&rate=${encodeURIComponent(annualRate)}&tenure=${encodeURIComponent(tenure)}`;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const calcForm = document.getElementById("emiCalculatorForm");
    if (calcForm) {
        const inputs = calcForm.querySelectorAll("input, select");
        inputs.forEach(input => {
            input.addEventListener("input", calculateLiveEMI);
            input.addEventListener("change", calculateLiveEMI);
        });
        calculateLiveEMI();
    }
});
