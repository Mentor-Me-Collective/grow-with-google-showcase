import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import { modules } from '../data/modules'
import { markLessonComplete, getProgress } from '../utils/storage'

const API_URL = 'http://127.0.0.1:8000'

const backendModuleIds = {
  'internet-basics': 1,
  'email-basics': 2,
  'online-safety': 3,
}

const getBackendModuleId = (moduleId) => {
  return backendModuleIds[moduleId]
}

// ============================================
// LESSON VIEWER COMPONENT
// This screen displays one lesson at a time.
// It shows the lesson icon, text, step-by-step instructions,
// and buttons to move to the next or previous lesson.
// ============================================

function LessonViewer({ onProgressUpdate }) {
  const router = useRouter()
  const { moduleId, lessonId } = router.query
  console.log("ROUTE PARAMS:", { moduleId, lessonId })
  console.log("MODULE DATA:", modules)

  const module = modules.find((m) => m.id === moduleId)
  const lesson = module?.lessons.find((l) => l.id === parseInt(lessonId))

  const [isComplete, setIsComplete] = useState(false)

  useEffect(() => {
    if (!moduleId || !lessonId) return
    const progress = getProgress()
    setIsComplete(progress.completedLessons.includes(`${moduleId}-${lessonId}`))
  }, [moduleId, lessonId])

  if (!moduleId || !lessonId) {
    return <div className="lesson-viewer"><h2>Loading...</h2></div>
  }

  if (!module || !lesson) {
    return <div className="lesson-viewer"><h2>Lesson not found</h2></div>
  }

  const currentIndex = module.lessons.findIndex(
    (l) => l.id === parseInt(lessonId)
  )
  const isLastLesson = currentIndex === module.lessons.length - 1

  const handleMarkComplete = async () => {
  try {
    const profile = JSON.parse(
      localStorage.getItem('nova_profile')
    )

    if (!profile?.learner_id) {
      alert('Learner profile not found.')
      return
    }

    const response = await fetch(
      `${API_URL}/learners/${profile.learner_id}/modules/${getBackendModuleId(moduleId)}/lessons/${lessonId}/complete`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )

    if (!response.ok) {
      throw new Error('Could not save lesson progress')
    }

    // Keep local storage too
    markLessonComplete(moduleId, parseInt(lessonId))

    setIsComplete(true)

    if (onProgressUpdate) {
      onProgressUpdate()
    }

  } catch (error) {
    console.error(error)
    alert('Could not save lesson progress.')
  }
}

  const handleNext = () => {
    if (!isLastLesson) {
      const nextLesson = module.lessons[currentIndex + 1]
      router.push(`/module/${moduleId}/lesson/${nextLesson.id}`)
    } else {
      router.push(`/module/${moduleId}/quiz`)
    }
  }

  return (
    <div className="lesson-viewer">
      {/* Module icon and title at the top */}
      <div className="lesson-header">
        <span className="lesson-module-icon">{module.icon}</span>
        <h2>{module.title}</h2>
      </div>

      {/* Lesson icon and title */}
      <div className="lesson-title-row">
        <span className="lesson-icon">{lesson.icon}</span>
        <h3>
          Lesson {lesson.id}: {lesson.title}
        </h3>
      </div>

      <div className="lesson-content">
        <p>{lesson.content}</p>
        <h4>Steps:</h4>
        <ol>
          {lesson.steps.map((step, idx) => (
            <li key={idx}>{step}</li>
          ))}
        </ol>
      </div>

      <div className="lesson-actions">
        {currentIndex > 0 && (
          <button
            onClick={() =>
              router.push(
                `/module/${moduleId}/lesson/${module.lessons[currentIndex - 1].id}`
              )
            }
          >
             Previous
          </button>
        )}

        {!isComplete ? (
          <button onClick={handleMarkComplete} className="btn-primary">
            Mark as Complete
          </button>
        ) : (
          <span className="completed-badge"> Completed</span>
        )}

        {isComplete && (
          <button onClick={handleNext} className="btn-primary">
            {isLastLesson ? 'Take Quiz' : 'Next Lesson'}
          </button>
        )}
      </div>
    </div>
  )
}

export default LessonViewer