import React from 'react'
import LessonViewer from '../../../../components/LessonViewer'

// ============================================
// LESSON PAGE (Dynamic Route)
// The file path creates the URL pattern:
// /module/internet-basics/lesson/1
// /module/email-basics/lesson/2
// etc.
// ============================================

export default function LessonPage({ onProgressUpdate }) {
  return <LessonViewer onProgressUpdate={onProgressUpdate} />
}
