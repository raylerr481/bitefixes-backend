import React, { useState } from 'react';
import { Server, Database, Bot, Smartphone, Globe, ArrowRight, Webhook, Shield, CheckCircle } from 'lucide-react';

export default function ArchitectureView() {
  const [activeNode, setActiveNode] = useState<string | null>(null);

  const nodes = [
    {
      id: 'clients',
      title: 'Canales de Cliente (Omnicanal)',
      description: 'Los puntos de contacto del usuario. WhatsApp Business (Meta Cloud API), el Chat Widget de la Web y la App Móvil envían y reciben mensajes en tiempo real.',
      icon: Smartphone,
      color: 'bg-indigo-50 border-indigo-200 text-indigo-700 dark:bg-indigo-950/20 dark:border-indigo-900 dark:text-indigo-400',
    },
    {
      id: 'fastapi',
      title: 'FastAPI Gateway (Servidor Python)',
      description: 'El núcleo de enrutamiento. Valida webhooks de Meta, maneja sesiones de chat asíncronas de manera ultra eficiente, expone endpoints REST públicos y ejecuta la lógica de negocio.',
      icon: Server,
      color: 'bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-950/20 dark:border-emerald-900 dark:text-emerald-400',
    },
    {
      id: 'gemini',
      title: 'Agente Gemini 3.5 (Google Gen AI)',
      description: 'El "cerebro" conversacional. Ejecuta Function Calling nativo con baja latencia para determinar si el usuario es cliente, solicitar datos que falten o levantar un ticket.',
      icon: Bot,
      color: 'bg-sky-50 border-sky-200 text-sky-700 dark:bg-sky-950/20 dark:border-sky-900 dark:text-sky-400',
    },
    {
      id: 'supabase',
      title: 'Supabase / PostgreSQL',
      description: 'Capa de persistencia robusta. Tablas estructuradas de "clientes" y "tickets". Proporciona escalabilidad SQL, respaldos en la nube, RLS (Row Level Security) e índices de consulta rápidos.',
      icon: Database,
      color: 'bg-teal-50 border-teal-200 text-teal-700 dark:bg-teal-950/20 dark:border-teal-900 dark:text-teal-400',
    }
  ];

  const interactions = [
    {
      title: '1. Webhook de Entrada',
      desc: 'Meta reenvía el mensaje del usuario por HTTP POST al webhook de FastAPI.'
    },
    {
      title: '2. Carga de Historial y Prompt',
      desc: 'FastAPI recupera el chat previo del usuario e inicializa el agente de Gemini.'
    },
    {
      title: '3. Evaluación de Herramientas',
      desc: 'Gemini analiza el mensaje y, si requiere validar o guardar datos, emite una llamada a función (Function Call).'
    },
    {
      title: '4. Ejecución en Supabase',
      desc: 'FastAPI intercepta la llamada, realiza la consulta segura SQL en Supabase, y le devuelve el resultado estructurado a Gemini.'
    },
    {
      title: '5. Respuesta Conclusiva',
      desc: 'Gemini redacta la respuesta final con empatía y FastAPI la remite a WhatsApp mediante Meta Graph API.'
    }
  ];

  return (
    <div className="space-y-8 animate-fade-in" id="architecture-view">
      <div className="bg-white rounded-2xl border border-gray-100 p-6 md:p-8 shadow-xs">
        <div className="max-w-3xl">
          <span className="px-3 py-1 text-xs font-semibold text-indigo-600 bg-indigo-50 rounded-full">Diseño de Producción</span>
          <h2 className="text-2xl font-bold text-gray-900 mt-2 tracking-tight">Ecosistema Arquitectónico BiteFixes</h2>
          <p className="text-gray-500 mt-2 text-sm leading-relaxed">
            Esta arquitectura desacoplada y orientada a eventos permite que múltiples canales de contacto consuman la misma lógica de IA y base de datos con total consistencia transaccional. Haz clic en los nodos para ver sus detalles.
          </p>
        </div>

        {/* Interactive Diagram Container */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mt-10 relative">
          {nodes.map((node, idx) => {
            const IconComponent = node.icon;
            const isActive = activeNode === node.id;
            return (
              <div 
                key={node.id}
                onClick={() => setActiveNode(isActive ? null : node.id)}
                className={`relative flex flex-col p-6 rounded-2xl border cursor-pointer transition-all duration-300 ${
                  isActive 
                    ? 'ring-2 ring-offset-2 ring-indigo-500 scale-[1.02] border-indigo-400 shadow-md' 
                    : 'hover:border-gray-300 hover:shadow-xs border-gray-200 bg-white'
                }`}
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 border ${node.color}`}>
                  <IconComponent className="w-6 h-6" />
                </div>
                <h3 className="font-semibold text-gray-900 text-sm flex items-center gap-2">
                  {node.title}
                  {isActive && <CheckCircle className="w-4 h-4 text-indigo-600 ml-auto" />}
                </h3>
                <p className="text-xs text-gray-500 mt-2 leading-relaxed line-clamp-3">
                  {node.description}
                </p>
                <span className="text-xs font-medium text-indigo-600 mt-4 inline-flex items-center gap-1 hover:underline">
                  Ver especificaciones {idx < 3 && <ArrowRight className="w-3 h-3" />}
                </span>
                
                {/* Decorative Connecting Arrow */}
                {idx < 3 && (
                  <div className="hidden lg:flex absolute top-1/2 -right-4 translate-y-[-50%] z-10 w-8 h-8 items-center justify-center bg-white rounded-full border border-gray-200 shadow-xs">
                    <ArrowRight className="w-4 h-4 text-gray-400" />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Active Node Detail Drawer */}
        {activeNode && (
          <div className="mt-6 p-5 bg-slate-50 border border-slate-200 rounded-xl animate-fade-in">
            {nodes.filter(n => n.id === activeNode).map(node => {
              const Icon = node.icon;
              return (
                <div key={node.id} className="flex flex-col md:flex-row gap-4 items-start">
                  <div className="p-3 bg-white border border-slate-200 rounded-lg text-slate-800 shrink-0">
                    <Icon className="w-8 h-8" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900 text-base">{node.title}</h4>
                    <p className="text-slate-600 text-sm mt-1 leading-relaxed">{node.description}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {node.id === 'clients' && (
                        <>
                          <span className="px-2 py-0.5 bg-indigo-100 text-indigo-800 text-[11px] rounded font-mono">Meta Cloud API</span>
                          <span className="px-2 py-0.5 bg-indigo-100 text-indigo-800 text-[11px] rounded font-mono">CORS Enabled</span>
                          <span className="px-2 py-0.5 bg-indigo-100 text-indigo-800 text-[11px] rounded font-mono">JSON Payloads</span>
                        </>
                      )}
                      {node.id === 'fastapi' && (
                        <>
                          <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 text-[11px] rounded font-mono">Uvicorn ASGI</span>
                          <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 text-[11px] rounded font-mono">FastAPI Router</span>
                          <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 text-[11px] rounded font-mono">Httpx Async</span>
                        </>
                      )}
                      {node.id === 'gemini' && (
                        <>
                          <span className="px-2 py-0.5 bg-sky-100 text-sky-800 text-[11px] rounded font-mono">google-genai SDK</span>
                          <span className="px-2 py-0.5 bg-sky-100 text-sky-800 text-[11px] rounded font-mono">Function Calling</span>
                          <span className="px-2 py-0.5 bg-sky-100 text-sky-800 text-[11px] rounded font-mono">Low Temp (0.3)</span>
                        </>
                      )}
                      {node.id === 'supabase' && (
                        <>
                          <span className="px-2 py-0.5 bg-teal-100 text-teal-800 text-[11px] rounded font-mono">PostgreSQL</span>
                          <span className="px-2 py-0.5 bg-teal-100 text-teal-800 text-[11px] rounded font-mono">supabase-py client</span>
                          <span className="px-2 py-0.5 bg-teal-100 text-teal-800 text-[11px] rounded font-mono">B-Tree Indexes</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Workflow Sequence */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6 md:p-8 shadow-xs">
        <h3 className="text-lg font-bold text-gray-900 tracking-tight flex items-center gap-2">
          <Webhook className="w-5 h-5 text-indigo-600" />
          Secuencia de Ejecución del Agente Técnico
        </h3>
        <p className="text-sm text-gray-500 mt-1 leading-relaxed">
          Flujo detallado de control cuando un usuario envía un mensaje solicitando soporte técnico:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mt-8">
          {interactions.map((step, idx) => (
            <div key={idx} className="relative bg-slate-50/50 rounded-xl p-5 border border-slate-100 flex flex-col">
              <span className="absolute -top-3 left-4 w-7 h-7 bg-indigo-600 text-white font-bold rounded-full flex items-center justify-center text-xs shadow-xs">
                {idx + 1}
              </span>
              <h4 className="font-semibold text-slate-800 text-sm mt-1">{step.title}</h4>
              <p className="text-[11px] text-slate-500 mt-2 leading-relaxed flex-grow">
                {step.desc}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Security Policies */}
      <div className="bg-slate-900 rounded-2xl p-6 md:p-8 text-white grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <span className="px-2 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-semibold rounded-full uppercase">Políticas de Seguridad</span>
          <h3 className="text-xl font-bold mt-3 tracking-tight">Buenas Prácticas Arquitectónicas</h3>
          <p className="text-slate-400 text-xs mt-2 leading-relaxed">
            Un backend omnicanal de soporte técnico que maneja información sensible (direcciones de clientes) y que interactúa con IA requiere salvaguardas estrictas:
          </p>
          <ul className="space-y-3 mt-4 text-xs text-slate-300">
            <li className="flex items-start gap-2">
              <Shield className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span><strong>Variables Fuera de Código:</strong> Las credenciales de Supabase y Google Gen AI nunca se inyectan directamente en archivos. Se consumen mediante archivos <code className="bg-slate-800 px-1 py-0.5 rounded text-slate-200">.env</code> seguros.</span>
            </li>
            <li className="flex items-start gap-2">
              <Shield className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span><strong>Validación de Webhooks:</strong> FastAPI implementa autenticación por Verify Token de Meta para bloquear llamadas maliciosas de fuentes externas.</span>
            </li>
            <li className="flex items-start gap-2">
              <Shield className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span><strong>Límites Conversacionales:</strong> Las instrucciones del sistema de Gemini acotan explícitamente el rango de acción, previniendo inyecciones de prompts o respuestas fuera del ámbito corporativo.</span>
            </li>
          </ul>
        </div>
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-800 flex flex-col justify-between">
          <div>
            <h4 className="font-bold text-sm text-slate-200">¿Por qué Supabase + Gemini 3.5 Flash?</h4>
            <p className="text-slate-400 text-[11px] mt-2 leading-relaxed">
              <strong>Supabase</strong> entrega la consistencia de una base de datos PostgreSQL con APIs HTTP autogeneradas ideales para dispositivos IoT o chatbots de alta frecuencia. 
            </p>
            <p className="text-slate-400 text-[11px] mt-2 leading-relaxed">
              <strong>Gemini 3.5 Flash</strong> entrega velocidad sobresaliente en procesamiento conversacional y una precisión de primer nivel para llamadas a funciones (Function Calling) nativas, indispensables para resolver tickets sin demoras artificiales.
            </p>
          </div>
          <div className="pt-4 border-t border-slate-700/50 flex items-center justify-between text-xs text-indigo-400">
            <span>Arquitecto de Soluciones Senior</span>
            <span className="font-mono text-[10px] text-slate-500">v1.0.0 Stable</span>
          </div>
        </div>
      </div>
    </div>
  );
}
