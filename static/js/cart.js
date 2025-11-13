/* ========== Cart Page JavaScript ========== */
(function () {
    'use strict';

    // Initialize cart data from template (will be set by inline script)
    let appliedPoints = 0;
    let originalTotal = 0;
    let maxPoints = 0;
    let isGuestWithoutMembership = false;

    // Translations object (will be populated by inline script)
    const translations = window.cartTranslations || {};

    function initCart(config) {
        appliedPoints = 0;
        originalTotal = config.originalTotal || 0;
        maxPoints = config.maxPoints || 0;
        isGuestWithoutMembership = config.isGuestWithoutMembership || false;

        // Show membership modal for pure guests
        if (isGuestWithoutMembership) {
            showMembershipModal();
        }

        // Setup event listeners
        setupMembershipVerification();
        setupPointRedemption();
        setupPayment();
        setupCartRemoval();
    }

    function showMembershipModal() {
        window.addEventListener('DOMContentLoaded', function () {
            const modalEl = document.getElementById('membershipModal');
            if (modalEl) {
                const modal = new bootstrap.Modal(modalEl);
                modal.show();
            }
        });
    }

    function setupMembershipVerification() {
        // Verify membership button
        const verifyBtn = document.getElementById('verifyMemberBtn');
        if (verifyBtn) {
            verifyBtn.addEventListener('click', async function () {
                const membershipNumber = document.getElementById('membershipInput').value.trim();
                const errorDiv = document.getElementById('membershipError');
                const successDiv = document.getElementById('membershipSuccess');

                if (!membershipNumber) {
                    errorDiv.textContent = translations.enterMembership || 'Please enter your membership number';
                    errorDiv.style.display = 'block';
                    return;
                }

                this.disabled = true;
                this.textContent = translations.verifying || 'Verifying...';

                try {
                    const response = await fetch('/store/api/membership/verify', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ membership_number: membershipNumber })
                    });

                    const data = await response.json();

                    if (data.success) {
                        successDiv.textContent = data.message;
                        successDiv.style.display = 'block';
                        errorDiv.style.display = 'none';
                        setTimeout(() => location.reload(), 1500);
                    } else {
                        errorDiv.textContent = data.error || translations.invalidMembership || 'Invalid membership number';
                        errorDiv.style.display = 'block';
                        successDiv.style.display = 'none';
                        this.disabled = false;
                        this.textContent = translations.verify || 'Verify';
                    }
                } catch (error) {
                    console.error(error);
                    errorDiv.textContent = translations.verificationFailed || 'Verification failed. Please try again.';
                    errorDiv.style.display = 'block';
                    this.disabled = false;
                    this.textContent = translations.verify || 'Verify';
                }
            });
        }

        // Continue as guest button
        const continueGuestBtn = document.getElementById('continueGuestBtn');
        if (continueGuestBtn) {
            continueGuestBtn.addEventListener('click', function () {
                const modalEl = document.getElementById('membershipModal');
                if (modalEl) {
                    const modalInstance = bootstrap.Modal.getInstance(modalEl);
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                }
            });
        }
    }

    function setupPointRedemption() {
        // Apply points button
        const applyBtn = document.getElementById('applyPointsBtn');
        if (applyBtn) {
            applyBtn.addEventListener('click', function () {
                const pointsInput = document.getElementById('pointsToRedeem');
                const points = parseInt(pointsInput.value) || 0;

                if (points < 100) {
                    alert(translations.minimumPoints || 'Minimum 100 points required');
                    return;
                }

                if (points > maxPoints) {
                    alert(`${translations.youOnlyHave || 'You only have'} ${maxPoints} ${translations.points || 'points'}`);
                    return;
                }

                if (points % 100 !== 0) {
                    alert(translations.multiplesOf100 || 'Points must be in multiples of 100');
                    return;
                }

                const discount = points / 100.0;
                if (discount > originalTotal) {
                    alert(translations.discountExceeds || 'Discount cannot exceed cart total');
                    return;
                }

                appliedPoints = points;
                updateTotals();

                document.getElementById('discountMessage').textContent =
                    `✓ ${translations.applied || 'Applied'} ${points} ${translations.points || 'points'} = $${discount.toFixed(2)} ${translations.discount || 'discount'}`;
                document.getElementById('discountMessage').style.display = 'block';
                document.getElementById('clearPointsBtn').style.display = 'inline-block';
            });
        }

        // Clear points button
        const clearBtn = document.getElementById('clearPointsBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', function () {
                appliedPoints = 0;
                document.getElementById('pointsToRedeem').value = 0;
                document.getElementById('discountMessage').style.display = 'none';
                this.style.display = 'none';
                updateTotals();
            });
        }
    }

    function updateTotals() {
        const discount = appliedPoints / 100.0;
        const finalTotal = Math.max(0, originalTotal - discount);
        const pointsToEarn = Math.floor(finalTotal);

        document.getElementById('discountAmount').textContent = `$${discount.toFixed(2)}`;
        document.getElementById('finalTotal').textContent = `$${finalTotal.toFixed(2)}`;
        document.getElementById('totalDisplay').textContent = `$${finalTotal.toFixed(2)}`;
        document.getElementById('pointsToEarn').textContent = pointsToEarn;

        const discountRow = document.getElementById('discountRow');
        if (discountRow) {
            discountRow.style.display = discount > 0 ? 'block' : 'none';
        }
    }

    function setupPayment() {
        const paymentBtn = document.getElementById('completePaymentBtn');
        if (paymentBtn) {
            paymentBtn.addEventListener('click', async function () {
                if (!confirm(translations.confirmPayment || 'Complete payment and finalize purchase?')) {
                    return;
                }

                this.disabled = true;
                this.textContent = translations.processing || 'Processing...';

                try {
                    const response = await fetch('/store/api/purchase', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ points_to_redeem: appliedPoints })
                    });

                    const data = await response.json();

                    if (data.success) {
                        document.getElementById('paymentMessage').textContent = data.message;

                        // Hide receipt link for pure guests
                        if (isGuestWithoutMembership) {
                            const receiptLink = document.getElementById('viewReceiptLink');
                            const receiptEmail = document.getElementById('receiptEmailMsg');
                            if (receiptLink) receiptLink.style.display = 'none';
                            if (receiptEmail) receiptEmail.style.display = 'none';
                        }

                        const modal = new bootstrap.Modal(document.getElementById('paymentSuccessModal'));
                        modal.show();
                    } else {
                        alert(`${translations.paymentFailed || 'Payment failed'}: ${data.error || translations.unknownError || 'Unknown error'}`);
                        this.disabled = false;
                        this.textContent = translations.completePayment || 'Complete Payment';
                    }
                } catch (error) {
                    console.error(error);
                    alert(translations.networkError || 'Network error during payment');
                    this.disabled = false;
                    this.textContent = translations.completePayment || 'Complete Payment';
                }
            });
        }
    }

    function setupCartRemoval() {
        document.querySelectorAll('.remove-item').forEach(btn => {
            btn.addEventListener('click', async function () {
                const productId = this.dataset.productId;
                try {
                    const response = await fetch('/store/api/cart/remove', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ product_id: parseInt(productId) })
                    });

                    if (response.ok) {
                        location.reload();
                    }
                } catch (error) {
                    console.error('Remove error:', error);
                }
            });
        });
    }

    // Expose init function globally
    window.initCart = initCart;
})();
