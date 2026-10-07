import { useState } from 'react';
import { Brain, Layers, Satellite, Radio, CheckCircle, AlertCircle, TrendingUp, Database } from 'lucide-react';

export default function FoundationModelPanel() {
  const [expandedSection, setExpandedSection] = useState<string | null>('architecture');

  const modelStats = {
    parameters: '~30M',
    latentDim: 256,
    lidarEncoder: 'PointNet++',
    sarEncoder: '4-level U-Net',
    fusion: 'Cross-Modal Transformer',
    status: 'Training Ready'
  };

  const trainingObjectives = [
    { name: 'Cross-modal MAE', description: 'Masked autoencoding between modalities', status: 'ready' },
    { name: 'Contrastive Alignment', description: 'InfoNCE with augmented views', status: 'ready' },
    { name: 'Decoupled Representation', description: 'DeCUR adversarial discriminator', status: 'ready' },
    { name: 'Reconstruction', description: 'L1 + Chamfer + Angular losses', status: 'ready' }
  ];

  const dataSources = [
    { name: 'LiDAR Point Clouds', format: '(x, y, z, intensity)', density: '<22 pts/m²' },
    { name: 'SAR SLC Images', format: 'C-band VV+VH', resolution: '10m' }
  ];

  return (
    <div className="bg-[#0d1320] border border-slate-800/50 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-4">
        <Brain className="text-cyan-400" size={20} />
        <h2 className="text-sm font-semibold text-slate-200">Foundation Model - LiDAR-SAR Fusion</h2>
      </div>

      {/* Model Overview */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-slate-800/30 rounded p-3">
          <div className="text-[10px] text-slate-500 uppercase mb-1">Parameters</div>
          <div className="text-lg font-bold text-cyan-300">{modelStats.parameters}</div>
        </div>
        <div className="bg-slate-800/30 rounded p-3">
          <div className="text-[10px] text-slate-500 uppercase mb-1">Latent Dim</div>
          <div className="text-lg font-bold text-cyan-300">{modelStats.latentDim}</div>
        </div>
      </div>

      {/* Architecture */}
      <div className="mb-4">
        <button
          onClick={() => setExpandedSection(expandedSection === 'architecture' ? null : 'architecture')}
          className="w-full flex items-center justify-between p-2 bg-slate-800/20 rounded hover:bg-slate-800/30 transition-colors"
        >
          <span className="text-xs font-medium text-slate-300">Architecture</span>
          <span className="text-slate-500 text-xs">{expandedSection === 'architecture' ? '▼' : '▶'}</span>
        </button>
        {expandedSection === 'architecture' && (
          <div className="mt-2 space-y-2 text-[11px]">
            <div className="flex items-start gap-2">
              <Radio className="text-emerald-400 mt-0.5" size={12} />
              <div>
                <div className="text-slate-300 font-medium">LiDAR Branch</div>
                <div className="text-slate-500">{modelStats.lidarEncoder} (KNN k=16)</div>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Satellite className="text-emerald-400 mt-0.5" size={12} />
              <div>
                <div className="text-slate-300 font-medium">SAR Branch</div>
                <div className="text-slate-500">{modelStats.sarEncoder} (Residual)</div>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Layers className="text-emerald-400 mt-0.5" size={12} />
              <div>
                <div className="text-slate-300 font-medium">Fusion</div>
                <div className="text-slate-500">{modelStats.fusion} (4 layers, 8 heads)</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Training Objectives */}
      <div className="mb-4">
        <button
          onClick={() => setExpandedSection(expandedSection === 'objectives' ? null : 'objectives')}
          className="w-full flex items-center justify-between p-2 bg-slate-800/20 rounded hover:bg-slate-800/30 transition-colors"
        >
          <span className="text-xs font-medium text-slate-300">Training Objectives</span>
          <span className="text-slate-500 text-xs">{expandedSection === 'objectives' ? '▼' : '▶'}</span>
        </button>
        {expandedSection === 'objectives' && (
          <div className="mt-2 space-y-1.5">
            {trainingObjectives.map((obj, i) => (
              <div key={i} className="flex items-start gap-2 text-[11px]">
                <CheckCircle className="text-emerald-400 mt-0.5" size={12} />
                <div>
                  <div className="text-slate-300">{obj.name}</div>
                  <div className="text-slate-500 text-[10px]">{obj.description}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Data Sources */}
      <div className="mb-4">
        <button
          onClick={() => setExpandedSection(expandedSection === 'data' ? null : 'data')}
          className="w-full flex items-center justify-between p-2 bg-slate-800/20 rounded hover:bg-slate-800/30 transition-colors"
        >
          <span className="text-xs font-medium text-slate-300">Data Sources</span>
          <span className="text-slate-500 text-xs">{expandedSection === 'data' ? '▼' : '▶'}</span>
        </button>
        {expandedSection === 'data' && (
          <div className="mt-2 space-y-2">
            {dataSources.map((source, i) => (
              <div key={i} className="bg-slate-800/20 rounded p-2">
                <div className="text-[11px] text-slate-300 font-medium">{source.name}</div>
                <div className="text-[10px] text-slate-500 mt-0.5">
                  {source.format} • {source.density || source.resolution}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Status */}
      <div className="flex items-center gap-2 p-2 bg-emerald-500/10 border border-emerald-500/30 rounded">
        <TrendingUp className="text-emerald-400" size={14} />
        <div className="flex-1">
          <div className="text-[11px] text-emerald-300 font-medium">{modelStats.status}</div>
          <div className="text-[10px] text-slate-500">Ready for self-supervised training</div>
        </div>
      </div>

      {/* Documentation Link */}
      <div className="mt-4 pt-4 border-t border-slate-800/50">
        <a
          href="/foundation_model/README.md"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 text-[11px] text-cyan-400 hover:text-cyan-300 transition-colors"
        >
          <Database size={12} />
          <span>View full documentation</span>
        </a>
      </div>
    </div>
  );
}
