
// Content script that runs on L&I pages
console.log("L&I Auto-Scraper Active");

// Auto-fill and submit search if on search page
if (window.location.href.includes("prc_carrlist")) {
    // Get USDOT from URL params or storage
    chrome.storage.local.get(['pending_usdots'], function(result) {
        if (result.pending_usdots && result.pending_usdots.length > 0) {
            const usdot = result.pending_usdots[0];
            
            // Fill in USDOT
            const input = document.querySelector('input[name="n_dotno"]');
            if (input) {
                input.value = usdot;
                
                // Submit form
                setTimeout(() => {
                    const form = input.closest('form');
                    if (form) form.submit();
                }, 1000);
            }
        }
    });
}

// Auto-click Active Insurance link
const insuranceLinks = Array.from(document.querySelectorAll('a'));
const activeInsuranceLink = insuranceLinks.find(link => 
    link.textContent.includes('Active Insurance')
);

if (activeInsuranceLink) {
    setTimeout(() => {
        activeInsuranceLink.click();
    }, 2000);
}

// Scrape insurance data if on insurance page
if (window.location.href.includes("prc_activeinsurance")) {
    const pageText = document.body.innerText;
    
    const insuranceData = {
        usdot: new URLSearchParams(window.location.search).get('pn_dotno'),
        company: null,
        policy: null,
        amount: null,
        date: null
    };
    
    // Extract insurance company
    if (pageText.includes('GEICO MARINE INSURANCE COMPANY')) {
        insuranceData.company = 'GEICO MARINE INSURANCE COMPANY';
    }
    
    // Extract policy number
    const policyMatch = pageText.match(/\b(9\d{9})\b/);
    if (policyMatch) {
        insuranceData.policy = policyMatch[1];
    }
    
    // Extract dates
    const dates = pageText.match(/\b(\d{1,2}\/\d{1,2}\/\d{4})\b/g);
    if (dates && dates.length > 0) {
        insuranceData.date = dates[dates.length - 1];
    }
    
    // Send data to background script
    chrome.runtime.sendMessage({
        type: 'insurance_data',
        data: insuranceData
    });
    
    // Remove this USDOT from pending and move to next
    chrome.storage.local.get(['pending_usdots'], function(result) {
        if (result.pending_usdots) {
            const remaining = result.pending_usdots.filter(u => u != insuranceData.usdot);
            chrome.storage.local.set({pending_usdots: remaining});
            
            // Go to next USDOT
            if (remaining.length > 0) {
                setTimeout(() => {
                    window.location.href = 'https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist';
                }, 3000);
            }
        }
    });
}
        