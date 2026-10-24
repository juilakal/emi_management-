/**
 * Dashboard & Reports Charts initialization using Chart.js
 */

function initDashboardCharts(data) {
    if (!data) return;

    // 1. Paid vs Pending vs Overdue Doughnut Chart
    const statusCtx = document.getElementById("installmentStatusChart");
    if (statusCtx) {
        new Chart(statusCtx, {
            type: "doughnut",
            data: {
                labels: ["Paid", "Pending", "Overdue"],
                datasets: [{
                    data: [data.paid_count || 0, (data.pending_count - (data.overdue_count || 0)) || 0, data.overdue_count || 0],
                    backgroundColor: ["#10b981", "#f59e0b", "#ef4444"],
                    borderWidth: 2,
                    borderColor: "#ffffff"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { boxWidth: 12, padding: 15, font: { size: 12 } }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) {
                                return ` ${ctx.label}: ${ctx.raw} instalments`;
                            }
                        }
                    }
                },
                cutout: "68%"
            }
        });
    }

    // 2. Loan Distribution Bar Chart
    const distCtx = document.getElementById("loanDistributionChart");
    if (distCtx && data.loan_names && data.loan_names.length > 0) {
        new Chart(distCtx, {
            type: "bar",
            data: {
                labels: data.loan_names,
                datasets: [{
                    label: "Outstanding Principal (₹)",
                    data: data.loan_balances,
                    backgroundColor: "#3b82f6",
                    borderRadius: 6,
                    maxBarThickness: 45
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) {
                                return ` Outstanding: ₹${Number(ctx.raw).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return "₹" + Number(value).toLocaleString("en-IN");
                            }
                        },
                        grid: { color: "#f1f5f9" }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }
}

function initReportsChart(labels, values) {
    const reportCtx = document.getElementById("monthlyTrendChart");
    if (reportCtx && labels && labels.length > 0) {
        new Chart(reportCtx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [{
                    label: "Repayment Amount (₹)",
                    data: values,
                    backgroundColor: "rgba(16, 185, 129, 0.15)",
                    borderColor: "#10b981",
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.3,
                    pointBackgroundColor: "#10b981",
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) {
                                return ` Paid: ₹${Number(ctx.raw).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return "₹" + Number(value).toLocaleString("en-IN");
                            }
                        },
                        grid: { color: "#f1f5f9" }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }
}
