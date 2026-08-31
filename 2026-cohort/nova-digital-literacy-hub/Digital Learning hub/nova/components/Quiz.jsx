import React, { useState } from 'react'
import { useRouter } from 'next/router'
import { modules } from '../data/modules'
import { saveQuizScore, getProgress } from '../utils/storage'

const API_URL = 'http://127.0.0.1:8000'

const backendModuleIds = {
  'internet-basics': 1,
  'email-basics': 2,
  'online-safety': 3,
}

const backendQuestionIds = {
  'internet-basics': [1, 2, 3],
  'email-basics': [4, 5, 6],
  'online-safety': [7, 8, 9],
}

function Quiz({ onProgressUpdate }) {
  const router = useRouter()
  const { moduleId } = router.query

  const module = modules.find((m) => m.id === moduleId)

  const [currentQ, setCurrentQ] = useState(0)
  const [selected, setSelected] = useState(null)
  const [score, setScore] = useState(0)
  const [showFeedback, setShowFeedback] = useState(false)
  const [finished, setFinished] = useState(false)
  const [answers, setAnswers] = useState([])
  const [backendResult, setBackendResult] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  if (!moduleId) {
    return <div className="quiz"><h2>Loading...</h2></div>
  }

  if (!module) {
    return <div className="quiz"><h2>Module not found</h2></div>
  }

  const question = module.quiz[currentQ]

  const handleAnswer = () => {
    if (selected === null) return

    const isCorrect = selected === question.answer

    if (isCorrect) {
      setScore((s) => s + 1)
    }

    setAnswers((previous) => [
      ...previous,
      {
        questionIndex: currentQ,
        selectedAnswer: question.options[selected],
      },
    ])

    setShowFeedback(true)
  }

  const handleNext = async () => {

  // ============================================
  // MOVE TO NEXT QUESTION
  // ============================================

  if (currentQ < module.quiz.length - 1) {

    setCurrentQ((c) => c + 1)
    setSelected(null)
    setShowFeedback(false)

    return
  }

  // ============================================
  // LAST QUESTION
  // ============================================

  // At this point, "score" contains the number
  // of correct answers BEFORE the final question.
  //
  // So we need to check the final question once.

  const finalQuestionCorrect =
    selected === question.answer

  const finalScore =
    score + (finalQuestionCorrect ? 1 : 0)

  const finalPercentage = Math.round(
    (finalScore / module.quiz.length) * 100
  )

  console.log('Final score:', finalScore)
  console.log('Final percentage:', finalPercentage)

  // ============================================
  // SAVE FRONTEND SCORE
  // ============================================

  saveQuizScore(
    moduleId,
    finalPercentage
  )

  // ============================================
  // GET LEARNER PROFILE
  // ============================================

  let profile = null

  try {

    const savedProfile =
      localStorage.getItem('nova_profile')

    profile = savedProfile
      ? JSON.parse(savedProfile)
      : null

  } catch (error) {

    console.error(
      'Could not read learner profile',
      error
    )

  }

  // ============================================
  // MAKE SURE LEARNER EXISTS
  // ============================================

  if (!profile?.learner_id) {

    setError(
      'Quiz completed, but no learner ID was found.'
    )

    setFinished(true)

    return
  }

  // ============================================
  // GET BACKEND IDs
  // ============================================

  const backendModuleId =
    backendModuleIds[moduleId]

  const questionIds =
    backendQuestionIds[moduleId]

  // ============================================
  // ADD FINAL ANSWER TO ALL ANSWERS
  // ============================================

  const allAnswers = answers

  // ============================================
  // CONVERT TO FASTAPI FORMAT
  // ============================================

  const backendAnswers =
    allAnswers.map((answer) => ({
      question_id:
        questionIds[answer.questionIndex],

      selected_answer:
        answer.selectedAnswer,
    }))

  console.log(
    'Sending answers to backend:',
    backendAnswers
  )

  // ============================================
  // SEND TO FASTAPI
  // ============================================

  try {

    setSubmitting(true)
    setError('')

    const response = await fetch(
      `${API_URL}/modules/${backendModuleId}/quiz`,
      {
        method: 'POST',

        headers: {
          'Content-Type': 'application/json',
        },

        body: JSON.stringify({
          learner_id:
            profile.learner_id,

          answers:
            backendAnswers,
        }),
      }
    )

    // ==========================================
    // CHECK BACKEND RESPONSE
    // ==========================================

    if (!response.ok) {

      const errorText =
        await response.text()

      console.error(
        'Backend error:',
        errorText
      )

      throw new Error(
        'Backend quiz submission failed'
      )
    }

    // ==========================================
    // GET BACKEND RESULT
    // ==========================================

    const result =
      await response.json()

    console.log(
      'Backend quiz result:',
      result
    )

    setBackendResult(result)

    setFinished(true)

    if (onProgressUpdate) {
      onProgressUpdate()
    }

  } catch (error) {

    console.error(error)

    setError(
      'Your quiz score was saved locally, but the server could not save the result.'
    )

    setFinished(true)

  } finally {

    setSubmitting(false)

  }
}

  const handleRetake = () => {
    setCurrentQ(0)
    setSelected(null)
    setScore(0)
    setShowFeedback(false)
    setFinished(false)
    setAnswers([])
    setBackendResult(null)
    setError('')
  }

  // RESULTS SCREEN

  if (finished) {

    const localPercentage = Math.round(
      (score / module.quiz.length) * 100
    )

    const displayedPercentage =
      backendResult?.percentage ?? localPercentage

    const progress = getProgress()

    const highScore =
      progress.quizScores[moduleId] || 0

    return (
      <div className="quiz-results">

        <h2>Quiz Complete!</h2>

        <p>
          Your score this attempt: {displayedPercentage}%
        </p>

        <p>
          Highest score saved: {highScore}%
        </p>

        {displayedPercentage >= 70 ? (

          <p className="pass">
            🎉 Great job! You passed!
          </p>

        ) : (

          <p className="fail">
            Keep trying! You can retake the quiz.
          </p>

        )}

        {backendResult && (
          <p>
            ✓ Your result was saved to your learner profile.
          </p>
        )}

        {error && (
          <p style={{ color: 'red' }}>
            {error}
          </p>
        )}

        <button
          onClick={handleRetake}
          disabled={submitting}
        >
          Retake Quiz
        </button>

        <button
          onClick={() => router.push('/')}
          disabled={submitting}
        >
          Back to Modules
        </button>

      </div>
    )
  }

  // QUESTION SCREEN

  return (
    <div className="quiz">

      <h2>{module.title} &mdash; Quiz</h2>

      <p>
        Question {currentQ + 1} of {module.quiz.length}
      </p>

      <h3>{question.question}</h3>

      <div className="options">

        {question.options.map((opt, idx) => (

          <button
            key={idx}
            className={`option
              ${selected === idx ? 'selected' : ''}
              ${showFeedback && idx === question.answer ? 'correct' : ''}
              ${showFeedback && selected === idx && idx !== question.answer ? 'wrong' : ''}
            `}
            onClick={() => {
              if (!showFeedback) {
                setSelected(idx)
              }
            }}
            disabled={showFeedback}
          >
            {opt}
          </button>

        ))}

      </div>

      {!showFeedback ? (

        <button
          onClick={handleAnswer}
          disabled={selected === null}
        >
          Check Answer
        </button>

      ) : (

        <div>

          <p>
            {selected === question.answer
              ? '✓ Correct! Well done.'
              : '✗ Incorrect. The correct answer is highlighted in green.'}
          </p>

          <button
            onClick={handleNext}
            disabled={submitting}
          >
            {submitting
              ? 'Saving Quiz...'
              : currentQ === module.quiz.length - 1
                ? 'Finish Quiz'
                : 'Next Question'}
          </button>

        </div>

      )}

    </div>
  )
}

export default Quiz