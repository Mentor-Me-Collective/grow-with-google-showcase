import React from 'react'
import Link from 'next/link'

// ============================================
// LAYOUT COMPONENT
// This component wraps EVERY page in the app.
// It provides the top navigation bar and the footer
// so we do not have to repeat them on every screen.
// ============================================

function Layout({ profile, children }) {
  return (
    <div className="app">
      {/* --- HEADER --- */}
      <header>
        <h1>Nova Digital Literacy Hub</h1>

        {/* Navigation links using Next.js Link (no page reload) */}
        <nav>
          <Link href="/">Modules</Link>
          <Link href="/dashboard">Dashboard</Link>
          <Link href="/badge">Badge</Link>
        </nav>

        {/* Show the learner's name in the corner */}
        <span className="profile-name">Hi, {profile.name}!</span>
      </header>

      {/* --- MAIN CONTENT --- */}
      <main>{children}</main>

      {/* --- FOOTER --- */}
      <footer>
        <p>UN SDG 4 — Quality Education | Nova Architects</p>
      </footer>
    </div>
  )
}

export default Layout
