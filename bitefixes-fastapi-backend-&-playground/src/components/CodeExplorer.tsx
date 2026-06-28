import React, { useState } from 'react';
import { FileText, Copy, Check, Download, FileCode, Server, Settings, Database, Info } from 'lucide-react';
import { PythonFile } from '../types';

interface CodeExplorerProps {
  files: PythonFile[];
}

export default function CodeExplorer({ files }: CodeExplorerProps) {
  const [selectedFile, setSelectedFile] = useState<PythonFile>(files[0]);
  const [copied, setCopied] = useState<boolean>(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(selectedFile.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const element = document.createElement("a");
    const file = new Blob([selectedFile.content], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = selectedFile.name;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const getFileIcon = (fileName: string) => {
    if (fileName.endsWith('.py')) return <FileCode className="w-4 h-4 text-sky-500" />;
    if (fileName.endsWith('.sql')) return <Database className="w-4 h-4 text-teal-500" />;
    if (fileName.endsWith('.env.example')) return <Settings className="w-4 h-4 text-amber-500" />;
    if (fileName === 'requirements.txt') return <FileText className="w-4 h-4 text-purple-500" />;
    return <FileText className="w-4 h-4 text-slate-500" />;
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-fade-in" id="code-explorer">
      {/* File Tree Sidebar */}
      <div className="lg:col-span-3 bg-white rounded-2xl border border-gray-100 p-4 shadow-xs h-fit">
        <h3 className="font-bold text-gray-900 text-sm px-2 mb-3 tracking-tight">Estructura del Proyecto</h3>
        <nav className="space-y-1">
          {files.map((file) => {
            const isSelected = selectedFile.name === file.name;
            return (
              <button
                key={file.name}
                onClick={() => setSelectedFile(file)}
                className={`w-full flex items-center gap-2.5 px-3 py-2 text-xs rounded-xl font-medium transition-all text-left ${
                  isSelected
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'text-gray-600 hover:bg-slate-50 hover:text-gray-900'
                }`}
              >
                {getFileIcon(file.name)}
                <div className="truncate">
                  <div className="font-mono">{file.name}</div>
                  <div className={`text-[10px] truncate ${isSelected ? 'text-slate-400' : 'text-gray-400'}`}>
                    {file.path}
                  </div>
                </div>
              </button>
            );
          })}
        </nav>
        
        <div className="mt-6 p-3 bg-slate-50 border border-slate-100 rounded-xl">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
            <Info className="w-3.5 h-3.5 text-slate-500" />
            <span>Nota del Arquitecto</span>
          </div>
          <p className="text-[10px] text-slate-500 mt-1.5 leading-relaxed">
            Todos los módulos han sido estructurados conforme a los estándares oficiales de producción de FastAPI y Google Gen AI SDK.
          </p>
        </div>
      </div>

      {/* Code Viewer Panel */}
      <div className="lg:col-span-9 flex flex-col bg-white rounded-2xl border border-gray-100 shadow-xs overflow-hidden">
        {/* File Header Details */}
        <div className="px-6 py-4 border-b border-gray-100 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-slate-700 bg-slate-200/60 px-2 py-0.5 rounded">
                {selectedFile.path}
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1.5 leading-relaxed max-w-2xl">
              {selectedFile.description}
            </p>
          </div>
          
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 active:bg-gray-100 rounded-lg transition-all shadow-xs"
              title="Copiar código al portapapeles"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600 animate-scale-up" />
                  <span className="text-emerald-600">¡Copiado!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copiar</span>
                </>
              )}
            </button>
            
            <button
              onClick={handleDownload}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white rounded-lg transition-all shadow-xs"
              title="Descargar archivo físico"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Descargar</span>
            </button>
          </div>
        </div>

        {/* Code Block Container */}
        <div className="relative flex-grow font-mono text-xs overflow-auto max-h-[550px] bg-slate-950 text-slate-100">
          <div className="flex min-w-full">
            {/* Line numbers column */}
            <div className="select-none text-right px-4 py-4 bg-slate-900 border-r border-slate-800/80 text-slate-600 text-xs shrink-0 font-mono text-right w-12">
              {selectedFile.content.split('\n').map((_, i) => (
                <div key={i} className="leading-5 h-5">{i + 1}</div>
              ))}
            </div>
            
            {/* Raw code column */}
            <pre className="p-4 flex-grow overflow-x-auto text-slate-200 leading-5 font-mono select-text whitespace-pre">
              <code>{selectedFile.content}</code>
            </pre>
          </div>
        </div>
        
        {/* Footer info bar */}
        <div className="px-6 py-2.5 bg-slate-900 border-t border-slate-800 flex justify-between items-center text-[10px] text-slate-400 font-mono">
          <span>{selectedFile.content.split('\n').length} líneas</span>
          <span>Formato: UTF-8 • {selectedFile.language.toUpperCase()}</span>
        </div>
      </div>
    </div>
  );
}
