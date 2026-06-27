import React, { useState } from 'react';
import { 
  Server, Database, Bot, Terminal, Code, LayoutDashboard, 
  Smartphone, Activity, Globe, HeartHandshake, FileText, Info
} from 'lucide-react';
import { pythonFiles } from './data/pythonFiles';
import ArchitectureView from './components/ArchitectureView';
import CodeExplorer from './components/CodeExplorer';
import Playground from './components/Playground';
import TicketMonitor from './components/TicketMonitor';

export default function App() {
  const [currentTab, setCurrentTab] = useState<'architecture' | 'code' | 'playground' | 'monitor'>('playground');

  return (
    <div className="min-h-screen bg-slate-50/50 text-gray-800 font-sans antialiased flex flex-col selection:bg-indigo-100 selection:text-indigo-900">
      
      {/* 1. BRANDING & STATUS TOP HEADER */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-40 shadow-xs shrink-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          
          {/* Brand Logo & Name */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-slate-900 text-white flex items-center justify-center font-bold tracking-tight shadow-sm shrink-0">
              BF
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-black text-gray-900 tracking-tight">BiteFixes</h1>
                <span className="px-2 py-0.5 text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-100 rounded-md font-mono">
                  DEV HUB
                </span>
              </div>
              <p className="text-xs text-gray-400 font-medium">Arquitectura Backend Omnicanal & Sandbox Interactiva</p>
            </div>
          </div>

          {/* Micro Status Indicators (Minimal, elegant architectural telemetry) */}
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs bg-slate-50 border border-slate-100 px-3 py-1.5 rounded-xl font-mono shrink-0">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-gray-500 font-medium">FastAPI:</span>
              <span className="text-gray-800 font-semibold">Online</span>
            </div>
            <div className="hidden sm:block w-px h-3.5 bg-gray-200"></div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span className="text-gray-500 font-medium">Supabase DB:</span>
              <span className="text-gray-800 font-semibold">Conectado</span>
            </div>
            <div className="hidden sm:block w-px h-3.5 bg-gray-200"></div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span className="text-gray-500 font-medium">Gemini Agent:</span>
              <span className="text-gray-800 font-semibold">Activo</span>
            </div>
          </div>

        </div>
      </header>

      {/* 2. NAVIGATION BAR */}
      <nav className="bg-white border-b border-gray-100 shadow-2xs shrink-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-1 py-1">
            {/* Tab 1: Playground */}
            <button
              id="tab-playground"
              onClick={() => setCurrentTab('playground')}
              className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
                currentTab === 'playground'
                  ? 'border-slate-900 text-slate-900 font-extrabold'
                  : 'border-transparent text-gray-500 hover:text-gray-950 hover:bg-slate-50/50'
              }`}
            >
              <Terminal className="w-4 h-4 text-indigo-600" />
              <span>🎮 Sandbox Interactiva</span>
            </button>

            {/* Tab 2: Code Explorer */}
            <button
              id="tab-code"
              onClick={() => setCurrentTab('code')}
              className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
                currentTab === 'code'
                  ? 'border-slate-900 text-slate-900 font-extrabold'
                  : 'border-transparent text-gray-500 hover:text-gray-950 hover:bg-slate-50/50'
              }`}
            >
              <Code className="w-4 h-4 text-sky-500" />
              <span>💻 Código Fuente (Python)</span>
            </button>

            {/* Tab 3: Architecture Diagram */}
            <button
              id="tab-architecture"
              onClick={() => setCurrentTab('architecture')}
              className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
                currentTab === 'architecture'
                  ? 'border-slate-900 text-slate-900 font-extrabold'
                  : 'border-transparent text-gray-500 hover:text-gray-950 hover:bg-slate-50/50'
              }`}
            >
              <Server className="w-4 h-4 text-emerald-500" />
              <span>🏗️ Plano de Arquitectura</span>
            </button>

            {/* Tab 4: Ticket Dashboard */}
            <button
              id="tab-monitor"
              onClick={() => setCurrentTab('monitor')}
              className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
                currentTab === 'monitor'
                  ? 'border-slate-900 text-slate-900 font-extrabold'
                  : 'border-transparent text-gray-500 hover:text-gray-950 hover:bg-slate-50/50'
              }`}
            >
              <LayoutDashboard className="w-4 h-4 text-pink-500" />
              <span>📊 Monitor de Soporte</span>
            </button>
          </div>
        </div>
      </nav>

      {/* 3. MAIN DASHBOARD STAGE */}
      <main className="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col">
        
        {/* Active tab rendering */}
        <div className="flex-grow flex flex-col">
          {currentTab === 'architecture' && <ArchitectureView />}
          {currentTab === 'code' && <CodeExplorer files={pythonFiles} />}
          {currentTab === 'playground' && <Playground />}
          {currentTab === 'monitor' && <TicketMonitor />}
        </div>

      </main>

      {/* 4. FOOTER */}
      <footer className="bg-white border-t border-gray-100 py-6 mt-12 shrink-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-gray-400">
          <div className="flex items-center gap-2 font-medium">
            <span>© 2026 BiteFixes Inc. Todos los derechos reservados.</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="font-semibold text-slate-500">FastAPI + Supabase + Google Gen AI SDK</span>
            <span className="text-slate-300">|</span>
            <span>Diseño de Grado de Producción por Arquitecto de Software Senior</span>
          </div>
        </div>
      </footer>

    </div>
  );
}
