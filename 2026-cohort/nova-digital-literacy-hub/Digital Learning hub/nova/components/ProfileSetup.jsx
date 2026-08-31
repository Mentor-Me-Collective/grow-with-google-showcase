import React, { useState } from 'react'
import { saveProfile } from '../utils/storage'

const API_URL = 'http://127.0.0.1:8000'

// ============================================
// PROFILE SETUP COMPONENT
// Creates a local profile AND registers the
// learner with the FastAPI backend.
// ============================================

function ProfileSetup({ onProfileCreated }) {
  const [name, setName] = useState('')
  const [pin, setPin] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!name.trim()) return

    setLoading(true)
    setError('')

    try {
      // Send learner to FastAPI
      const response = await fetch(`${API_URL}/learners`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: name.trim()
        })
      })

      if (!response.ok) {
        throw new Error('Could not create learner')
      }

      // Get the learner ID created by SQLite
      const learner = await response.json()

      // Save profile locally
      const profile = {
        learner_id: learner.learner_id,
        name: learner.name,
        pin: pin || null
      }

      saveProfile(profile)

      // Tell the parent component profile creation succeeded
      onProfileCreated(profile)

    } catch (error) {
      console.error(error)
      setError('Unable to create your profile. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="profile-setup">
      <h1>Welcome to Nova Digital Literacy Hub</h1>

      <p>
        Create your profile to start learning. No email needed!
      </p>

      <form onSubmit={handleSubmit}>

        <label>
          Your Name:
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter your name"
            required
          />
        </label>

        <label>
          Optional 4-digit PIN:
          <input
            type="password"
            maxLength={4}
            value={pin}
            onChange={(e) =>
              setPin(e.target.value.replace(/\D/g, ''))
            }
            placeholder="1234"
          />
        </label>

        <button type="submit" disabled={loading}>
          {loading ? 'Creating Profile...' : 'Start Learning'}
        </button>

        {error && (
          <p style={{ color: 'red' }}>
            {error}
          </p>
        )}

      </form>
    </div>
  )
}

export default ProfileSetup