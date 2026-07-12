/**
 * Tunas Daud E-Voting Portal - Frontend Applications Script
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log("✅ Tunas Daud app.js successfully loaded!");

    // 1. Fetch Modal Elements
    const backdrop = document.getElementById('custom-modal-backdrop');
    const content = document.getElementById('custom-modal-content');
    const titleEl = document.getElementById('custom-modal-title');
    const messageEl = document.getElementById('custom-modal-message');
    const btnConfirm = document.getElementById('custom-modal-confirm');
    const btnConfirmText = document.getElementById('custom-modal-confirm-text');
    const btnCancel = document.getElementById('custom-modal-cancel');

    const manifestoBackdrop = document.getElementById('manifesto-modal-backdrop');
    const manifestoContent = document.getElementById('manifesto-modal-content');
    const manifestoTitleEl = document.getElementById('manifesto-modal-title');
    const manifestoBodyEl = document.getElementById('manifesto-modal-body');
    const manifestoClose = document.getElementById('manifesto-modal-close');

    if (!backdrop || !content || !titleEl || !messageEl || !btnConfirm || !btnConfirmText || !btnCancel || !manifestoBackdrop || !manifestoContent || !manifestoTitleEl || !manifestoBodyEl || !manifestoClose) {
        console.error("❌ Custom modal HTML IDs not found in base.html! Check your HTML IDs.");
        return; 
    }

    let currentIssueRequest = null;

    // Function to smoothly show the vote confirmation modal
    function showModal({ title, message, issueRequestFn = null, confirmText = 'Yes, Cast My Vote', cancelText = 'Cancel', showConfirm = true }) {
        currentIssueRequest = issueRequestFn;
        titleEl.innerText = title;
        messageEl.innerText = message;
        btnConfirmText.innerText = confirmText;
        btnCancel.innerText = cancelText;

        if (showConfirm) {
            btnConfirm.classList.remove('hidden');
        } else {
            btnConfirm.classList.add('hidden');
        }

        backdrop.classList.remove('hidden');
        setTimeout(() => {
            backdrop.classList.remove('opacity-0');
            content.classList.remove('scale-95');
            content.classList.add('scale-100');
        }, 10);
    }

    // Function to smoothly hide the vote confirmation modal
    function hideModal() {
        backdrop.classList.add('opacity-0');
        content.classList.remove('scale-100');
        content.classList.add('scale-95');
        
        setTimeout(() => {
            backdrop.classList.add('hidden');
            currentIssueRequest = null;
        }, 200);
    }

    // Function to smoothly show the manifesto viewer modal
    function showManifestoModal({ title, message }) {
        manifestoTitleEl.innerText = title;
        manifestoBodyEl.innerText = message;

        manifestoBackdrop.classList.remove('hidden');
        setTimeout(() => {
            manifestoBackdrop.classList.remove('opacity-0');
            manifestoContent.classList.remove('scale-95');
            manifestoContent.classList.add('scale-100');
        }, 10);
    }

    // Function to smoothly hide the manifesto viewer modal
    function hideManifestoModal() {
        manifestoBackdrop.classList.add('opacity-0');
        manifestoContent.classList.remove('scale-100');
        manifestoContent.classList.add('scale-95');
        
        setTimeout(() => {
            manifestoBackdrop.classList.add('hidden');
        }, 200);
    }

    // 2. THE MASTER FIX: Listen to all HTMX requests and check for our data-confirm attribute!
    document.body.addEventListener('htmx:confirm', function(evt) {
        const elt = evt.target;
        
        // Safely check if the form (or a button inside it) has our custom data-confirm attribute
        const confirmMsg = elt.getAttribute('data-confirm') || 
                           elt.querySelector('[data-confirm]')?.getAttribute('data-confirm');

        if (confirmMsg) {
            console.log("🛑 Intercepted vote submission! Showing custom glassmorphism modal...");
            evt.preventDefault(); // Stop HTMX from sending the vote immediately!
            
            showModal({
                title: 'Official Ballot Confirmation',
                message: confirmMsg,
                issueRequestFn: () => {
                    console.log("🚀 User confirmed! Sending ballot to server...");
                    evt.detail.issueRequest(true);
                },
                confirmText: 'Yes, Cast My Vote',
                cancelText: 'Cancel',
                showConfirm: true
            });
        }
    });

    document.body.addEventListener('click', function(evt) {
        const readMoreButton = evt.target.closest('[data-read-more]');
        if (!readMoreButton) return;
        evt.preventDefault();

        const card = readMoreButton.closest('[data-candidate-card]');
        if (!card) return;

        const manifestoText = card.querySelector('[data-manifesto-text]')?.textContent.trim() || '';
        const candidateName = card.querySelector('[data-candidate-name]')?.textContent.trim() || 'Candidate';

        showManifestoModal({
            title: `${candidateName} `,
            message: manifestoText
        });
    });

    // 3. Button Click Listeners
    btnConfirm.addEventListener('click', () => {
        if (currentIssueRequest) {
            currentIssueRequest();
        }
        hideModal();
    });

    btnCancel.addEventListener('click', hideModal);

    backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) hideModal();
    });

    manifestoBackdrop.addEventListener('click', (e) => {
        if (e.target === manifestoBackdrop) hideManifestoModal();
    });

    manifestoClose.addEventListener('click', hideManifestoModal);
});