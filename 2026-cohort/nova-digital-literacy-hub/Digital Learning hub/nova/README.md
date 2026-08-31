# Nova Digital Literacy Hub — Next.js Frontend

A beginner-friendly Next.js frontend for the Nova Architects digital literacy platform.

## What This App Does

- Lets learners create a simple local profile (name + optional PIN).
- Displays 3 learning modules: **Internet Basics**, **Email Basics**, **Online Safety**.
- Each module has 3 step-by-step lessons.
- Each module ends with a multiple-choice quiz (immediate feedback, retakes allowed).
- Tracks progress locally in the browser (works offline after first load).
- Shows a progress dashboard and a completion badge when all modules are done.

## Tech Stack

- **Next.js** — React framework (handles routing, building, and serving)
- **React** — UI library
- **localStorage** — saves data on the user's device (no backend needed for MVP)

## How to Run (Step by Step)

### 1. Install Node.js
Download and install from [https://nodejs.org](https://nodejs.org) (choose the **LTS** version).

### 2. Unzip the project
Extract the downloaded zip file into a folder on your computer (e.g., Desktop).

### 3. Open a terminal
- **Windows:** Press `Win + R`, type `cmd`, press Enter.
- **Mac:** Press `Cmd + Space`, type `Terminal`, press Enter.

### 4. Navigate to the project folder
```bash
cd Desktop/nova-digital-literacy-nextjs
```
(Replace `Desktop` with wherever you put the folder.)

### 5. Install dependencies
```bash
npm install
```
This downloads Next.js, React, and everything else automatically.

### 6. Start the development server
```bash
npm run dev
```
Next.js will print a local URL (usually `http://localhost:3000`).
Open that URL in your browser to see the app.

### 7. Build for production (when ready to deploy)
```bash
npm run build
```
This creates a production-ready build. You can then deploy to **Vercel** (the company that makes Next.js) for free.

## Project Folder Structure

```
nova-digital-literacy-nextjs/
├── package.json              # Lists dependencies
├── next.config.js            # Next.js settings
├── README.md                 # This file
├── public/                   # Static files (images, etc.)
├── styles/
│   └── globals.css           # All styling
├── data/
│   └── modules.js            # All lesson & quiz content
├── utils/
│   └── storage.js            # localStorage helpers
├── components/
│   ├── Layout.jsx            # Header, nav, footer
│   ├── ProfileSetup.jsx      # First-time profile screen
│   ├── ModuleList.jsx        # Home page with module cards
│   ├── LessonViewer.jsx      # Reads one lesson
│   ├── Quiz.jsx              # Interactive quiz
│   ├── Dashboard.jsx         # Progress overview
│   └── Badge.jsx             # Completion celebration
└── pages/
    ├── _app.jsx              # Root wrapper (profile check + layout)
    ├── index.jsx             # Home page (/)
    ├── dashboard.jsx         # Dashboard page (/dashboard)
    ├── badge.jsx             # Badge page (/badge)
    └── module/
        └── [moduleId]/
            ├── quiz.jsx      # Quiz page (/module/xxx/quiz)
            └── lesson/
                └── [lessonId].jsx  # Lesson page (/module/xxx/lesson/1)
```

## How Next.js Routing Works (Simple Explanation)

In Next.js **Pages Router**, the folder structure inside `pages/` **IS** the URL structure:

| File Path | URL in Browser |
|---|---|
| `pages/index.jsx` | `/` |
| `pages/dashboard.jsx` | `/dashboard` |
| `pages/badge.jsx` | `/badge` |
| `pages/module/[moduleId]/quiz.jsx` | `/module/internet-basics/quiz` |
| `pages/module/[moduleId]/lesson/[lessonId].jsx` | `/module/internet-basics/lesson/1` |

The square brackets `[moduleId]` mean "this part of the URL can be anything." Next.js passes that value to your component through `router.query`.

## How to Customize Content

All learning material lives in `data/modules.js`.
You can edit the text, add more lessons, or add more modules without touching any other file.

## How to Customize Colors

All colors are defined at the top of `styles/globals.css`.
Look for lines like `background-color: #1a5f7a;` and change the hex code to your preferred color.

## Tips for Beginners

- If you see an error in the terminal, try stopping the server (`Ctrl + C`) and running `npm run dev` again.
- Changes you make to the code will appear instantly in the browser while `npm run dev` is running.
- If you want to reset your progress, open the browser's Developer Tools (F12), go to the **Application** tab, click **Local Storage**, and delete the `nova_profile` and `nova_progress` keys.
- If `npm install` fails with permission errors, try running your terminal as Administrator (Windows) or use `sudo` (Mac/Linux).

## Connecting to Your FastAPI Backend Later

Right now, the app is **frontend-only** and uses `localStorage`. When your team is ready to connect the FastAPI backend:

1. Replace the functions in `utils/storage.js` with **API calls** (using `fetch`) to your FastAPI endpoints:
   - `POST /profile` → instead of `saveProfile`
   - `GET /modules` → instead of importing from `modules.js`
   - `POST /quiz` → instead of saving quiz scores locally
   - `GET /progress` → instead of reading from `localStorage`

2. The components (`LessonViewer`, `Quiz`, `Dashboard`) do not need to change much — only the `storage.js` file acts as the "bridge."
