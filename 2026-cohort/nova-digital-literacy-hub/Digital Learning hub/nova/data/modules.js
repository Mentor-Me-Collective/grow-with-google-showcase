// ============================================
// MODULES DATA
// All learning content lives here.
// We use template literals (backticks) so long text
// never breaks across lines and causes syntax errors.
// Icons are emoji — they work offline with zero setup.
// ============================================

export const modules = [
  {
    id: "internet-basics",
    title: "Internet Basics",
    icon: "🌐",
    description: "Learn how the internet works and how to navigate it confidently.",
    lessons: [
      {
        id: 1,
        title: "What is the Internet?",
        icon: "🕸️",
        content: `The internet is a global network of millions of computers that talk to each other. It allows you to access websites, send messages, watch videos, and much more from anywhere in the world.`,
        steps: [
          `Think of the internet like a giant spiderweb connecting computers together.`,
          `When you open a website, your computer asks another computer for that page.`,
          `That other computer sends the page back through the web so you can see it.`,
        ],
      },
      {
        id: 2,
        title: "Using a Web Browser",
        icon: "🖥️",
        content: `A web browser is the program you use to visit websites. Common browsers include Google Chrome, Safari (on Apple devices), Microsoft Edge, and Mozilla Firefox.`,
        steps: [
          `Find the browser icon on your computer or phone and tap it to open.`,
          `Click the address bar at the top and type a website name (for example: google.com).`,
          `Press Enter. The website will load so you can read and interact with it.`,
          `Use the bookmark star to save a page so you can return later easily.`,
        ],
      },
      {
        id: 3,
        title: "Searching the Web",
        icon: "🔍",
        content: `Search engines like Google, Bing, or DuckDuckGo help you find information quickly. Instead of knowing exact website names, you can type what you are looking for.`,
        steps: [
          `Go to a search engine website (google.com is the most popular).`,
          `Click the search box and type keywords, for example: "how to make tea".`,
          `Press Enter and the search engine shows a list of relevant websites.`,
          `Read the short descriptions under each link to pick the best result.`,
        ],
      },
    ],
    quiz: [
      {
        question: "What is the internet?",
        options: ["A type of computer", "A global network of computers", "A web browser", "An email service"],
        answer: 1,
      },
      {
        question: "Which of these is a web browser?",
        options: ["Google Chrome", "Microsoft Word", "Windows", "Instagram"],
        answer: 0,
      },
      {
        question: "What do you use to find information on the web?",
        options: ["A calculator", "A search engine", "A printer", "A keyboard"],
        answer: 1,
      },
    ],
  },
  {
    id: "email-basics",
    title: "Email Basics",
    icon: "📧",
    description: "Learn how to create and use email to communicate safely and effectively.",
    lessons: [
      {
        id: 1,
        title: "What is Email?",
        icon: "✉️",
        content: `Email (short for electronic mail) is a way to send written messages and files over the internet. It is fast, free, and reaches anywhere in the world within seconds.`,
        steps: [
          `Every email address looks like this: name@example.com.`,
          `The part before @ is your username; the part after is the service (Gmail, Yahoo, etc.).`,
          `When you send an email, it travels through the internet to the recipient's inbox.`,
        ],
      },
      {
        id: 2,
        title: "Creating an Email Account",
        icon: "📝",
        content: `You can create a free email account with providers like Gmail, Yahoo Mail, or Outlook. You only need a phone number or another email for verification.`,
        steps: [
          `Open the provider's website (for example: gmail.com).`,
          `Click "Create account" and fill in your first name, last name, and desired email address.`,
          `Create a strong password and write it down somewhere safe.`,
          `Follow the verification steps (usually a code sent to your phone).`,
        ],
      },
      {
        id: 3,
        title: "Sending and Receiving Emails",
        icon: "📤",
        content: `Once your account is ready, you can send messages to friends, family, or businesses. You can also receive replies in your inbox.`,
        steps: [
          `Click the "Compose" or "New" button to start a new message.`,
          `Type the recipient's email address in the "To" field.`,
          `Add a short, clear subject so the reader knows what the email is about.`,
          `Write your message in the big box, then click "Send".`,
        ],
      },
    ],
    quiz: [
      {
        question: "What does email stand for?",
        options: ["Electric mail", "Electronic mail", "Easy mail", "Every mail"],
        answer: 1,
      },
      {
        question: "Which symbol is in every email address?",
        options: ["#", "$", "@", "&"],
        answer: 2,
      },
      {
        question: "What button do you click to write a new email?",
        options: ["Reply", "Compose", "Forward", "Delete"],
        answer: 1,
      },
    ],
  },
  {
    id: "online-safety",
    title: "Online Safety",
    icon: "🔒",
    description: "Learn how to stay safe, protect your information, and avoid scams online.",
    lessons: [
      {
        id: 1,
        title: "Creating Strong Passwords",
        icon: "🔑",
        content: `A strong password is your first line of defense. Weak passwords are easy for hackers to guess.`,
        steps: [
          `Use at least 8 characters (12 is even better).`,
          `Mix uppercase letters, lowercase letters, numbers, and symbols like ! or #.`,
          `Avoid using your name, birthday, or common words like "password" or "123456".`,
          `Consider using a passphrase: four random words joined together, like "Blue-Tiger-7-Sings!".`,
        ],
      },
      {
        id: 2,
        title: "Recognizing Scams",
        icon: "⚠️",
        content: `Scams are tricks criminals use to steal your money or personal information. They often come through email, text, or fake websites.`,
        steps: [
          `Check the sender's email address carefully. Scammers often use addresses that look almost real.`,
          `Be suspicious of urgent messages: "Your account will be closed today!"`,
          `Never click links or download attachments from unknown senders.`,
          `When in doubt, contact the company directly using a phone number you trust.`,
        ],
      },
      {
        id: 3,
        title: "Protecting Personal Information",
        icon: "🛡️",
        content: `Personal information includes your full name, address, phone number, ID numbers, and photos. Once shared online, it can be hard to remove.`,
        steps: [
          `Review privacy settings on social media so only friends can see your posts.`,
          `Think before you post: would you be comfortable if a stranger saw this?`,
          `Always log out of your accounts when using a shared or public computer.`,
          `Keep your devices updated; updates often include security fixes.`,
        ],
      },
    ],
    quiz: [
      {
        question: "What makes a password strong?",
        options: ["Using your name", "Using 8+ mixed characters", `Using "password"`, "Using only numbers"],
        answer: 1,
      },
      {
        question: "What should you do with suspicious links?",
        options: ["Click them immediately", "Share with friends", "Avoid clicking them", "Forward them"],
        answer: 2,
      },
      {
        question: "Why should you log out on shared devices?",
        options: ["To save battery", "To protect your information", "To make it faster", "It is not necessary"],
        answer: 1,
      },
    ],
  },
]
