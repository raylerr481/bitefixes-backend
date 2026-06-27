import React, { useState, useEffect, useRef } from 'react';
import { 
  Smartphone, MessageSquare, Database, Terminal, Send, CheckCheck, 
  Trash2, RotateCcw, Plus, Search, HelpCircle, Bot, AlertCircle, Play, UserPlus, Server
} from 'lucide-react';
import { ClientRecord, TicketRecord, ChatMessage, DeveloperLog } from '../types';

export default function Playground() {
  // Initial demo data
  const initialClients: ClientRecord[] = [
    { id: 'c-8f2a1', nombre: 'Carlos Mendoza', whatsapp: '34612345678', direccion: 'Calle Gran Vía 45, Piso 3, Madrid' },
    { id: 'c-9e3b4', nombre: 'María Fernández', whatsapp: '34698765432', direccion: 'Avenida Diagonal 120, Barcelona' }
  ];

  const initialTickets: TicketRecord[] = [
    { id: '1001', created_at: new Date(Date.now() - 3600000 * 24).toISOString(), categoria: 'Hardware', cliente_id: 'c-8f2a1', descripcion: 'Mi computadora portátil enciende pero la pantalla se queda completamente en negro.', estatus: 'Abierto' },
    { id: '1002', created_at: new Date(Date.now() - 3600000 * 4).toISOString(), categoria: 'Redes', cliente_id: 'c-9e3b4', descripcion: 'El enrutador de oficina pierde conexión intermitentemente cada tarde a las 3 PM.', estatus: 'En Proceso' }
  ];

  const initialLogs: DeveloperLog[] = [
    { id: 'l1', timestamp: new Date().toLocaleTimeString(), source: 'fastapi', type: 'info', title: 'Servidor Iniciado', message: 'FastAPI corriendo exitosamente en http://0.0.0.0:3000' },
    { id: 'l2', timestamp: new Date().toLocaleTimeString(), source: 'supabase', type: 'success', title: 'Conexión Supabase', message: 'Establecida conexión segura con el pool de base de datos Postgres.' },
    { id: 'l3', timestamp: new Date().toLocaleTimeString(), source: 'gemini', type: 'info', title: 'Agente Cargado', message: 'Gemini 3.5 Flash cargado con instrucciones de soporte de BiteFixes.' }
  ];

  // React State for simulated tables and console
  const [clients, setClients] = useState<ClientRecord[]>(initialClients);
  const [tickets, setTickets] = useState<TicketRecord[]>(initialTickets);
  const [logs, setLogs] = useState<DeveloperLog[]>(initialLogs);
  const [activeTab, setActiveTab] = useState<'database' | 'terminal'>('terminal');
  const [activeChannel, setActiveChannel] = useState<'whatsapp' | 'web'>('whatsapp');
  
  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'm-init',
      sender: 'bot',
      text: '¡Hola! Bienvenido al canal de soporte técnico de BiteFixes. ¿En qué puedo ayudarte hoy con tus equipos o sistemas?',
      timestamp: new Date()
    }
  ]);
  const [inputText, setInputText] = useState<string>('');
  
  // Custom simulator state machine to guide Gemini's behavior
  const [phoneNumber, setPhoneNumber] = useState<string>('34612345678'); // Default test number (Carlos)
  const [customPhoneInput, setCustomPhoneInput] = useState<string>('34612345678');
  const [userProfile, setUserProfile] = useState<ClientRecord | null>(null);
  const [currentFlowStep, setCurrentFlowStep] = useState<'IDLE' | 'AWAITING_NAME' | 'AWAITING_ADDRESS' | 'AWAITING_PROBLEM'>('IDLE');
  const [tempNewClient, setTempNewClient] = useState<Partial<ClientRecord>>({});

  // Search inside tables
  const [clientSearch, setClientSearch] = useState<string>('');
  const [ticketSearch, setTicketSearch] = useState<string>('');

  const chatEndRef = useRef<HTMLDivElement>(null);
  const consoleEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat and logs
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    consoleEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Load profile whenever phone changes
  useEffect(() => {
    const matched = clients.find(c => c.whatsapp === phoneNumber);
    setUserProfile(matched || null);
    // Reset conversation on phone switch to show fresh verification
    setMessages([
      {
        id: `m-init-${phoneNumber}`,
        sender: 'bot',
        text: '¡Hola! Bienvenido al canal de soporte técnico de BiteFixes. ¿En qué puedo ayudarte hoy con tus equipos o sistemas?',
        timestamp: new Date()
      }
    ]);
    setCurrentFlowStep('IDLE');
    setTempNewClient({});
    addLog('fastapi', 'info', 'Nueva Sesión', `Usuario cambió número de canal a: +${phoneNumber}`);
  }, [phoneNumber]);

  // DB Helpers
  const addLog = (source: 'whatsapp' | 'gemini' | 'supabase' | 'fastapi', type: 'info' | 'success' | 'warning' | 'error', title: string, message: string, payload?: any) => {
    const newLog: DeveloperLog = {
      id: `l-${Math.random().toString(36).substr(2, 5)}`,
      timestamp: new Date().toLocaleTimeString(),
      source,
      type,
      title,
      message,
      payload: payload ? JSON.stringify(payload, null, 2) : undefined
    };
    setLogs(prev => [...prev, newLog]);
  };

  const handleResetSimulator = () => {
    setClients(initialClients);
    setTickets(initialTickets);
    setLogs(initialLogs);
    setMessages([
      {
        id: 'm-reset',
        sender: 'bot',
        text: '¡Hola! Bienvenido al canal de soporte de BiteFixes. ¿En qué puedo ayudarte hoy?',
        timestamp: new Date()
      }
    ]);
    setPhoneNumber('34612345678');
    setCustomPhoneInput('34612345678');
    setCurrentFlowStep('IDLE');
    setTempNewClient({});
    addLog('fastapi', 'warning', 'Sistema Reiniciado', 'Base de datos simulada y consola restaurados a valores demo.');
  };

  // Automated chatbot engine (Simulates FastAPI Python code behavior)
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const userMsg = inputText.trim();
    setInputText('');

    // Append User Message
    const userMessageId = `msg-user-${Date.now()}`;
    const newUserMsg: ChatMessage = {
      id: userMessageId,
      sender: 'user',
      text: userMsg,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newUserMsg]);

    // 1. FastAPI Webhook Trigger log
    const channelLabel = activeChannel === 'whatsapp' ? 'WhatsApp Webhook' : 'API Directa (Web)';
    addLog('whatsapp', 'info', `HTTP POST /webhook/${activeChannel}`, `Mensaje entrante de +${phoneNumber}: "${userMsg}"`, {
      from: phoneNumber,
      channel: activeChannel,
      message: userMsg,
      timestamp: new Date().toISOString()
    });

    // Short processing delay for simulation realism
    setTimeout(() => {
      processAgentStep(userMsg);
    }, 800);
  };

  // The state machine replicating 'tools.py' and 'main.py' logic
  const processAgentStep = (userText: string) => {
    // 2. Gemini execution logging
    addLog('gemini', 'info', 'Gemini Agent Processing', 'Ejecutando iteración con Gemini 3.5 Flash y tools habilitados...');

    // Flow Step A: IDLE (Start of conversational verification)
    if (currentFlowStep === 'IDLE') {
      // Prompt Gemini Tool verify
      addLog('gemini', 'warning', 'Function Call Request', 'Gemini solicita llamar a: tool_verificar_cliente', {
        numero_whatsapp: `+${phoneNumber}`
      });

      // DB Search simulation
      addLog('supabase', 'info', 'Supabase Query', `SELECT * FROM clientes WHERE whatsapp = '${phoneNumber}'`);
      
      const existingClient = clients.find(c => c.whatsapp === phoneNumber);

      if (existingClient) {
        // Result: Registered
        addLog('supabase', 'success', 'Query Resultado', 'Cliente encontrado en la base de datos.', existingClient);
        addLog('gemini', 'success', 'Function Call Response', `tool_verificar_cliente devolvió "registrado" (${existingClient.nombre})`);

        // Now categorize and process the technical request
        handleTechnicalProblem(userText, existingClient);
      } else {
        // Result: Not Registered
        addLog('supabase', 'warning', 'Query Resultado', 'Cliente no registrado (0 registros devueltos).');
        addLog('gemini', 'success', 'Function Call Response', 'tool_verificar_cliente devolvió "no_registrado"');

        // Transition to registration flow
        addLog('gemini', 'info', 'AI Thinking', 'El usuario no es cliente. Siguiendo el protocolo, solicito el nombre completo.');
        
        const botReply = `Veo que es tu primera vez comunicándote con el soporte técnico de **BiteFixes**. ¡Es un placer atenderte! Para darte de alta en nuestro sistema y poder agendar servicios técnicos, ¿podrías indicarme tu **nombre completo**?`;
        
        setMessages(prev => [...prev, {
          id: `msg-bot-${Date.now()}`,
          sender: 'bot',
          text: botReply,
          timestamp: new Date()
        }]);

        setCurrentFlowStep('AWAITING_NAME');
        addLog('whatsapp', 'success', 'Webhook Response Sent', 'Respuesta HTTP 200 entregada a Meta API.', { reply: botReply });
      }
    } 
    
    // Flow Step B: Registering - Awaiting Name
    else if (currentFlowStep === 'AWAITING_NAME') {
      const parsedName = userText;
      setTempNewClient(prev => ({ ...prev, nombre: parsedName }));
      
      addLog('gemini', 'info', 'AI Thinking', `Nombre provisto: "${parsedName}". Solicitando ahora la dirección física.`);
      
      const botReply = `Muchas gracias, **${parsedName}**. Por último, indícame tu **dirección física** completa (calle, número, piso y ciudad) para que nuestros técnicos sepan dónde acudir si es necesario el soporte en sitio.`;
      
      setMessages(prev => [...prev, {
        id: `msg-bot-${Date.now()}`,
        sender: 'bot',
        text: botReply,
        timestamp: new Date()
      }]);

      setCurrentFlowStep('AWAITING_ADDRESS');
      addLog('whatsapp', 'success', 'Webhook Response Sent', 'Respuesta de registro (Dirección) enviada.', { reply: botReply });
    }

    // Flow Step C: Registering - Awaiting Address
    else if (currentFlowStep === 'AWAITING_ADDRESS') {
      const parsedAddress = userText;
      const completedClient: ClientRecord = {
        id: `c-${Math.random().toString(36).substr(2, 5)}`,
        nombre: tempNewClient.nombre || 'Cliente Nuevo',
        whatsapp: phoneNumber,
        direccion: parsedAddress
      };

      // Trigger Tool Call log
      addLog('gemini', 'warning', 'Function Call Request', 'Gemini solicita llamar a: tool_registrar_cliente', completedClient);
      addLog('supabase', 'info', 'Supabase Insert', `INSERT INTO clientes (nombre, whatsapp, direccion) VALUES ('${completedClient.nombre}', '${completedClient.whatsapp}', '${completedClient.direccion}')`);

      // Update clients state
      setClients(prev => [...prev, completedClient]);
      setUserProfile(completedClient);

      addLog('supabase', 'success', 'Insert Resultado', 'Registro insertado con éxito en tabla clientes.', completedClient);
      addLog('gemini', 'success', 'Function Call Response', 'tool_registrar_cliente finalizado.');

      addLog('gemini', 'info', 'AI Thinking', 'Cliente registrado. Ahora le doy la bienvenida formal y pregunto por su problema.');

      const botReply = `¡Excelente! Te he dado de alta exitosamente en BiteFixes, **${completedClient.nombre}**. Tu registro ha quedado asociado a tu número y tu dirección: _${completedClient.direccion}_.\n\nAhora sí, descríbeme detalladamente la falla o servicio técnico que requieres el día de hoy.`;
      
      setMessages(prev => [...prev, {
        id: `msg-bot-${Date.now()}`,
        sender: 'bot',
        text: botReply,
        timestamp: new Date()
      }]);

      setCurrentFlowStep('AWAITING_PROBLEM');
      addLog('whatsapp', 'success', 'Webhook Response Sent', 'Respuesta de bienvenida y solicitud de problema despachada.', { reply: botReply });
    }

    // Flow Step D: Process Technical Request (For newly registered or returning client)
    else if (currentFlowStep === 'AWAITING_PROBLEM' || currentFlowStep === 'IDLE') {
      const activeClient = userProfile || clients.find(c => c.whatsapp === phoneNumber);
      if (activeClient) {
        handleTechnicalProblem(userText, activeClient);
      }
    }
  };

  const handleTechnicalProblem = (problemDescription: string, clientRecord: ClientRecord) => {
    // 3. Classify with NLP simulator (mocking Gemini's categorization prompt)
    const lowerText = problemDescription.toLowerCase();
    let category: 'Hardware' | 'Software' | 'Redes' | 'Comercial' | 'Otro' = 'Otro';
    let catReason = 'Descripción general';

    if (
      lowerText.includes('pantalla') || lowerText.includes('laptop') || lowerText.includes('computadora') || 
      lowerText.includes('pc') || lowerText.includes('teclado') || lowerText.includes('disco') || 
      lowerText.includes('memoria') || lowerText.includes('hardware') || lowerText.includes('no prende') || 
      lowerText.includes('ventilador') || lowerText.includes('recalienta')
    ) {
      category = 'Hardware';
      catReason = 'Mención de componente físico, equipo que no prende o pantalla.';
    } else if (
      lowerText.includes('programa') || lowerText.includes('sistema') || lowerText.includes('windows') || 
      lowerText.includes('office') || lowerText.includes('antivirus') || lowerText.includes('formatear') || 
      lowerText.includes('licencia') || lowerText.includes('excel') || lowerText.includes('software') || 
      lowerText.includes('virus') || lowerText.includes('lento')
    ) {
      category = 'Software';
      catReason = 'Mención de sistemas operativos, virus, formateo o suites de oficina.';
    } else if (
      lowerText.includes('internet') || lowerText.includes('wifi') || lowerText.includes('router') || 
      lowerText.includes('modem') || lowerText.includes('enrutador') || lowerText.includes('conexion') || 
      lowerText.includes('fibra') || lowerText.includes('red') || lowerText.includes('redes') || 
      lowerText.includes('cable')
    ) {
      category = 'Redes';
      catReason = 'Mención de conectividad de red, ruteadores o modulación.';
    } else if (
      lowerText.includes('cotizar') || lowerText.includes('cotizacion') || lowerText.includes('precio') || 
      lowerText.includes('comprar') || lowerText.includes('contrato') || lowerText.includes('factura') || 
      lowerText.includes('empresa') || lowerText.includes('comercial') || lowerText.includes('licitacion')
    ) {
      category = 'Comercial';
      catReason = 'Consulta de índole de compras, licitaciones o contratos corporativos.';
    }

    addLog('gemini', 'info', 'AI Thinking', `Categoría clasificada: "${category}". Razón: ${catReason}`);

    // Create ticket payload
    const ticketId = (parseInt(tickets[tickets.length - 1]?.id || '1000') + 1).toString();
    const newTicket: TicketRecord = {
      id: ticketId,
      created_at: new Date().toISOString(),
      categoria: category,
      cliente_id: clientRecord.id,
      descripcion: problemDescription,
      estatus: 'Abierto'
    };

    // Trigger Tool request
    addLog('gemini', 'warning', 'Function Call Request', 'Gemini solicita llamar a: tool_crear_ticket', {
      cliente_id: clientRecord.id,
      categoria: category,
      descripcion: problemDescription
    });

    addLog('supabase', 'info', 'Supabase Insert', `INSERT INTO tickets (cliente_id, categoria, descripcion, estatus) VALUES ('${clientRecord.id}', '${category}', '${problemDescription}', 'Abierto')`);

    // Update tickets state
    setTickets(prev => [...prev, newTicket]);

    addLog('supabase', 'success', 'Insert Resultado', `Ticket #${ticketId} insertado con éxito en tabla tickets.`, newTicket);
    addLog('gemini', 'success', 'Function Call Response', `tool_crear_ticket finalizado. Ticket ID generado: #${ticketId}`);

    addLog('gemini', 'info', 'AI Thinking', 'Ticket creado. Respondiendo confirmación con número de reporte.');

    const botReply = `Entendido perfectly, **${clientRecord.nombre}**. He registrado tu solicitud para el departamento de **${category}**.\n\nSe ha levantado el **Ticket de Soporte #${ticketId}** con estatus **Abierto**.\n\nUn especialista técnico de BiteFixes ha sido asignado y se comunicará contigo al +${phoneNumber} o acudirá a la dirección: _${clientRecord.direccion}_ para solventar el inconveniente. ¡Gracias por confiar en BiteFixes!`;

    setMessages(prev => [...prev, {
      id: `msg-bot-${Date.now()}`,
      sender: 'bot',
      text: botReply,
      timestamp: new Date()
    }]);

    setCurrentFlowStep('IDLE'); // Reset flow for next inquiries
    addLog('whatsapp', 'success', 'Webhook Response Sent', `Respuesta final despachada al cliente para Ticket #${ticketId}.`, { reply: botReply });
  };

  // Switch phone handler
  const handlePhoneSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = customPhoneInput.replace(/\D/g, '');
    if (clean) {
      setPhoneNumber(clean);
    }
  };

  // Format date helper
  const formatDate = (isoStr: string) => {
    try {
      return new Date(isoStr).toLocaleString();
    } catch {
      return isoStr;
    }
  };

  // Filter lists
  const filteredClients = clients.filter(c => 
    c.nombre.toLowerCase().includes(clientSearch.toLowerCase()) || 
    c.whatsapp.includes(clientSearch) ||
    c.direccion.toLowerCase().includes(clientSearch.toLowerCase())
  );

  const filteredTickets = tickets.filter(t => {
    const ownerName = clients.find(c => c.id === t.cliente_id)?.nombre || 'Desconocido';
    return t.id.includes(ticketSearch) || 
      t.categoria.toLowerCase().includes(ticketSearch.toLowerCase()) ||
      t.descripcion.toLowerCase().includes(ticketSearch.toLowerCase()) ||
      ownerName.toLowerCase().includes(ticketSearch.toLowerCase()) ||
      t.estatus.toLowerCase().includes(ticketSearch.toLowerCase());
  });

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 animate-fade-in" id="playground">
      
      {/* LEFT COLUMN: The Client Omnichannel Simulator */}
      <div className="xl:col-span-5 flex flex-col space-y-4">
        
        {/* Simulator Settings */}
        <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-gray-900 text-sm tracking-tight flex items-center gap-2">
              <Smartphone className="w-4 h-4 text-indigo-600" />
              Simulador del Cliente
            </h3>
            <button 
              onClick={handleResetSimulator}
              className="text-xs font-semibold text-gray-500 hover:text-slate-900 flex items-center gap-1 hover:bg-gray-50 px-2 py-1 rounded-lg transition-all"
              title="Restaurar base de datos simulada"
            >
              <RotateCcw className="w-3 h-3" />
              Restaurar
            </button>
          </div>

          <p className="text-xs text-gray-500 mt-1 leading-relaxed">
            Elige el canal digital y el número de remitente para probar las respuestas de la IA y el registro dinámico de tickets:
          </p>

          {/* Channel Selectors */}
          <div className="grid grid-cols-2 gap-2 mt-4">
            <button
              onClick={() => setActiveChannel('whatsapp')}
              className={`flex items-center justify-center gap-2 py-2 px-3 text-xs font-medium rounded-xl border transition-all ${
                activeChannel === 'whatsapp'
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              WhatsApp Business
            </button>
            <button
              onClick={() => setActiveChannel('web')}
              className={`flex items-center justify-center gap-2 py-2 px-3 text-xs font-medium rounded-xl border transition-all ${
                activeChannel === 'web'
                  ? 'bg-indigo-50 border-indigo-200 text-indigo-800'
                  : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
              Widget Web / Móvil
            </button>
          </div>

          {/* Quick Contacts Switcher */}
          <div className="mt-4 pt-4 border-t border-gray-100">
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block mb-2">
              Probar Escenarios de Remitentes
            </span>
            
            <div className="space-y-1.5">
              {/* Scenario 1: Returning client */}
              <button
                onClick={() => {
                  setPhoneNumber('34612345678');
                  setCustomPhoneInput('34612345678');
                }}
                className={`w-full flex items-center justify-between p-2.5 rounded-xl text-left border text-xs transition-all ${
                  phoneNumber === '34612345678'
                    ? 'bg-slate-900 border-slate-950 text-white'
                    : 'bg-slate-50 border-slate-100 hover:bg-slate-100 text-slate-700'
                }`}
              >
                <div>
                  <div className="font-semibold flex items-center gap-1.5">
                    Carlos Mendoza
                    <span className={`text-[9px] px-1.5 py-0.2 rounded font-mono ${phoneNumber === '34612345678' ? 'bg-emerald-900 text-emerald-200' : 'bg-emerald-100 text-emerald-800'}`}>
                      Registrado
                    </span>
                  </div>
                  <div className={`text-[10px] ${phoneNumber === '34612345678' ? 'text-slate-300' : 'text-slate-500'}`}>
                    WhatsApp: +34 612 34 56 78
                  </div>
                </div>
                <Play className={`w-3 h-3 ${phoneNumber === '34612345678' ? 'text-white' : 'text-slate-400'}`} />
              </button>

              {/* Scenario 2: Unregistered client */}
              <button
                onClick={() => {
                  setPhoneNumber('34655555555');
                  setCustomPhoneInput('34655555555');
                }}
                className={`w-full flex items-center justify-between p-2.5 rounded-xl text-left border text-xs transition-all ${
                  phoneNumber === '34655555555'
                    ? 'bg-slate-900 border-slate-950 text-white'
                    : 'bg-slate-50 border-slate-100 hover:bg-slate-100 text-slate-700'
                }`}
              >
                <div>
                  <div className="font-semibold flex items-center gap-1.5">
                    Anónimo / Remitente Desconocido
                    <span className={`text-[9px] px-1.5 py-0.2 rounded font-mono ${phoneNumber === '34655555555' ? 'bg-amber-900 text-amber-200' : 'bg-amber-100 text-amber-800'}`}>
                      No Registrado
                    </span>
                  </div>
                  <div className={`text-[10px] ${phoneNumber === '34655555555' ? 'text-slate-300' : 'text-slate-500'}`}>
                    WhatsApp: +34 655 55 55 55
                  </div>
                </div>
                <UserPlus className={`w-3.5 h-3.5 ${phoneNumber === '34655555555' ? 'text-white' : 'text-slate-400'}`} />
              </button>
            </div>

            {/* Manual custom phone input */}
            <form onSubmit={handlePhoneSubmit} className="flex gap-2 mt-3">
              <input
                type="text"
                placeholder="Ingresar número manual, ej: 34600112233"
                value={customPhoneInput}
                onChange={(e) => setCustomPhoneInput(e.target.value)}
                className="flex-grow px-3 py-1.5 text-xs border border-gray-200 rounded-lg font-mono focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
              />
              <button
                type="submit"
                className="px-3 py-1.5 text-xs font-semibold bg-gray-100 hover:bg-gray-200 active:bg-gray-300 text-gray-700 rounded-lg transition-all"
              >
                Fijar
              </button>
            </form>
          </div>
        </div>

        {/* CHAT DISPLAY CONTAINER */}
        <div className="flex-grow bg-white rounded-3xl border border-gray-100 shadow-md overflow-hidden flex flex-col min-h-[480px] max-h-[580px]">
          
          {/* Mock Header */}
          {activeChannel === 'whatsapp' ? (
            /* WhatsApp Style Header */
            <div className="bg-[#075e54] text-white px-5 py-4 flex items-center gap-3 shrink-0">
              <div className="w-10 h-10 rounded-full bg-emerald-900 border border-emerald-800 flex items-center justify-center text-sm font-bold">
                BF
              </div>
              <div className="flex-grow">
                <div className="font-bold text-sm tracking-tight flex items-center gap-1.5">
                  BiteFixes Soporte 🛠️
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block animate-ping"></span>
                </div>
                <div className="text-[10px] text-emerald-200">Asistente Virtual (Bitey) • Online</div>
              </div>
              <div className="text-[10px] text-emerald-100/80 bg-emerald-800/40 px-2.5 py-0.5 rounded-full font-mono">
                +{phoneNumber}
              </div>
            </div>
          ) : (
            /* Web Chat Style Header */
            <div className="bg-slate-900 text-white px-5 py-4 flex items-center gap-3 shrink-0">
              <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center">
                <Bot className="w-5 h-5" />
              </div>
              <div className="flex-grow">
                <div className="font-bold text-sm tracking-tight">Soporte BiteFixes</div>
                <div className="text-[10px] text-indigo-300">Respuesta asíncrona instantánea</div>
              </div>
              <span className="text-[10px] text-slate-400 font-mono">Web Widget</span>
            </div>
          )}

          {/* Messages Body */}
          <div className="flex-grow p-4 overflow-y-auto bg-[#efeae2] dark:bg-slate-950/40 space-y-3 scrollbar-thin">
            {/* Encryption Notice */}
            {activeChannel === 'whatsapp' && (
              <div className="mx-auto max-w-[260px] bg-amber-50 text-amber-800/80 border border-amber-100 p-2 rounded-lg text-[9px] text-center leading-normal">
                🔒 Las conversaciones están cifradas en tránsito por Meta API. Este chat simula de forma directa la lógica del webhook en FastAPI.
              </div>
            )}

            {messages.map((msg) => {
              const isBot = msg.sender === 'bot';
              return (
                <div 
                  key={msg.id}
                  className={`flex w-full ${isBot ? 'justify-start' : 'justify-end'} animate-fade-in`}
                >
                  <div className={`max-w-[82%] p-3.5 rounded-2xl shadow-xs leading-relaxed text-xs relative ${
                    isBot 
                      ? 'bg-white text-gray-800 rounded-tl-none border border-slate-100' 
                      : activeChannel === 'whatsapp' 
                        ? 'bg-[#d9fdd3] text-gray-900 rounded-tr-none'
                        : 'bg-indigo-600 text-white rounded-tr-none'
                  }`}>
                    {/* Render markdown style lines */}
                    <p className="whitespace-pre-wrap">
                      {msg.text.split('\n').map((line, lIdx) => {
                        // Support bold indicators
                        let elements: React.ReactNode[] = [];
                        let textCursor = line;
                        let index = 0;
                        while(textCursor.includes('**')) {
                          const startIdx = textCursor.indexOf('**');
                          const endIdx = textCursor.indexOf('**', startIdx + 2);
                          if(endIdx === -1) break;
                          
                          elements.push(textCursor.substring(0, startIdx));
                          elements.push(
                            <strong key={index++} className="font-bold underline">
                              {textCursor.substring(startIdx + 2, endIdx)}
                            </strong>
                          );
                          textCursor = textCursor.substring(endIdx + 2);
                        }
                        elements.push(textCursor);
                        return <span key={lIdx} className="block mt-1 first:mt-0">{elements}</span>;
                      })}
                    </p>
                    
                    {/* Message metadata footer */}
                    <div className={`text-[9px] mt-2 flex items-center justify-end gap-1 ${isBot ? 'text-gray-400' : activeChannel === 'whatsapp' ? 'text-emerald-700' : 'text-indigo-200'}`}>
                      <span>
                        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                      {!isBot && activeChannel === 'whatsapp' && (
                        <CheckCheck className="w-3 h-3 text-sky-500 inline-block" />
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
            <div ref={chatEndRef} />
          </div>

          {/* Form input */}
          <form onSubmit={handleSendMessage} className="p-3 bg-slate-50 border-t border-gray-100 flex items-center gap-2 shrink-0">
            <input
              type="text"
              placeholder="Escribe un mensaje técnico de soporte..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className="flex-grow px-4 py-2 text-xs bg-white border border-gray-200 rounded-full focus:outline-hidden focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 shadow-inner"
            />
            <button
              type="submit"
              className={`w-9 h-9 rounded-full flex items-center justify-center text-white shrink-0 transition-all ${
                inputText.trim() 
                  ? activeChannel === 'whatsapp' 
                    ? 'bg-[#00a884] hover:bg-[#008f72] active:bg-[#00755d] scale-105' 
                    : 'bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 scale-105'
                  : 'bg-gray-300 cursor-not-allowed'
              }`}
              disabled={!inputText.trim()}
            >
              <Send className="w-4 h-4 ml-0.5" />
            </button>
          </form>
        </div>
        
        {/* Help Suggestions inside Playground */}
        <div className="bg-indigo-50/50 border border-indigo-100 rounded-2xl p-4">
          <h4 className="text-xs font-bold text-indigo-900 flex items-center gap-1.5">
            <HelpCircle className="w-3.5 h-3.5 text-indigo-600" />
            Sugerencias para probar
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2.5">
            <button
              onClick={() => setInputText('Mi ordenador portátil se calienta mucho y se apaga de golpe')}
              className="p-2 text-[10px] text-left text-indigo-800 hover:bg-indigo-100/60 bg-white border border-indigo-100 rounded-lg transition-all truncate"
            >
              🔥 "Laptop recalienta y se apaga"
            </button>
            <button
              onClick={() => setInputText('No tengo acceso a internet, la luz del router parpadea roja')}
              className="p-2 text-[10px] text-left text-indigo-800 hover:bg-indigo-100/60 bg-white border border-indigo-100 rounded-lg transition-all truncate"
            >
              🌐 "Internet caido router rojo"
            </button>
            <button
              onClick={() => setInputText('Quiero formatear mi PC e instalar Windows 11 de cero')}
              className="p-2 text-[10px] text-left text-indigo-800 hover:bg-indigo-100/60 bg-white border border-indigo-100 rounded-lg transition-all truncate"
            >
              💻 "Instalar Windows 11 de cero"
            </button>
            <button
              onClick={() => setInputText('Necesito una cotización para contratar soporte corporativo en mi oficina')}
              className="p-2 text-[10px] text-left text-indigo-800 hover:bg-indigo-100/60 bg-white border border-indigo-100 rounded-lg transition-all truncate"
            >
              🏢 "Cotización oficina corporativa"
            </button>
          </div>
        </div>
      </div>

      {/* RIGHT COLUMN: The Developer Hub (Terminal logs & Database Tables) */}
      <div className="xl:col-span-7 flex flex-col space-y-4">
        
        {/* Tab Selector */}
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('terminal')}
            className={`flex items-center gap-2 py-3 px-6 text-xs font-semibold border-b-2 transition-all ${
              activeTab === 'terminal'
                ? 'border-indigo-600 text-indigo-600 font-bold bg-white'
                : 'border-transparent text-gray-500 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            <Terminal className="w-4 h-4" />
            Consola FastAPI (En Tiempo Real)
          </button>
          
          <button
            onClick={() => setActiveTab('database')}
            className={`flex items-center gap-2 py-3 px-6 text-xs font-semibold border-b-2 transition-all ${
              activeTab === 'database'
                ? 'border-indigo-600 text-indigo-600 font-bold bg-white'
                : 'border-transparent text-gray-500 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            <Database className="w-4 h-4" />
            Explorador Supabase DB (Live State)
          </button>
        </div>

        {/* TAB CONTENTS */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-xs p-5 flex-grow flex flex-col min-h-[580px] max-h-[700px] overflow-hidden">
          
          {/* TERMINAL TAB */}
          {activeTab === 'terminal' && (
            <div className="flex flex-col h-full overflow-hidden">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 shrink-0">
                <div>
                  <h4 className="font-bold text-gray-900 text-sm tracking-tight flex items-center gap-1.5">
                    <Server className="w-4 h-4 text-emerald-600" />
                    BiteFixes FastAPI Webhook Log Inspector
                  </h4>
                  <p className="text-[10px] text-gray-400 mt-0.5">Muestra la secuencia de peticiones HTTP, llamadas de Gemini y transacciones SQL.</p>
                </div>
                
                <button
                  onClick={() => setLogs(initialLogs)}
                  className="px-2.5 py-1 text-[10px] border border-gray-200 text-gray-500 hover:text-slate-900 hover:bg-slate-50 rounded-lg transition-all font-semibold flex items-center gap-1"
                >
                  <RotateCcw className="w-3 h-3" /> Limpiar Consola
                </button>
              </div>

              {/* Black Terminal Screen */}
              <div className="flex-grow bg-slate-950 rounded-xl p-4 mt-4 overflow-y-auto font-mono text-[11px] leading-relaxed text-slate-300 space-y-3.5 h-[400px]">
                {logs.length === 0 ? (
                  <div className="text-slate-500 text-center py-10">Consola inactiva. Envía un mensaje en el simulador de chat para disparar la secuencia del webhook.</div>
                ) : (
                  logs.map((log) => {
                    const srcLabels: Record<string, string> = {
                      fastapi: '[FASTAPI]',
                      supabase: '[SUPABASE]',
                      gemini: '[GEMINI ]',
                      whatsapp: '[WSP_API]'
                    };
                    
                    const srcColors: Record<string, string> = {
                      fastapi: 'text-emerald-400',
                      supabase: 'text-teal-400',
                      gemini: 'text-sky-400',
                      whatsapp: 'text-pink-400'
                    };

                    const typeColors: Record<string, string> = {
                      info: 'text-slate-400',
                      success: 'text-emerald-500 font-semibold',
                      warning: 'text-amber-500 font-semibold',
                      error: 'text-red-500 font-bold underline'
                    };

                    return (
                      <div key={log.id} className="border-b border-slate-900/60 pb-2.5 last:border-b-0 animate-fade-in">
                        <div className="flex flex-wrap items-center gap-x-2.5">
                          <span className="text-slate-500 text-[10px] select-none">{log.timestamp}</span>
                          <span className={`${srcColors[log.source]} font-bold`}>{srcLabels[log.source]}</span>
                          <span className="text-slate-100 font-semibold text-xs">{log.title}</span>
                          <span className={`text-[10px] uppercase font-mono px-1.5 py-0.2 bg-slate-900/80 rounded ${typeColors[log.type]}`}>
                            {log.type}
                          </span>
                        </div>
                        <p className="text-slate-300 mt-1 leading-normal ml-0">{log.message}</p>
                        
                        {log.payload && (
                          <pre className="mt-2 p-2 bg-slate-900 text-[10px] text-slate-400 rounded border border-slate-800/60 overflow-x-auto whitespace-pre">
                            {log.payload}
                          </pre>
                        )}
                      </div>
                    );
                  })
                )}
                <div ref={consoleEndRef} />
              </div>
            </div>
          )}

          {/* DATABASE TAB */}
          {activeTab === 'database' && (
            <div className="flex flex-col h-full overflow-hidden">
              
              {/* Clientes Table Title / Header */}
              <div className="pb-3 border-b border-slate-100 flex items-center justify-between shrink-0">
                <div>
                  <h4 className="font-bold text-gray-900 text-sm tracking-tight flex items-center gap-2">
                    Tabla: <span className="font-mono text-indigo-600 font-bold bg-indigo-50 px-2 py-0.5 rounded">clientes</span>
                  </h4>
                  <p className="text-[10px] text-gray-400 mt-0.5">Almacena el registro único de remitentes omnicanal asociados.</p>
                </div>
                
                {/* Search Bar for Clients */}
                <div className="relative w-44">
                  <Search className="absolute left-2.5 top-1.5 w-3.5 h-3.5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Buscar cliente..."
                    value={clientSearch}
                    onChange={(e) => setClientSearch(e.target.value)}
                    className="w-full pl-8 pr-3 py-1 text-[11px] border border-gray-200 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              {/* Clientes Grid List */}
              <div className="mt-3 overflow-auto max-h-[180px] border border-gray-100 rounded-xl shrink-0">
                <table className="w-full text-left text-xs text-gray-500 border-collapse">
                  <thead className="text-[10px] uppercase font-bold text-gray-700 bg-gray-50/80 sticky top-0">
                    <tr>
                      <th className="px-4 py-2 border-b border-gray-100">ID</th>
                      <th className="px-4 py-2 border-b border-gray-100">Nombre</th>
                      <th className="px-4 py-2 border-b border-gray-100">WhatsApp</th>
                      <th className="px-4 py-2 border-b border-gray-100">Dirección</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50 bg-white">
                    {filteredClients.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="px-4 py-4 text-center text-gray-400">Sin clientes cargados.</td>
                      </tr>
                    ) : (
                      filteredClients.map((client) => (
                        <tr key={client.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="px-4 py-2 font-mono text-[10px] text-indigo-600 font-semibold">{client.id}</td>
                          <td className="px-4 py-2 font-medium text-gray-900">{client.nombre}</td>
                          <td className="px-4 py-2 font-mono text-[11px] text-gray-700">+{client.whatsapp}</td>
                          <td className="px-4 py-2 truncate max-w-[150px]" title={client.direccion}>{client.direccion}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* Tickets Table Title / Header */}
              <div className="mt-6 pb-3 border-b border-slate-100 flex items-center justify-between shrink-0">
                <div>
                  <h4 className="font-bold text-gray-900 text-sm tracking-tight flex items-center gap-2">
                    Tabla: <span className="font-mono text-indigo-600 font-bold bg-indigo-50 px-2 py-0.5 rounded">tickets</span>
                  </h4>
                  <p className="text-[10px] text-gray-400 mt-0.5">Almacena las solicitudes técnicas levantadas por los agentes.</p>
                </div>
                
                {/* Search Bar for Tickets */}
                <div className="relative w-44">
                  <Search className="absolute left-2.5 top-1.5 w-3.5 h-3.5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Buscar ticket..."
                    value={ticketSearch}
                    onChange={(e) => setTicketSearch(e.target.value)}
                    className="w-full pl-8 pr-3 py-1 text-[11px] border border-gray-200 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              {/* Tickets Grid List */}
              <div className="mt-3 overflow-auto flex-grow border border-gray-100 rounded-xl min-h-[180px]">
                <table className="w-full text-left text-xs text-gray-500 border-collapse">
                  <thead className="text-[10px] uppercase font-bold text-gray-700 bg-gray-50/80 sticky top-0">
                    <tr>
                      <th className="px-4 py-2 border-b border-gray-100">Ticket #</th>
                      <th className="px-4 py-2 border-b border-gray-100">Cliente</th>
                      <th className="px-4 py-2 border-b border-gray-100">Categoría</th>
                      <th className="px-4 py-2 border-b border-gray-100">Descripción de Falla</th>
                      <th className="px-4 py-2 border-b border-gray-100">Estatus</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50 bg-white">
                    {filteredTickets.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-4 text-center text-gray-400">Sin tickets generados.</td>
                      </tr>
                    ) : (
                      filteredTickets.map((ticket) => {
                        const owner = clients.find(c => c.id === ticket.cliente_id)?.nombre || 'Desconocido';
                        
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
                          Resuelto: 'bg-gray-100 text-gray-700 border-gray-200'
                        };

                        return (
                          <tr key={ticket.id} className="hover:bg-slate-50/50 transition-colors">
                            <td className="px-4 py-2.5 font-mono text-[11px] text-gray-900 font-bold">#{ticket.id}</td>
                            <td className="px-4 py-2.5 font-medium text-gray-700">{owner}</td>
                            <td className="px-4 py-2.5">
                              <span className={`px-2 py-0.5 text-[10px] font-semibold rounded-md border ${catColors[ticket.categoria]}`}>
                                {ticket.categoria}
                              </span>
                            </td>
                            <td className="px-4 py-2.5 text-xs max-w-[180px] truncate" title={ticket.descripcion}>
                              {ticket.descripcion}
                            </td>
                            <td className="px-4 py-2.5">
                              <span className={`px-2 py-0.5 text-[10px] font-semibold rounded-md border ${statusColors[ticket.estatus]}`}>
                                {ticket.estatus}
                              </span>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
