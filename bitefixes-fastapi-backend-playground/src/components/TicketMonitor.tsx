import React from 'react';
import { LayoutDashboard, CheckCircle, Clock, FileText, AlertCircle, HardDrive, Cpu, Wifi, Briefcase, HelpCircle } from 'lucide-react';
import { TicketRecord } from '../types';

interface TicketMonitorProps {
  tickets: TicketRecord[];
}

export default function TicketMonitor() {
  // Static state data mirroring our live tables
  const mockTickets = [
    { id: '1001', created_at: '2026-06-26T10:00:00Z', categoria: 'Hardware', owner: 'Carlos Mendoza', descripcion: 'Mi computadora portátil enciende pero la pantalla se queda completamente en negro.', estatus: 'Abierto' },
    { id: '1002', created_at: '2026-06-27T06:15:00Z', categoria: 'Redes', owner: 'María Fernández', descripcion: 'El enrutador de oficina pierde conexión intermitentemente cada tarde a las 3 PM.', estatus: 'En Proceso' },
    { id: '1003', created_at: '2026-06-27T10:20:00Z', categoria: 'Software', owner: 'Juan Gómez', descripcion: 'Se requiere formateo urgente e instalación de suite de diseño corporativo.', estatus: 'Abierto' },
    { id: '1004', created_at: '2026-06-27T10:25:00Z', categoria: 'Comercial', owner: 'Distribuidora S.A.', descripcion: 'Solicitud de cotización formal para plan de mantenimiento anual de 15 puestos.', estatus: 'Resuelto' }
  ];

  // Calculations
  const total = mockTickets.length;
  const abiertos = mockTickets.filter(t => t.estatus === 'Abierto').length;
  const proceso = mockTickets.filter(t => t.estatus === 'En Proceso').length;
  const resueltos = mockTickets.filter(t => t.estatus === 'Resuelto').length;

  const categories = ['Hardware', 'Software', 'Redes', 'Comercial', 'Otro'];
  const catDistribution = categories.map(cat => ({
    name: cat,
    count: mockTickets.filter(t => t.categoria === cat).length
  }));

  const getCategoryIcon = (cat: string) => {
    switch (cat) {
      case 'Hardware': return <Cpu className="w-3.5 h-3.5 text-orange-500" />;
      case 'Software': return <HardDrive className="w-3.5 h-3.5 text-indigo-500" />;
      case 'Redes': return <Wifi className="w-3.5 h-3.5 text-sky-500" />;
      case 'Comercial': return <Briefcase className="w-3.5 h-3.5 text-teal-500" />;
      default: return <HelpCircle className="w-3.5 h-3.5 text-slate-500" />;
    }
  };

  return (
    <div className="space-y-6 animate-fade-in" id="ticket-monitor">
      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Tickets */}
        <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Total Tickets</span>
            <div className="text-2xl font-black text-gray-900 mt-1">{total}</div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center text-slate-600">
            <FileText className="w-5 h-5" />
          </div>
        </div>

        {/* Abiertos */}
        <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Abiertos</span>
            <div className="text-2xl font-black text-emerald-600 mt-1">{abiertos}</div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600">
            <AlertCircle className="w-5 h-5" />
          </div>
        </div>

        {/* En Proceso */}
        <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">En Proceso</span>
            <div className="text-2xl font-black text-amber-500 mt-1">{proceso}</div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center text-amber-500">
            <Clock className="w-5 h-5" />
          </div>
        </div>

        {/* Resueltos */}
        <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Resueltos</span>
            <div className="text-2xl font-black text-gray-500 mt-1">{resueltos}</div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center text-slate-500">
            <CheckCircle className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Main Stats Block */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Category breakdown visualizer */}
        <div className="lg:col-span-4 bg-white rounded-2xl border border-gray-100 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-gray-900 text-sm tracking-tight flex items-center gap-1.5 mb-1">
              <LayoutDashboard className="w-4 h-4 text-indigo-600" />
              Distribución por Categoría
            </h3>
            <p className="text-[10px] text-gray-400 leading-normal">Mapeo automático de reportes levantados por el chatbot.</p>
          </div>

          <div className="space-y-3.5 mt-5 flex-grow">
            {catDistribution.map((cat, idx) => {
              const percentage = total > 0 ? (cat.count / total) * 100 : 0;
              return (
                <div key={idx} className="space-y-1">
                  <div className="flex items-center justify-between text-xs text-gray-600 font-medium">
                    <span className="flex items-center gap-1.5">
                      {getCategoryIcon(cat.name)}
                      {cat.name}
                    </span>
                    <span className="font-mono text-[11px] text-gray-400">{cat.count} ({Math.round(percentage)}%)</span>
                  </div>
                  {/* Custom Progress bar */}
                  <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full transition-all duration-500 ${
                        cat.name === 'Hardware' ? 'bg-orange-500' :
                        cat.name === 'Software' ? 'bg-indigo-500' :
                        cat.name === 'Redes' ? 'bg-sky-500' :
                        cat.name === 'Comercial' ? 'bg-teal-500' : 'bg-slate-400'
                      }`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Live Admin ticket feed */}
        <div className="lg:col-span-8 bg-white rounded-2xl border border-gray-100 p-5 shadow-xs flex flex-col">
          <h3 className="font-bold text-gray-900 text-sm tracking-tight mb-3">
            Últimos Tickets de Soporte
          </h3>
          
          <div className="divide-y divide-gray-100 overflow-auto max-h-[280px]">
            {mockTickets.map((ticket) => {
              const catColors: Record<string, string> = {
                Hardware: 'bg-orange-50 text-orange-700 border-orange-100',
                Software: 'bg-indigo-50 text-indigo-700 border-indigo-100',
                Redes: 'bg-sky-50 text-sky-700 border-sky-100',
                Comercial: 'bg-teal-50 text-teal-700 border-teal-100',
                Otro: 'bg-slate-50 text-slate-700 border-slate-100'
              };

              const statusColors: Record<string, string> = {
                Abierto: 'bg-emerald-50 text-emerald-700 border-emerald-100',
                'En Proceso': 'bg-amber-50 text-amber-700 border-amber-100',
                Resuelto: 'bg-slate-100 text-slate-700 border-slate-200'
              };

              return (
                <div key={ticket.id} className="py-3 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 first:pt-0 last:pb-0">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-gray-900">#{ticket.id}</span>
                      <span className="text-xs text-gray-500">• {ticket.owner}</span>
                      <span className={`px-2 py-0.2 text-[9px] font-semibold rounded border ${catColors[ticket.categoria]}`}>
                        {ticket.categoria}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 line-clamp-1 max-w-lg">
                      {ticket.descripcion}
                    </p>
                  </div>

                  <span className={`px-2 py-0.5 text-[10px] font-semibold rounded-md border shrink-0 ${statusColors[ticket.estatus]}`}>
                    {ticket.estatus}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
