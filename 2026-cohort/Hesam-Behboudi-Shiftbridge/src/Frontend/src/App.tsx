import { useState, useEffect, useRef, useCallback } from 'react';
import type { Worker, ShiftInfo, ProposalType } from './types';
import { api } from './services/api';
import { AuthCard } from './components/AuthCard';
import { Header } from './components/Header';
import { SidebarChat } from './components/SidebarChat';
import { CalendarGrid } from './components/CalendarGrid';

export default function App() {
  // Navigation: '/login' vs '/dashboard'
  const [currentPage, setCurrentPage] = useState<'login' | 'dashboard'>(() => {
    return window.location.pathname === '/login' ? 'login' : 'dashboard';
  });

  // Current session user and role
  const [currentRole, setCurrentRole] = useState<'worker' | 'manager'>('worker');
  const [currentUser, setCurrentUser] = useState<Worker | null>(null); // Sarah Jenkins

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('jwt');
      if (!token) {
        navigateTo('login');
        return;
      }

      try {
        const user = await api.getMe(token);
        setCurrentUser(user);
        setCurrentRole(user.id.startsWith('m') ? 'manager' : 'worker'); // Simple logic for demo
        navigateTo('dashboard');
      } catch (error) {
        localStorage.removeItem('jwt');
        navigateTo('login');
      }
    };
    checkAuth();
  }, []);

  // Core Schedule State
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [schedule, setSchedule] = useState<ShiftInfo[]>([]);

  useEffect(() => {
    if (currentPage !== 'dashboard') return;
    const fetchData = async () => {
      try {
        const [fetchedWorkers, fetchedSchedule, fetchedProposals] = await Promise.all([
          api.getWorkers(),
          api.getSchedule(),
          api.getProposals(),
        ]);
        setWorkers(fetchedWorkers);
        setSchedule(fetchedSchedule);
        setAiProposals(fetchedProposals);
      } catch (error) {
        console.error('Failed to fetch initial data:', error);
      }
    };
    if (localStorage.getItem('jwt'))
      fetchData();
  }, [currentPage]);

  const [appliedProposalTitle, setAppliedProposalTitle] = useState<string | null>(null);
  const [approvalStatus, setApprovalStatus] = useState<{
    workerApproved: boolean;
    managerApproved: boolean;
    applied: boolean;
    selectedOption: 'opt_A' | 'opt_B' | null;
  }>({
    workerApproved: false,
    managerApproved: false,
    applied: false,
    selectedOption: null
  });
  const [aiProposals, setAiProposals] = useState<ProposalType[]>([]);

  // Resizable Chat Section State (Task 3)
  const [chatWidth, setChatWidth] = useState<number>(440);
  const isDraggingRef = useRef(false);

  const startResizing = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isDraggingRef.current = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    const handleMouseMove = (moveEvent: MouseEvent) => {
      if (!isDraggingRef.current) return;
      // Clamp chat width between 300px and 750px, also considering window width
      const maxWidth = Math.min(800, window.innerWidth - 450);
      const newWidth = Math.max(300, Math.min(maxWidth, moveEvent.clientX));
      setChatWidth(newWidth);
    };

    const handleMouseUp = () => {
      isDraggingRef.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  }, []);

  // Keep browser history and URL in sync with state
  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname;
      if (path === '/login') {
        setCurrentPage('login');
      } else {
        setCurrentPage('dashboard');
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigateTo = (page: 'login' | 'dashboard') => {
    setCurrentPage(page);
    window.history.pushState({}, '', page === 'login' ? '/login' : '/dashboard');
  };

  const handleLogin = async (token: string) => {
    localStorage.setItem('jwt', token);

    const user = await api.getMe(token)
    setCurrentRole(user.id.startsWith('m') ? 'manager' : 'worker');
    console.error(user)
    setCurrentUser(user);
    navigateTo('dashboard');
  };

  const handleLogout = () => {
    localStorage.removeItem('jwt');
    navigateTo('login');
  };

  const handleSwitchRole = () => {
    if (currentRole === 'worker') {
      setCurrentRole('manager');
      // Default to Marcus Vance for manager
      const managerUser = workers.find((w) => w.id === 'w4') || workers[0];
      setCurrentUser(managerUser);
    } else {
      setCurrentRole('worker');
      // Default back to Sarah Jenkins for worker
      const workerUser = workers.find((w) => w.id === 'w1') || workers[0];
      setCurrentUser(workerUser);
    }
  };

  // Reset all scenario states
  const handleResetData = async () => {
    try {
      const [fetchedWorkers, fetchedSchedule] = await Promise.all([
        api.getWorkers(),
        api.getSchedule(),
      ]);
      setWorkers(fetchedWorkers);
      setSchedule(fetchedSchedule);
      setAppliedProposalTitle(null);
      setApprovalStatus({
        workerApproved: false,
        managerApproved: false,
        applied: false,
        selectedOption: null
      });
    } catch (error) {
      console.error('Failed to reset data:', error);
    }
  };

  if (currentPage === 'login') {
    return <AuthCard onLogin={handleLogin} />;
  }

  if (!currentUser) {
    return null; // Or a loading spinner
  }

  return (
    <div className="min-h-screen h-[100vh] flex flex-col bg-slate-50 text-slate-900 font-sans">
      <Header
        currentUser={currentUser}
        currentRole={currentRole}
        onSwitchRole={handleSwitchRole}
        onLogout={handleLogout}
        onResetData={handleResetData}
        isResolved={approvalStatus.applied}
      />

      <main className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        <div
          style={{ width: typeof window !== 'undefined' && window.innerWidth >= 1024 ? `${chatWidth}px` : undefined }}

          data-testid="sidebar-chat-container"
        >
          <SidebarChat
            key={aiProposals.length}
            currentUser={currentUser}
            setSchedule={setSchedule}
            currentRole={currentRole}
            aiProposals={aiProposals}
            onResetChat={handleResetData}
          />
        </div>

        {/* Resizer Handle (Desktop only) */}
        <div
          onMouseDown={startResizing}
          data-testid="chat-resizer"
          role="separator"
          aria-orientation="vertical"
          tabIndex={0}
          title="Drag to resize chat panel"
          className="hidden lg:flex w-2 hover:w-2.5 bg-slate-200/80 hover:bg-indigo-400 active:bg-indigo-600 transition-all cursor-col-resize items-center justify-center shrink-0 z-20 group select-none"
        >
          <div className="w-0.5 h-8 bg-slate-400 group-hover:bg-white rounded-full transition-colors" />
        </div>

        {/* Right Section: Interactive 7-Day Calendar & Shift Grid */}
        <div className="flex-1 h-full min-w-0">
          <CalendarGrid
            workers={workers}
            schedule={schedule}
            appliedProposalTitle={appliedProposalTitle}
            currentUser={currentUser}
            currentRole={currentRole}
          />
        </div>
      </main>
    </div>
  );
}
