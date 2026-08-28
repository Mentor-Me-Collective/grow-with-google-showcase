/* Shared public-navigation controller. Every public page loads this file. */
(() => {
  const getPageAndHash = () => {
    const currentFile = (window.location.pathname.split('/').pop() || 'index.html').toLowerCase();
    const currentPage = currentFile === 'index.html' ? 'home' : currentFile.replace(/\.html$/, '');
    const currentHash = window.location.hash.toLowerCase() || (currentPage === 'home' ? '#home' : '');
    return { page: currentPage, hash: currentHash };
  };

  const pageForLink = (link) => {
    const href = (link.getAttribute('href') || '').toLowerCase();
    
    // Hash links on Home page
    if (href.startsWith('#')) {
      return { page: 'home', hash: href };
    }
    
    // Links pointing to index.html with or without hash
    if (href === 'index.html' || href.startsWith('index.html#')) {
      const idx = href.indexOf('#');
      const hash = idx !== -1 ? href.substring(idx) : '#home';
      return { page: 'home', hash: hash };
    }

    // Direct page routing
    if (href === 'about.html') return { page: 'about', hash: '' };
    if (href === 'how-it-works.html') return { page: 'how-it-works', hash: '' };
    if (href === 'communities.html') return { page: 'communities', hash: '' };
    if (href === 'impact.html') return { page: 'impact', hash: '' };
    if (href === 'faq.html') return { page: 'faq', hash: '' };
    if (href === 'contact.html') return { page: 'contact', hash: '' };
    if (href === 'login.html') return { page: 'login', hash: '' };
    if (href === 'join.html') return { page: 'join', hash: '' };
    
    // Fallback matching relative pages (like inside secondary directory)
    const pageName = href.replace(/\.html$/, '');
    return { page: pageName, hash: '' };
  };

  const syncPublicNavigation = () => {
    const current = getPageAndHash();
    
    document.querySelectorAll('.nav-item, .drawer-item').forEach((link) => {
      const target = pageForLink(link);
      let isCurrent = false;

      if (current.page === 'home') {
        // If current page is home, match page 'home' and the correct hash location
        isCurrent = (target.page === 'home' && target.hash === current.hash);
      } else {
        // Otherwise on separate sub-pages, check if URL matches the direct sub-page
        isCurrent = (target.page === current.page);
      }

      link.classList.toggle('active', isCurrent);
      if (isCurrent) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
  };

  // Listen to hash changes (for in-page navigation tabs / scrolling clicks)
  window.addEventListener('hashchange', syncPublicNavigation);
  window.addEventListener('popstate', syncPublicNavigation);

  // Sync on click behavior immediately to prevent UI lag before browser hashes resolve
  document.addEventListener('click', (e) => {
    const link = e.target.closest('.nav-item, .drawer-item');
    if (!link) return;
    
    // Let browser navigate, but trigger visual toggle switch next tick
    setTimeout(syncPublicNavigation, 25);
  });

  window.PublicNavigation = { sync: syncPublicNavigation };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', syncPublicNavigation);
  else syncPublicNavigation();
})();
