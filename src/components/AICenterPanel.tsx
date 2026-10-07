import React, { useState } from 'react';
import { 
  Brain, Cpu, Database, Play, Pause, CheckCircle, XCircle, 
  AlertCircle, Clock, TrendingUp, Settings, Eye, Zap,
  ChevronRight, ChevronDown, Activity, BarChart3
} from 'lucide-react';

interface AICenterPanelProps {
  className?: string;
}

export default function AICenterPanel({ className = '' }: AICenterPanelProps) {
  const [activeTab, setActiveTab] = useState<'commands' | 'models' | 'training' | 'inference' | 'audit'>('commands');
  const [commandInput, setCommandInput] = useState('');
  const [expandedSection, setExpandedSection] = useState<string | null>('overview');

  const tabs = [
    { id: 'commands', label: 'Órdenes IA', icon: Brain },
    { id: 'models', label: 'Modelos', icon: Cpu },
    { id: 'training', label: 'Entrenamiento', icon: Database },
    { id: 'inference', label: 'Inferencia', icon: Zap },
    { id: 'audit', label: 'Auditoría', icon: Activity },
  ];

  const modelStats = {
    total: 15,
    ready: 8,
    training: 2,
    validating: 3,
    disabled: 2,
  };

  const recentCommands = [
    { id: 'cmd_1', intent: 'ANALYZE_RISK', status: 'COMPLETED', timestamp: '2026-01-15 10:30:00' },
    { id: 'cmd_2', intent: 'EXPLORE_AREA', status: 'RUNNING', timestamp: '2026-01-15 10:25:00' },
    { id: 'cmd_3', intent: 'TRAIN_MODEL', status: 'WAITING_FOR_APPROVAL', timestamp: '2026-01-15 10:20:00' },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED':
      case 'READY':
      case 'HEALTHY':
        return 'text-emerald-400';
      case 'RUNNING':
      case 'TRAINING':
        return 'text-blue-400';
      case 'WAITING_FOR_APPROVAL':
      case 'VALIDATING':
        return 'text-amber-400';
      case 'FAILED':
      case 'DISABLED':
        return 'text-red-400';
      default:
        return 'text-slate-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED':
      case 'READY':
      case 'HEALTHY':
        return <CheckCircle size={14} className="text-emerald-400" />;
      case 'RUNNING':
      case 'TRAINING':
        return <Play size={14} className="text-blue-400" />;
      case 'WAITING_FOR_APPROVAL':
      case 'VALIDATING':
        return <Clock size={14} className="text-amber-400" />;
      case 'FAILED':
      case 'DISABLED':
        return <XCircle size={14} className="text-red-400" />;
      default:
        return <AlertCircle size={14} className="text-slate-400" />;
    }
  };

  return (
    <div className={`bg-[#0d1320] border border-slate-800/50 rounded-lg ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-slate-800/50">
        <div className="flex items-center gap-2">
          <Brain className="text-cyan-400" size={20} />
          <h2 className="text-sm font-semibold text-slate-200">Centro de IA</h2>
          <span className="text-[10px] text-slate-500 ml-auto">SAE AI Command & Training Center</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800/50">
        {tabs.map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-1.5 px-3 py-2 text-[11px] transition-colors ${
                activeTab === tab.id
                  ? 'text-cyan-300 border-b-2 border-cyan-400 bg-cyan-500/5'
                  : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/30'
              }`}
            >
              <Icon size={14} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Commands Tab */}
        {activeTab === 'commands' && (
          <div className="space-y-4">
            {/* Command Input */}
            <div className="bg-slate-800/30 rounded-lg p-3">
              <label className="text-[10px] text-slate-500 uppercase mb-2 block">
                Nueva Orden
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={commandInput}
                  onChange={(e) => setCommandInput(e.target.value)}
                  placeholder="Ej: Analiza riesgo de incendio en la zona..."
                  className="flex-1 px-3 py-2 bg-[#111827] border border-slate-700/50 rounded text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500/50"
                />
                <button className="px-4 py-2 bg-cyan-500/20 border border-cyan-500/30 rounded text-xs text-cyan-300 hover:bg-cyan-500/30 transition-colors">
                  Ejecutar
                </button>
              </div>
            </div>

            {/* Recent Commands */}
            <div>
              <h3 className="text-[11px] font-semibold text-slate-400 mb-2">Órdenes Recientes</h3>
              <div className="space-y-2">
                {recentCommands.map(cmd => (
                  <div key={cmd.id} className="flex items-center gap-2 p-2 bg-slate-800/20 rounded text-[11px]">
                    {getStatusIcon(cmd.status)}
                    <span className="text-slate-300 font-mono">{cmd.intent}</span>
                    <span className={`ml-auto ${getStatusColor(cmd.status)}`}>{cmd.status}</span>
                    <span className="text-slate-600 text-[10px]">{cmd.timestamp}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Models Tab */}
        {activeTab === 'models' && (
          <div className="space-y-4">
            {/* Model Stats */}
            <div className="grid grid-cols-5 gap-2">
              <div className="bg-slate-800/30 rounded p-2 text-center">
                <div className="text-lg font-bold text-cyan-300">{modelStats.total}</div>
                <div className="text-[9px] text-slate-500">Total</div>
              </div>
              <div className="bg-slate-800/30 rounded p-2 text-center">
                <div className="text-lg font-bold text-emerald-400">{modelStats.ready}</div>
                <div className="text-[9px] text-slate-500">Ready</div>
              </div>
              <div className="bg-slate-800/30 rounded p-2 text-center">
                <div className="text-lg font-bold text-blue-400">{modelStats.training}</div>
                <div className="text-[9px] text-slate-500">Training</div>
              </div>
              <div className="bg-slate-800/30 rounded p-2 text-center">
                <div className="text-lg font-bold text-amber-400">{modelStats.validating}</div>
                <div className="text-[9px] text-slate-500">Validating</div>
              </div>
              <div className="bg-slate-800/30 rounded p-2 text-center">
                <div className="text-lg font-bold text-red-400">{modelStats.disabled}</div>
                <div className="text-[9px] text-slate-500">Disabled</div>
              </div>
            </div>

            {/* Model List Placeholder */}
            <div className="bg-slate-800/20 rounded p-3 text-center text-[11px] text-slate-500">
              Registro de modelos integrado con SAE Core Model Registry
            </div>
          </div>
        )}

        {/* Training Tab */}
        {activeTab === 'training' && (
          <div className="space-y-4">
            <div className="bg-slate-800/20 rounded p-3 text-center text-[11px] text-slate-500">
              Centro de entrenamiento integrado con Training Center
              <br />
              <span className="text-[10px] text-slate-600">
                Requiere runtime PyTorch para ejecución real
              </span>
            </div>
          </div>
        )}

        {/* Inference Tab */}
        {activeTab === 'inference' && (
          <div className="space-y-4">
            <div className="bg-slate-800/20 rounded p-3 text-center text-[11px] text-slate-500">
              Centro de inferencia integrado con Inference Center
              <br />
              <span className="text-[10px] text-slate-600">
                Routing automático basado en capacidades y políticas
              </span>
            </div>
          </div>
        )}

        {/* Audit Tab */}
        {activeTab === 'audit' && (
          <div className="space-y-4">
            <div className="bg-slate-800/20 rounded p-3 text-center text-[11px] text-slate-500">
              Auditoría de operaciones de IA
              <br />
              <span className="text-[10px] text-slate-600">
                Trazabilidad completa de comandos, inferencias y entrenamientos
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-slate-800/50 text-[9px] text-slate-600">
        <div className="flex items-center justify-between">
          <span>AI Governance: Activa</span>
          <span>Policy Engine: Integrado</span>
          <span>Audit Trail: Habilitado</span>
        </div>
      </div>
    </div>
  );
}
