import React from 'react'
import Link from 'next/link'
import { modules } from '../data/modules'

function ModuleList() {
  return (
    <div className="module-list">
      <h2>Learning Modules</h2>

      <div className="modules-grid">
        {modules.map((module) => (
          <div key={module.id} className="module-card">

            <h3>{module.title}</h3>

            <p>{module.description}</p>

            <Link
              href={`/module/${module.id}/lesson/${module.lessons[0].id}`}
              className="btn"
            >
              Start Module
            </Link>

          </div>
        ))}
      </div>
    </div>
  )
}

export default ModuleList