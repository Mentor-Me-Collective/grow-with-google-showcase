import React, { useState, useEffect } from 'react'
import Head from 'next/head'
import Layout from '../components/Layout'
import ProfileSetup from '../components/ProfileSetup'
import { getProfile, getProgress } from '../utils/storage'
import '../styles/globals.css'

// ============================================
// _app.jsx — THE ROOT OF THE APP
// In Next.js, this file wraps EVERY page.
// It is like the "manager" that decides what to show.
// ============================================

function MyApp({ Component, pageProps }) {
  // State to hold the learner's profile and progress
  const [profile, setProfile] = useState(null)
  const [progress, setProgress] = useState(null)

  // useEffect with empty [] runs ONLY once when the app first loads.
  // It checks localStorage to see if the user already has a profile.
  useEffect(() => {
    const savedProfile = getProfile()
    const savedProgress = getProgress()
    if (savedProfile) setProfile(savedProfile)
    if (savedProgress) setProgress(savedProgress)
  }, [])

  const handleProfileCreated = (newProfile) => {
    setProfile(newProfile)
  }

  const handleProgressUpdate = () => {
    setProgress(getProgress())
  }

  // If there is NO profile yet, show the ProfileSetup screen ONLY.
  // This blocks access to everything else until a name is entered.
  if (!profile) {
    return (
      <>
        <Head>
          <title>Nova Digital Literacy Hub</title>
          <meta name="viewport" content="width=device-width, initial-scale=1" />
        </Head>
        <ProfileSetup onProfileCreated={handleProfileCreated} />
      </>
    )
  }

  // Once a profile exists, show the full app inside the Layout wrapper.
  // Component is whatever page the user is visiting (home, lesson, quiz, etc.)
  return (
    <>
      <Head>
        <title>Nova Digital Literacy Hub</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <Layout profile={profile}>
        <Component
          {...pageProps}
          progress={progress}
          onProgressUpdate={handleProgressUpdate}
        />
      </Layout>
    </>
  )
}

export default MyApp
