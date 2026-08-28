const closeItem = (button) => {
  const panel = document.getElementById(button.getAttribute('aria-controls'));
  const symbol = button.querySelector('b');
  button.setAttribute('aria-expanded', 'false');
  if (symbol) {
    symbol.textContent = '+';
  }
  panel.classList.remove('open');
  setTimeout(() => {
    if (button.getAttribute('aria-expanded') === 'false') {
      panel.hidden = true;
    }
  }, 250);
};

document.querySelectorAll('.faq-item button').forEach(button => {
  button.addEventListener('click', () => {
    const isCurrentlyOpen = button.getAttribute('aria-expanded') === 'true';
    
    // Close other open questions
    document.querySelectorAll('.faq-item button').forEach(other => {
      if (other !== button) {
        closeItem(other);
      }
    });

    if (isCurrentlyOpen) {
      closeItem(button);
    } else {
      const panel = document.getElementById(button.getAttribute('aria-controls'));
      const symbol = button.querySelector('b');
      panel.hidden = false;
      button.setAttribute('aria-expanded', 'true');
      if (symbol) {
        symbol.textContent = '−';
      }
      requestAnimationFrame(() => panel.classList.add('open'));
    }
  });
});

