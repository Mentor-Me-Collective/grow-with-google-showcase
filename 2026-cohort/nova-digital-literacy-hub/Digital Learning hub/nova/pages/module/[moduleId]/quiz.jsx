import React from 'react'
import Quiz from '../../../components/Quiz'

// ============================================
// QUIZ PAGE (Dynamic Route)
// The file path creates the URL pattern:
// /module/internet-basics/quiz
// /module/email-basics/quiz
// etc.
// ============================================

export default function QuizPage({ onProgressUpdate }) {
  return <Quiz onProgressUpdate={onProgressUpdate} />
}
