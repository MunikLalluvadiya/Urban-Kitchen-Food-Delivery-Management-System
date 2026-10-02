/**
 * URBAN KITCHEN – Food & Beverage
 * Front-end interactive functionality
 */

document.addEventListener('DOMContentLoaded', () => {

  // 1. Mobile Navigation Drawer
  const mobileToggle = document.querySelector('.mobile-menu-toggle');
  const drawer = document.querySelector('.mobile-nav-drawer');
  const drawerClose = document.querySelector('.drawer-close');

  if (mobileToggle && drawer) {
    mobileToggle.addEventListener('click', () => {
      drawer.classList.add('open');
    });
  }

  if (drawerClose && drawer) {
    drawerClose.addEventListener('click', () => {
      drawer.classList.remove('open');
    });
  }

  // 2. Flash Alert Dismissal
  document.querySelectorAll('.alert-close').forEach(btn => {
    btn.addEventListener('click', () => {
      const alertBox = btn.closest('.alert');
      if (alertBox) {
        alertBox.style.opacity = '0';
        alertBox.style.transform = 'translateY(-10px)';
        setTimeout(() => alertBox.remove(), 250);
      }
    });
  });

  // 3. Quantity Controls (+ / - buttons)
  document.querySelectorAll('.qty-btn').forEach(button => {
    button.addEventListener('click', (e) => {
      const isPlus = button.dataset.action === 'plus';
      const container = button.closest('.quantity-control');
      const input = container ? container.querySelector('.qty-input') : null;
      if (!input) return;

      let currentVal = parseInt(input.value, 10) || 1;
      if (isPlus) {
        currentVal += 1;
      } else {
        if (currentVal > 1) {
          currentVal -= 1;
        }
      }
      input.value = currentVal;

      // Auto-submit if inside a cart update form
      const cartUpdateForm = button.closest('.cart-qty-form');
      if (cartUpdateForm) {
        cartUpdateForm.submit();
      }
    });
  });

  // 4. Checkout Payment Method Selector
  const paymentCards = document.querySelectorAll('.payment-method-card');
  const paymentRadioInputs = document.querySelectorAll('input[name="payment_method"]');
  const detailPanels = document.querySelectorAll('.payment-details-panel');

  if (paymentCards.length > 0) {
    paymentCards.forEach(card => {
      card.addEventListener('click', () => {
        paymentCards.forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');

        const radio = card.querySelector('input[type="radio"]');
        if (radio) {
          radio.checked = true;
          const method = radio.value;

          // Toggle corresponding input panels
          detailPanels.forEach(panel => {
            if (panel.dataset.method === method) {
              panel.classList.add('active');
            } else {
              panel.classList.remove('active');
            }
          });
        }
      });
    });
  }

  // 5. Category Navigation Scrolling on Menu Page
  const catPills = document.querySelectorAll('.category-pill');
  catPills.forEach(pill => {
    pill.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = pill.getAttribute('href');
      if (!targetId || targetId === '#') return;
      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        catPills.forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

});
