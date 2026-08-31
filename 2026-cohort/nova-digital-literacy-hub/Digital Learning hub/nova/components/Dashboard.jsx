import React, { useEffect, useState } from 'react'

const API_URL = 'http://127.0.0.1:8000'

function Dashboard() {
  const [progress, setProgress] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadProgress = async () => {
      try {
        const savedProfile = localStorage.getItem('nova_profile')

        if (!savedProfile) {
          setError('No learner profile found.')
          return
        }

        const profile = JSON.parse(savedProfile)

        const response = await fetch(
          `${API_URL}/learners/${profile.learner_id}/progress`
        )

        if (!response.ok) {
          throw new Error('Failed to load progress')
        }

        const data = await response.json()

        console.log('Dashboard progress:', data)

        setProgress(data)

      } catch (err) {
        console.error('Dashboard error:', err)
        setError('Unable to load your progress.')
      }
    }

    loadProgress()
  }, [])

  if (error) {
    return (
      <div className="dashboard">
        <h2>Your Progress</h2>
        <p>{error}</p>
      </div>
    )
  }

  if (!progress) {
    return (
      <div className="dashboard">
        <h2>Your Progress</h2>
        <p>Loading your progress...</p>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <h2>Your Progress</h2>

      <p>
        Keep going, <strong>{progress.learner_name}</strong>!
      </p>

      <div className="overall">
        <h3>
          Overall Completion: {Math.round(progress.overall_progress)}%
        </h3>

        <div className="progress-bar">
          <div
            style={{
              width: `${progress.overall_progress}%`
            }}
          />
        </div>
      </div>

      <div className="module-progress">
        {progress.modules.map((module) => (
          <div
            key={module.module_id}
            className="module-status"
          >
            <h4>
              {module.module_title}{' '}
              {module.completed && <span>✓</span>}
            </h4>

            <p>
              Status:{' '}
              {module.completed
                ? 'Completed'
                : 'Not completed'}
            </p>

            <p>
              Lessons completed: {module.completed_lessons}
            </p>

            <p>
              Quiz Score:{' '}
              {module.latest_quiz_percentage !== null
                ? `${module.latest_quiz_percentage}%`
                : 'Not taken yet'}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Dashboard