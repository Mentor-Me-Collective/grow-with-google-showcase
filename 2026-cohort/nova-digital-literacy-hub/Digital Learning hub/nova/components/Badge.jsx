import React from 'react'
import { useRouter } from 'next/router'
import { modules } from '../data/modules'

// ============================================
// BADGE COMPONENT
// This page shows a completion badge once ALL
// three modules are finished. If not finished,
// it encourages the learner to keep going.
// ============================================

function Badge({ progress }) {
  const router = useRouter()
  const prog = progress || { modulesCompleted: [] }
  const allComplete = prog.modulesCompleted.length === modules.length

  if (!allComplete) {
    return (
      <div className="badge-page">
        <h2>Completion Badge</h2>
        <p>Complete all modules to unlock your badge!</p>
        <p>
          Progress: {prog.modulesCompleted.length} / {modules.length} modules
        </p>
        <button onClick={() => router.push('/')}>Continue Learning</button>
      </div>
    )
  }

  return (
    <div className="badge-page">
      <h2>&#127881; Congratulations! &#127881;</h2>
      <div className="badge-display">
        <h3>Digital Literacy Graduate</h3>
        <p>You have successfully completed all learning modules!</p>
      </div>
      <button onClick={() => window.print()}>Print Certificate</button>
      <button onClick={() => router.push('/')}>Back to Home</button>
    </div>
  )
}

export default Badge
