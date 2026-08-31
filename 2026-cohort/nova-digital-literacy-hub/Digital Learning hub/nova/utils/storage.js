// ============================================
// LOCAL STORAGE UTILITIES
// localStorage is a built-in browser feature.
// It saves small amounts of data on the user's computer.
// This means progress is saved even without internet,
// and no server or database is needed for the MVP.
// ============================================

import { modules } from '../data/modules'

const PROFILE_KEY = 'nova_profile'
const PROGRESS_KEY = 'nova_progress'

/**
 * getProfile
 * Reads the saved learner profile from localStorage.
 * Returns null if no profile exists yet.
 */
export const getProfile = () => {
  try {
    const data = localStorage.getItem(PROFILE_KEY)
    return data ? JSON.parse(data) : null
  } catch (error) {
    return null
  }
}

/**
 * saveProfile
 * Saves the learner's name and PIN to localStorage.
 */
export const saveProfile = (profile) => {
  localStorage.setItem(PROFILE_KEY, JSON.stringify(profile))
}

/**
 * getProgress
 * Reads the learner's progress.
 * If nothing is saved yet, returns a fresh empty progress object.
 */
export const getProgress = () => {
  try {
    const data = localStorage.getItem(PROGRESS_KEY)
    return data
      ? JSON.parse(data)
      : { completedLessons: [], quizScores: {}, modulesCompleted: [] }
  } catch (error) {
    return { completedLessons: [], quizScores: {}, modulesCompleted: [] }
  }
}

/**
 * saveProgress
 * Overwrites the entire progress object in localStorage.
 */
export const saveProgress = (progress) => {
  localStorage.setItem(PROGRESS_KEY, JSON.stringify(progress))
}

/**
 * markLessonComplete
 * Adds a lesson to the completed list if it is not already there.
 * We identify each lesson with a string like "internet-basics-1".
 */
export const markLessonComplete = (moduleId, lessonId) => {
  const progress = getProgress()
  const key = `${moduleId}-${lessonId}`
  if (!progress.completedLessons.includes(key)) {
    progress.completedLessons.push(key)
    saveProgress(progress)
  }
}

/**
 * saveQuizScore
 * Saves the quiz score. Only keeps the HIGHEST score ever achieved.
 * Also marks the module as "completed" if:
 *   1. All lessons in that module are finished, AND
 *   2. The quiz score is at least 60%.
 */
export const saveQuizScore = (moduleId, score) => {
  const progress = getProgress()

  // Make absolutely sure the score is a valid percentage
  const safeScore = Math.min(
    100,
    Math.max(0, Number(score) || 0)
  )

  const currentHigh =
    progress.quizScores[moduleId] || 0

  progress.quizScores[moduleId] = Math.max(
    currentHigh,
    safeScore
  )

  const module = modules.find(
    (m) => m.id === moduleId
  )

  if (!module) {
    saveProgress(progress)
    return
  }

  const allLessonsDone =
    module.lessons.every((lesson) =>
      progress.completedLessons.includes(
        `${moduleId}-${lesson.id}`
      )
    )

  if (
    allLessonsDone &&
    safeScore >= 60 &&
    !progress.modulesCompleted.includes(moduleId)
  ) {
    progress.modulesCompleted.push(moduleId)
  }

  saveProgress(progress)
}
