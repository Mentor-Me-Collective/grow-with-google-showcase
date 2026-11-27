import React from 'react';
import { Calendar, Shield, User, LogOut } from 'lucide-react';
import type { Worker } from '../types';

interface HeaderProps {
  currentUser: Worker;
  currentRole: 'worker' | 'manager';
  onSwitchRole: () => void;
  onLogout: () => void;
  onResetData: () => void;
  isResolved: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentUser,
  currentRole,
  onLogout,
}) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo & Tag */}
          <div className="flex items-center gap-3">
            <div className="p-2 bg-linear-to-tr from-indigo-600 to-violet-600 rounded-xl text-white shadow-sm shadow-indigo-500/20">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-lg text-slate-900 tracking-tight">ShiftBridge</span>
              </div>
            </div>
          </div>

          {/* Right Controls: Role Badge, Role Switcher, Reset, Logout */}
          <div className="flex items-center gap-3 sm:gap-4">
            {/* User Profile Capsule */}
            <div className="flex items-center gap-2.5 bg-slate-50 border border-slate-200/80 px-2.5 py-1.5 rounded-xl">
              <img
                src={currentUser.avatar}
                alt={currentUser.name}
                className="w-7 h-7 rounded-full object-cover border border-slate-300"
              />
              <div className="text-left text-xs leading-tight">
                <div className="font-semibold text-slate-900 flex items-center gap-1">
                  {currentUser.name}
                  {currentRole === 'manager' ? (
                    <span className="inline-flex items-center text-[10px] font-bold px-1.5 py-0.2 rounded bg-purple-100 text-purple-800">
                      <Shield className="w-2.5 h-2.5 mr-0.5" /> Manager
                    </span>
                  ) : (
                    <span className="inline-flex items-center text-[10px] font-bold px-1.5 py-0.2 rounded bg-blue-100 text-blue-800">
                      <User className="w-2.5 h-2.5 mr-0.5" /> Worker
                    </span>
                  )}
                </div>
                <div className="text-[11px] text-slate-500 truncate max-w-30">{currentUser.role}</div>
              </div>
            </div>

            {/* Logout */}
            <button
              onClick={onLogout}
              title="Exit to login screen"
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
