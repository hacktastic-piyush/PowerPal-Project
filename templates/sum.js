// Basic dataset for simulation
const baseData = {
    monthlyConsumption: 300, // kWh
    monthlyBill: 3000, // ₹
    ratePerUnit: 10, // ₹/kWh
    co2PerKwh: 0.82 // kg CO2/kWh
};

document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts
    initializeCharts();
    
    // Tab switching
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Deactivate all tabs
            tabButtons.forEach(btn => {
                btn.classList.remove('border-green-500', 'text-green-600');
                btn.classList.add('border-transparent', 'text-gray-500');
            });
            
            // Hide all content
            tabContents.forEach(content => {
                content.classList.add('hidden');
            });
            
            // Activate clicked tab
            this.classList.remove('border-transparent', 'text-gray-500');
            this.classList.add('border-green-500', 'text-green-600');
            
            // Show corresponding content
            const contentId = 'content-' + this.id.split('-')[1];
            document.getElementById(contentId).classList.remove('hidden');
            
            // Refresh charts on tab change
            window.setTimeout(() => {
                updateAllCharts();
            }, 100);
        });
    });
    
    // Initialize first tab as active
    document.getElementById('tab-overview').click();
    
    // --- HABITS TAB ---
    // Setup slider event listeners with visible value updates
    setupSliderWithValue('peak-percentage', 'peak-value', '%', updateHabitsSavings);
    setupSliderWithValue('ac-temp', 'ac-temp-value', '°C', updateHabitsSavings);
    setupSliderWithValue('fridge-temp', 'fridge-temp-value', '°C', updateHabitsSavings);
    setupSliderWithValue('habits-duration', 'habits-duration-value', ' months', updateHabitsSavings);
    
    // Checkbox event listeners for habits
    document.querySelectorAll('#content-habits input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', updateHabitsSavings);
    });
    
    // --- APPLIANCES TAB ---
    // Appliance checkbox listeners
    document.querySelectorAll('#content-appliances input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', updateApplianceSavings);
    });
    
    // --- SOLAR TAB ---
    // Solar panel slider listeners
    setupSliderWithValue('solar-size', 'solar-size-value', ' kW', updateSolarSavings);
    setupSliderWithValue('solar-duration', 'solar-duration-value', ' years', updateSolarSavings);
    
    // Initialize calculations
    updateHabitsSavings();
    updateApplianceSavings();
    updateSolarSavings();
    updateCombinedSavings();
    
    // Button click handlers
    document.getElementById('solar-report').addEventListener('click', function() {
        alert('Generating solar proposal with current settings...');
    });
    
    document.getElementById('habits-calendar').addEventListener('click', function() {
        alert('Generating energy usage calendar with recommended habits...');
    });
});

// Helper function to set up sliders with visible value updates
function setupSliderWithValue(sliderId, valueId, unit, updateCallback) {
    const slider = document.getElementById(sliderId);
    const valueDisplay = document.getElementById(valueId);
    
    if (slider && valueDisplay) {
        // Initial value
        valueDisplay.textContent = slider.value + unit;
        
        // Value update on slide
        slider.addEventListener('input', function() {
            valueDisplay.textContent = this.value + unit;
            
            // Add visual feedback
            valueDisplay.classList.add('value-change');
            setTimeout(() => valueDisplay.classList.remove('value-change'), 300);
            
            // Update calculations
            if (updateCallback) updateCallback();
        });
    }
}

// --- HABITS CALCULATIONS ---
function updateHabitsSavings() {
    const peakPercentage = parseInt(document.getElementById('peak-percentage').value);
    const acTemp = parseInt(document.getElementById('ac-temp').value);
    const fridgeTemp = parseInt(document.getElementById('fridge-temp').value);
    const duration = parseInt(document.getElementById('habits-duration').value);
    
    // Calculate savings based on slider values and checkboxes
    // Off-peak usage savings
    const peakBaseSavings = Math.round(baseData.monthlyBill * 0.3 * (1 - (peakPercentage / 100)));
    let offpeakSavings = peakBaseSavings;
    
    if (document.getElementById('offpeak-washing').checked) offpeakSavings += 180;
    if (document.getElementById('offpeak-dishwasher').checked) offpeakSavings += 120;
    if (document.getElementById('offpeak-water').checked) offpeakSavings += 80;
    
    // Temperature savings calculation
    // Each degree change in AC saves ~6%
    const acBaseSavings = (acTemp - 22) * 0.06 * baseData.monthlyBill * 0.4;
    const acSavings = Math.round(Math.max(0, acBaseSavings));
    
    // Refrigerator temperature (optimal is 3-4°C)
    const fridgeSavings = Math.round(Math.abs(fridgeTemp - 4) * 30);
    const tempSavings = acSavings + fridgeSavings;
    
    // Standby savings
    let standbySavings = 0;
    if (document.getElementById('smart-strips').checked) standbySavings += 80;
    if (document.getElementById('unplug-chargers').checked) standbySavings += 30;
    if (document.getElementById('switch-off').checked) standbySavings += 40;
    
    // Seasonal savings
    let seasonalSavings = 0;
    if (document.getElementById('natural-cooling').checked) seasonalSavings += 120;
    if (document.getElementById('ceiling-fans').checked) seasonalSavings += 80;
    if (document.getElementById('daylight').checked) seasonalSavings += 50;
    
    // Total monthly savings
    const monthlySavings = offpeakSavings + tempSavings + standbySavings + seasonalSavings;
    const totalSavings = monthlySavings * duration;
    
    // Energy reduction percentage
    const energyReduction = Math.round(monthlySavings / baseData.monthlyBill * 100);
    
    // CO2 reduction
    const kwhSaved = monthlySavings / baseData.ratePerUnit;
    const co2Reduction = Math.round(kwhSaved * baseData.co2PerKwh);
    
    // Update UI
    document.getElementById('offpeak-savings').textContent = '₹' + offpeakSavings + '/month';
    document.getElementById('temp-savings').textContent = '₹' + tempSavings + '/month';
    document.getElementById('standby-savings').textContent = '₹' + standbySavings + '/month';
    document.getElementById('seasonal-savings').textContent = '₹' + seasonalSavings + '/month';
    
    document.getElementById('habits-monthly-savings').textContent = '₹' + monthlySavings;
    document.getElementById('habits-total-savings').textContent = '₹' + totalSavings;
    document.getElementById('habits-energy-reduction').textContent = energyReduction + '%';
    document.getElementById('habits-co2-reduction').textContent = co2Reduction + ' kg';
    
    // Update the habits chart
    updateHabitsChart(offpeakSavings, tempSavings, standbySavings, seasonalSavings);
    
    // Also update combined savings when habits change
    updateCombinedSavings();
}

// --- APPLIANCE CALCULATIONS ---
function updateApplianceSavings() {
    let totalInvestment = 0;
    let totalSavings = 0;
    let totalCO2Reduction = 0;
    
    // Calculate based on selected appliances
    if (document.getElementById('upgrade-ac').checked) {
        totalInvestment += 45000;
        totalSavings += 450;
        totalCO2Reduction += 45 * baseData.co2PerKwh;
    }
    
    if (document.getElementById('upgrade-refrigerator').checked) {
        totalInvestment += 28000;
        totalSavings += 380;
        totalCO2Reduction += 38 * baseData.co2PerKwh;
    }
    
    if (document.getElementById('upgrade-washing').checked) {
        totalInvestment += 16000;
        totalSavings += 220;
        totalCO2Reduction += 22 * baseData.co2PerKwh;
    }
    
    if (document.getElementById('upgrade-lights').checked) {
        totalInvestment += 3500;
        totalSavings += 150;
        totalCO2Reduction += 15 * baseData.co2PerKwh;
    }
    
    if (document.getElementById('upgrade-fans').checked) {
        totalInvestment += 8000;
        totalSavings += 180;
        totalCO2Reduction += 18 * baseData.co2PerKwh;
    }
    
    // Calculate derived values
    const annualSavings = totalSavings * 12;
    const paybackYears = totalInvestment / annualSavings || 0;
    const paybackTime = paybackYears.toFixed(1) + ' years';
    const roi10Year = totalInvestment > 0 ? 
        Math.round((annualSavings * 10 - totalInvestment) / totalInvestment * 100) : 0;
    
    // Update UI
    document.getElementById('appliance-investment').textContent = '₹' + totalInvestment;
    document.getElementById('appliance-monthly').textContent = '₹' + totalSavings;
    document.getElementById('appliance-annual').textContent = '₹' + annualSavings;
    document.getElementById('appliance-payback').textContent = paybackTime;
    document.getElementById('appliance-roi').textContent = roi10Year + '%';
    document.getElementById('appliance-co2').textContent = Math.round(totalCO2Reduction) + ' kg';
    
    // Update appliance chart
    updateApplianceChart();
    
    // Also update combined savings
    updateCombinedSavings();
}

// --- SOLAR CALCULATIONS ---
function updateSolarSavings() {
    const solarSize = parseFloat(document.getElementById('solar-size').value);
    const duration = parseInt(document.getElementById('solar-duration').value);
    
    // Calculate solar values based on practical estimates
    // Average solar panel efficiency in India: ~1,300-1,500 kWh per kWp per year
    const annualProductionPerKW = 1400; // kWh
    const monthlyProductionPerKW = annualProductionPerKW / 12;
    
    const installationCost = Math.round(solarSize * 53333);
    const monthlyProduction = Math.round(solarSize * monthlyProductionPerKW);
    const monthlySavings = Math.round(monthlyProduction * baseData.ratePerUnit);
    const annualSavings = monthlySavings * 12;
    const lifetimeSavings = annualSavings * 25;
    
    const paybackYears = installationCost / annualSavings;
    // Solar subsidy (40% up to a maximum)
    const subsidyAmount = Math.min(31200, installationCost * 0.4);
    const netCost = installationCost - subsidyAmount;
    const paybackWithSubsidy = netCost / annualSavings;
    
    // CO2 calculations
    const co2Reduction = Math.round(monthlyProduction * baseData.co2PerKwh);
    const lifetimeCO2 = Math.round(co2Reduction * 25 * 12);
    const treesEquivalent = Math.round(co2Reduction / 15);
    const carbonPayback = 1.2; // years for solar panels to offset their manufacturing emissions
    
    // Update UI
    document.getElementById('solar-cost').textContent = '₹' + installationCost;
    document.getElementById('solar-subsidy').textContent = '₹' + subsidyAmount;
    document.getElementById('solar-net-cost').textContent = '₹' + netCost;
    document.getElementById('solar-production').textContent = monthlyProduction + ' kWh';
    document.getElementById('solar-monthly').textContent = '₹' + monthlySavings;
    document.getElementById('solar-annual').textContent = '₹' + annualSavings;
    document.getElementById('solar-lifetime').textContent = '₹' + lifetimeSavings;
    document.getElementById('solar-payback').textContent = paybackYears.toFixed(1) + ' years';
    document.getElementById('solar-payback-subsidy').textContent = paybackWithSubsidy.toFixed(1) + ' years';
    
    document.getElementById('co2-reduction').textContent = co2Reduction + ' kg';
    document.getElementById('lifetime-co2').textContent = lifetimeCO2 + ' kg';
    document.getElementById('trees-equivalent').textContent = treesEquivalent + ' trees';
    document.getElementById('carbon-payback').textContent = carbonPayback + ' years';
    
    // Update solar chart
    updateSolarChart(duration, monthlySavings, installationCost);
    
    // Also update combined savings
    updateCombinedSavings();
}

// --- CHARTS IMPLEMENTATION ---
let habitsChart, applianceChart, solarChart, combinedChart;

function initializeCharts() {
    // Create initial charts with placeholder data
    updateHabitsChart(380, 320, 150, 250);
    updateApplianceChart();
    updateSolarChart();
    updateCombinedChart();
}

function updateAllCharts() {
    // This function refreshes all charts (useful when tabs change)
    if (document.getElementById('habitsChart')) updateHabitsChart();
    if (document.getElementById('applianceChart')) updateApplianceChart();
    if (document.getElementById('solarChart')) updateSolarChart();
    if (document.getElementById('combinedSavingsChart')) updateCombinedChart();
}

function updateHabitsChart(offpeakSavings = 380, tempSavings = 320, standbySavings = 150, seasonalSavings = 250) {
    const ctx = document.getElementById('habitsChart');
    if (!ctx) return;
    
    const currentExpense = baseData.monthlyBill;
    const newExpense = currentExpense - offpeakSavings - tempSavings - standbySavings - seasonalSavings;
    
    if (habitsChart) {
        habitsChart.destroy();
    }
    
    habitsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Current', 'With Changes'],
            datasets: [{
                label: 'Monthly Expense (₹)',
                data: [currentExpense, newExpense],
                backgroundColor: ['#f87171', '#34d399'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: currentExpense * 1.1
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

function updateApplianceChart() {
    const ctx = document.getElementById('applianceChart');
    if (!ctx) return;
    
    const upgrades = [];
    const savings = [];
    
    if (document.getElementById('upgrade-ac').checked) {
        upgrades.push('AC');
        savings.push(450);
    }
    
    if (document.getElementById('upgrade-refrigerator').checked) {
        upgrades.push('Refrigerator');
        savings.push(380);
    }
    
    if (document.getElementById('upgrade-washing').checked) {
        upgrades.push('Washing Machine');
        savings.push(220);
    }
    
    if (document.getElementById('upgrade-lights').checked) {
        upgrades.push('LED Lights');
        savings.push(150);
    }
    
    if (document.getElementById('upgrade-fans').checked) {
        upgrades.push('BLDC Fans');
        savings.push(180);
    }
    
    if (upgrades.length === 0) {
        upgrades.push('No Selection');
        savings.push(0);
    }
    
    if (applianceChart) {
        applianceChart.destroy();
    }
    
    applianceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: upgrades,
            datasets: [{
                label: 'Monthly Savings (₹)',
                data: savings,
                backgroundColor: '#60a5fa',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function updateSolarChart(years = 10, monthlySavings = 2480, installationCost = 160000) {
    const ctx = document.getElementById('solarChart');
    if (!ctx) return;
    
    // Generate data for solar ROI over years
    const labels = [];
    const savings = [];
    const investment = [];
    
    for (let i = 0; i <= years; i++) {
        labels.push('Year ' + i);
        savings.push(i * monthlySavings * 12);
        investment.push(installationCost);
    }
    
    if (solarChart) {
        solarChart.destroy();
    }
    
    solarChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Cumulative Savings',
                    data: savings,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true
                },
                {
                    label: 'Installation Cost',
                    data: investment,
                    borderColor: '#f59e0b',
                    borderDash: [5, 5]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Solar ROI Over Time'
                }
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Amount (₹)'
                    }
                }
            }
        }
    });
}

function updateCombinedChart() {
    const ctx = document.getElementById('combinedSavingsChart');
    if (!ctx) return;
    
    // Get current values from each section
    const applianceMonthly = parseInt(document.getElementById('appliance-monthly').textContent.replace('₹', '')) || 0;
    const solarMonthly = parseInt(document.getElementById('solar-monthly').textContent.replace('₹', '')) || 0;
    const habitsMonthly = parseInt(document.getElementById('habits-monthly-savings').textContent.replace('₹', '')) || 0;
    
    // Calculate yearly and long-term values
    const applianceYearly = applianceMonthly * 12;
    const solarYearly = solarMonthly * 12;
    const habitsYearly = habitsMonthly * 12;
    
    if (combinedChart) {
        combinedChart.destroy();
    }
    
    combinedChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['1 Year', '5 Years', '10 Years'],
            datasets: [
                {
                    label: 'Appliance Upgrades',
                    data: [applianceYearly, applianceYearly * 5, applianceYearly * 10],
                    backgroundColor: '#60a5fa'
                },
                {
                    label: 'Solar Installation',
                    data: [solarYearly, solarYearly * 5, solarYearly * 10],
                    backgroundColor: '#10b981'
                },
                {
                    label: 'Usage Habits',
                    data: [habitsYearly, habitsYearly * 5, habitsYearly * 10],
                    backgroundColor: '#8b5cf6'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Cumulative Savings by Approach'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ₹' + context.raw.toLocaleString();
                        }
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                },
                y: {
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Savings (₹)'
                    }
                }
            }
        }
    });
}

function updateCombinedSavings() {
    // Update the combined savings table with live values
    const applianceAnnual = parseInt(document.getElementById('appliance-annual').textContent.replace('₹', '')) || 0;
    const solarAnnual = parseInt(document.getElementById('solar-annual').textContent.replace('₹', '')) || 0;
    const habitsAnnual = parseInt(document.getElementById('habits-monthly-savings').textContent.replace('₹', '')) * 12 || 0;
    
    const totalAnnual = applianceAnnual + solarAnnual + habitsAnnual;
    
    // Update the combined chart
    updateCombinedChart();
}

// Add some CSS for slider value animation
const style = document.createElement('style');
style.textContent = `
.value-change {
    transition: all 0.3s ease;
    background-color: rgba(16, 185, 129, 0.3) !important;
    transform: scale(1.1);
}
`;
document.head.appendChild(style);