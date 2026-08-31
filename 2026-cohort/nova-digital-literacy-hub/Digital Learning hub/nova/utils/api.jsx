const API_URL = 'http://127.0.0.1:8000'

export const createLearner = async (name) => {
  const response = await fetch(`${API_URL}/learners`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name: name,
    }),
  })

  if (!response.ok) {
    throw new Error('Failed to create learner')
  }

  return response.json()
}

export const submitQuiz = async (moduleId, learnerId, answers) => {
  const response = await fetch(`${API_URL}/modules/${moduleId}/quiz`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      learner_id: learnerId,
      answers: answers,
    }),
  })

  if (!response.ok) {
    throw new Error('Failed to submit quiz')
  }

  return response.json()
}

export const getLearnerProgress = async (learnerId) => {
  const response = await fetch(
    `${API_URL}/learners/${learnerId}/progress`
  )

  if (!response.ok) {
    throw new Error('Failed to get learner progress')
  }

  return response.json()
}