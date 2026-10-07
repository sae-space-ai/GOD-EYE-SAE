import { useState, useCallback, useEffect } from 'react';
import {
  Search, Globe, Layers, Radio, Satellite, Flame, Cloud,
  AlertTriangle, Plane, Ship, Camera, Building2, FileText,
  Shield, Bell, Settings, HelpCircle, ChevronLeft, ChevronRight,
  MapPin, Clock, Ruler, Camera as CameraIcon, Download,
  Bot, Command, Mic, MicOff, Palette, Eye, Target,
  Crosshair, Zap, Brain, Activity, Navigation,
  BarChart3, Globe2, Wifi, WifiOff, CheckCircle2, AlertCircle
} from 'lucide-react';
import Globe3D from './components/Globe';
import FoundationModelPanel from './components/FoundationModelPanel';
import { t, Locale, getLocaleName } from './i18n';
import { dataSources, resources, getActiveSourcesCount, getNotConfiguredCount, getKeylessSourcesCount } from './data/sources';
import type { ResourceStatus, OperationalMode, MicrophoneState } from './types';
import { useSources } from './hooks/useSources';
import { captureEvidence, listEvidence, verifyEvidence } from './services/evidence/engine';
import { recordAuditEvent, listAuditEvents } from './services/audit/engine';
import type { GeoEntity } from './services/sources/types';

function App() {
  const [locale, setLocale] = useState<Locale>('es-ES');
  const [showMission, setShowMission] = useState(true);
  const [leftPanelOpen, setLeftPanelOpen] = useState(true);
  const [rightPanelOpen, setRightPanelOpen] = useState(true);
  const [activeMode, setActiveMode] = useState<OperationalMode>('operational');
  const [coordinates, setCoordinates] = useState({ lat: 0, lng: 0 });
  const [searchQuery, setSearchQuery] = useState('');
  const [micState, setMicState] = useState<MicrophoneState>('deactivated');
  const [expandedCategory, setExpandedCategory] = useState<string | null>('dataLayers');
  const [showLangMenu, setShowLangMenu] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [dontShowMission, setDontShowMission] = useState(false);
  const [selectedResource, setSelectedResource] = useState<string | null>(null);
  const [globeReady, setGlobeReady] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState<GeoEntity | null>(null);
  const [evidenceCount, setEvidenceCount] = useState(0);
  const [showFoundationModel, setShowFoundationModel] = useState(false);
  
  // Source management
  const { sources, isInitialized, fetchSource, enableSource, disableSource, startAutoRefresh, getAllEntities } = useSources();
  
  // Initialize sources on mount
  useEffect(() => {
    if (isInitialized) {
      // Auto-enable USGS earthquakes (keyless, verified)
      enableSource('usgs-earthquakes');
      startAutoRefresh('usgs-earthquakes');
      
      // Load evidence count
      listEvidence().then(ev => setEvidenceCount(ev.length));
      
      recordAuditEvent('MISSION_STARTED', 'app', {
        actor: 'user',
        metadata: { mode: activeMode },
      });
    }
  }, [isInitialized]);
  
  // Handle entity selection from globe
  const handleEntitySelect = useCallback(async (entity: GeoEntity) => {
    setSelectedEntity(entity);
    setRightPanelOpen(true);
    
    await recordAuditEvent('ENTITY_SELECTED', entity.type, {
      actor: 'user',
      resourceId: entity.id,
      metadata: {
        sourceId: entity.sourceId,
        name: entity.name,
        coordinates: entity.position,
      },
    });
  }, []);
  
  // Capture evidence for selected entity
  const handleCaptureEvidence = useCallback(async () => {
    if (!selectedEntity) return;
    
    try {
      await captureEvidence(selectedEntity);
      setEvidenceCount(prev => prev + 1);
      
      await recordAuditEvent('EVIDENCE_CAPTURED', selectedEntity.type, {
        actor: 'user',
        resourceId: selectedEntity.id,
        metadata: { sourceId: selectedEntity.sourceId },
      });
      
      alert('Evidencia capturada correctamente');
    } catch (error) {
      console.error('Error capturing evidence:', error);
      alert('Error al capturar evidencia');
    }
  }, [selectedEntity]);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const saved = localStorage.getItem('god-eye-dont-show-mission');
    if (saved === 'true') setShowMission(false);
  }, []);

  const handleCoordinateChange = useCallback((lat: number, lng: number) => {
    setCoordinates({ lat, lng });
  }, []);

  const handleViewerReady = useCallback(() => {
    setGlobeReady(true);
  }, []);

  const getStatusColor = (status: ResourceStatus): string => {
    switch (status) {
      case 'active': case 'operational': return 'text-emerald-400';
      case 'notConfigured': case 'requiresConfig': return 'text-amber-400';
      case 'error': return 'text-red-400';
      case 'loading': return 'text-blue-400';
      case 'experimental': return 'text-purple-400';
      case 'comingSoon': return 'text-slate-500';
      case 'partial': return 'text-yellow-400';
      default: return 'text-slate-400';
    }
  };

  const getStatusBg = (status: ResourceStatus): string => {
    switch (status) {
      case 'active': case 'operational': return 'bg-emerald-400/10 border-emerald-400/30';
      case 'notConfigured': case 'requiresConfig': return 'bg-amber-400/10 border-amber-400/30';
      case 'error': return 'bg-red-400/10 border-red-400/30';
      case 'comingSoon': return 'bg-slate-400/10 border-slate-400/30';
      default: return 'bg-slate-400/10 border-slate-400/30';
    }
  };

  const getStatusText = (status: ResourceStatus): string => {
    return t(`status.${status}`, locale);
  };

  const categoryIcons: Record<string, React.ReactNode> = {
    dataLayers: <Layers size={16} />,
    sources: <Radio size={16} />,
    scenes: <Eye size={16} />,
    missions: <Target size={16} />,
    territory: <Navigation size={16} />,
    earthObservation: <Globe2 size={16} />,
    satellites: <Satellite size={16} />,
    fires: <Flame size={16} />,
    weather: <Cloud size={16} />,
    earthquakes: <Activity size={16} />,
    aircraft: <Plane size={16} />,
    vessels: <Ship size={16} />,
    cameras: <Camera size={16} />,
    infrastructure: <Building2 size={16} />,
    documents: <FileText size={16} />,
    evidence: <Shield size={16} />,
    alerts: <Bell size={16} />,
  };

  const categories = [
    'dataLayers', 'sources', 'earthObservation', 'satellites', 'fires',
    'weather', 'earthquakes', 'aircraft', 'vessels', 'cameras',
    'infrastructure', 'missions', 'evidence', 'alerts'
  ];

  const modes: { id: OperationalMode; label: string; icon: React.ReactNode }[] = [
    { id: 'operational', label: t('modes.operational', locale), icon: <Command size={14} /> },
    { id: 'eo', label: t('modes.eo', locale), icon: <Satellite size={14} /> },
    { id: 'osint', label: t('modes.osint', locale), icon: <Eye size={14} /> },
    { id: 'firecycle', label: t('modes.firecycle', locale), icon: <Flame size={14} /> },
    { id: 'evidence', label: t('modes.evidence', locale), icon: <Shield size={14} /> },
    { id: 'aiAnalysis', label: t('modes.aiAnalysis', locale), icon: <Brain size={14} /> },
  ];

  const missionOptions = [
    { id: 'realTime', titleKey: 'mission.options.realTimeContacts.title', descKey: 'mission.options.realTimeContacts.description', icon: <Radio size={24} />, available: true },
    { id: 'space', titleKey: 'mission.options.spaceMissions.title', descKey: 'mission.options.spaceMissions.description', icon: <Satellite size={24} />, available: true },
    { id: 'environment', titleKey: 'mission.options.environment.title', descKey: 'mission.options.environment.description', icon: <Flame size={24} />, available: true },
    { id: 'firecycle', titleKey: 'mission.options.firecycle.title', descKey: 'mission.options.firecycle.description', icon: <Zap size={24} />, available: false },
    { id: 'territorial', titleKey: 'mission.options.territorial.title', descKey: 'mission.options.territorial.description', icon: <Globe2 size={24} />, available: true },
    { id: 'intelligence', titleKey: 'mission.options.intelligence.title', descKey: 'mission.options.intelligence.description', icon: <Brain size={24} />, available: false },
  ];

  const handleMissionSelect = (id: string) => {
    setShowMission(false);
    if (id === 'firecycle') setActiveMode('firecycle');
    else if (id === 'intelligence') setActiveMode('aiAnalysis');
    else if (id === 'space') setActiveMode('eo');
    else setActiveMode('operational');
  };

  const handleDontShow = () => {
    setDontShowMission(true);
    localStorage.setItem('god-eye-dont-show-mission', 'true');
  };

  const toggleMic = () => {
    if (micState === 'deactivated') {
      setMicState('ready');
    } else {
      setMicState('deactivated');
    }
  };

  const activeCount = getActiveSourcesCount();
  const notConfiguredCount = getNotConfiguredCount();
  const keylessCount = getKeylessSourcesCount();

  return (
    <div className="h-screen w-screen flex flex-col bg-[#0a0e17] text-slate-200 overflow-hidden select-none">
      {/* TOP HEADER */}
      <header className="h-14 min-h-[56px] flex items-center px-3 bg-[#0d1320] border-b border-cyan-900/30 z-50 gap-2">
        {/* Logo & Title */}
        <div className="flex items-center gap-2 mr-4">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Globe size={18} className="text-white" />
          </div>
          <div className="hidden sm:block">
            <h1 className="text-sm font-bold text-cyan-300 tracking-wide leading-tight">GOD EYE SAE</h1>
            <p className="text-[10px] text-slate-500 leading-tight">{t('app.subtitle', locale)}</p>
          </div>
        </div>

        {/* Search */}
        <div className="flex-1 max-w-md relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={t('header.searchPlaceholder', locale)}
            className="w-full pl-9 pr-3 py-1.5 bg-[#111827] border border-slate-700/50 rounded-md text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20"
            aria-label={t('header.search', locale)}
          />
        </div>

        {/* Mode Selector */}
        <div className="hidden lg:flex items-center gap-1 ml-2">
          {modes.map(mode => (
            <button
              key={mode.id}
              onClick={() => setActiveMode(mode.id)}
              className={`flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium transition-all ${
                activeMode === mode.id
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/50'
              }`}
              title={mode.label}
            >
              {mode.icon}
              <span className="hidden xl:inline">{mode.label}</span>
            </button>
          ))}
        </div>

        {/* System Status */}
        <div className="hidden md:flex items-center gap-3 ml-3 text-[10px]">
          <div className="flex items-center gap-1">
            {globeReady ? (
              <>
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-slate-400">Cesium {t('status.operational', locale)}</span>
              </>
            ) : (
              <>
                <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                <span className="text-slate-400">Cesium {t('status.loading', locale)}</span>
              </>
            )}
          </div>
          <div className="text-slate-600">|</div>
          <span className="text-slate-500">
            {activeCount} {t('status.active', locale).toLowerCase()}
          </span>
          <div className="text-slate-600">|</div>
          <span className="text-amber-500/70">
            {notConfiguredCount} {t('status.notConfigured', locale).toLowerCase()}
          </span>
        </div>

        {/* Time */}
        <div className="hidden sm:block text-[10px] text-slate-500 ml-3 font-mono">
          {currentTime.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 ml-2">
          {/* Language */}
          <div className="relative">
            <button
              onClick={() => setShowLangMenu(!showLangMenu)}
              className="p-1.5 rounded hover:bg-slate-800/50 text-slate-400 hover:text-slate-200 text-[10px] font-medium"
              aria-label={t('header.language', locale)}
            >
              {getLocaleName(locale).substring(0, 2).toUpperCase()}
            </button>
            {showLangMenu && (
              <div className="absolute right-0 top-full mt-1 bg-[#1a2332] border border-slate-700/50 rounded-md shadow-xl z-50 overflow-hidden">
                {(['es-ES', 'en-US'] as Locale[]).map(l => (
                  <button
                    key={l}
                    onClick={() => { setLocale(l); setShowLangMenu(false); }}
                    className={`block w-full text-left px-3 py-1.5 text-xs hover:bg-slate-700/50 ${locale === l ? 'text-cyan-300' : 'text-slate-300'}`}
                  >
                    {getLocaleName(l)}
                  </button>
                ))}
              </div>
            )}
          </div>

          <button className="p-1.5 rounded hover:bg-slate-800/50 text-slate-400 hover:text-slate-200" aria-label={t('header.settings', locale)}>
            <Settings size={16} />
          </button>
          <button className="p-1.5 rounded hover:bg-slate-800/50 text-slate-400 hover:text-slate-200" aria-label={t('header.help', locale)}>
            <HelpCircle size={16} />
          </button>
          <button
            onClick={() => setShowMission(true)}
            className="p-1.5 rounded hover:bg-slate-800/50 text-slate-400 hover:text-slate-200"
            aria-label={t('mission.title', locale)}
          >
            <Command size={16} />
          </button>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* LEFT PANEL */}
        <aside
          className={`${leftPanelOpen ? 'w-64 min-w-[256px]' : 'w-0 min-w-0'} transition-all duration-300 bg-[#0d1320] border-r border-slate-800/50 overflow-hidden flex flex-col z-30`}
        >
          <div className="p-3 border-b border-slate-800/50 flex items-center justify-between">
            <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              {t('panels.resources', locale)}
            </h2>
            <button
              onClick={() => setLeftPanelOpen(false)}
              className="p-1 rounded hover:bg-slate-800/50 text-slate-500 hover:text-slate-300"
              aria-label={t('panels.collapse', locale)}
            >
              <ChevronLeft size={14} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar">
            {categories.map(cat => {
              const catResources = resources.filter(r => r.category === cat);
              const catSources = dataSources.filter(s => s.category === cat);
              const hasContent = catResources.length > 0 || catSources.length > 0;
              const isExpanded = expandedCategory === cat;

              return (
                <div key={cat} className="border-b border-slate-800/30">
                  <button
                    onClick={() => setExpandedCategory(isExpanded ? null : cat)}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs hover:bg-slate-800/30 transition-colors"
                  >
                    <span className="text-cyan-400/70">{categoryIcons[cat]}</span>
                    <span className="flex-1 text-left text-slate-300 font-medium">
                      {t(`categories.${cat}`, locale)}
                    </span>
                    {hasContent && (
                      <span className="text-[9px] text-slate-600 bg-slate-800/50 px-1.5 py-0.5 rounded">
                        {catResources.length + catSources.length}
                      </span>
                    )}
                    <ChevronRight
                      size={12}
                      className={`text-slate-600 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                    />
                  </button>

                  {isExpanded && (
                    <div className="pb-2">
                      {catResources.map(res => (
                        <button
                          key={res.id}
                          onClick={() => setSelectedResource(res.id)}
                          className={`w-full flex items-center gap-2 px-6 py-1.5 text-[11px] hover:bg-slate-800/20 transition-colors ${
                            selectedResource === res.id ? 'bg-cyan-500/5 border-l-2 border-cyan-400' : ''
                          }`}
                        >
                          <span className={`w-1.5 h-1.5 rounded-full ${
                            res.status === 'active' || res.status === 'operational' ? 'bg-emerald-400' :
                            res.status === 'comingSoon' ? 'bg-slate-600' :
                            'bg-amber-400'
                          }`} />
                          <span className="flex-1 text-left text-slate-400 truncate">{res.name}</span>
                          <span className={`text-[9px] ${getStatusColor(res.status)}`}>
                            {getStatusText(res.status)}
                          </span>
                        </button>
                      ))}
                      {catSources.map(src => (
                        <div
                          key={src.id}
                          className="flex items-center gap-2 px-6 py-1.5 text-[11px]"
                        >
                          <span className={`w-1.5 h-1.5 rounded-full ${
                            src.status === 'active' ? 'bg-emerald-400' :
                            src.status === 'notConfigured' ? 'bg-amber-400' :
                            'bg-slate-600'
                          }`} />
                          <span className="flex-1 text-left text-slate-400 truncate">{src.name}</span>
                          <span className={`text-[9px] ${getStatusColor(src.status)}`}>
                            {getStatusText(src.status)}
                          </span>
                          {src.requiresAuth && (
                            <span title="Requiere clave"><WifiOff size={9} className="text-amber-500/50" /></span>
                          )}
                        </div>
                      ))}
                      {!hasContent && (
                        <div className="px-6 py-2 text-[10px] text-slate-600 italic">
                          {t('status.comingSoon', locale)}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Panel footer with source summary */}
          <div className="p-2 border-t border-slate-800/50 text-[9px] text-slate-600">
            <div className="flex justify-between">
              <span>{keylessCount} sin clave</span>
              <span>{dataSources.length - keylessCount} requieren clave</span>
            </div>
          </div>
        </aside>

        {/* Left panel toggle when closed */}
        {!leftPanelOpen && (
          <button
            onClick={() => setLeftPanelOpen(true)}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-40 bg-[#0d1320] border border-slate-800/50 rounded-r-md p-1.5 hover:bg-slate-800/50 text-slate-400 hover:text-cyan-300"
            aria-label={t('panels.expand', locale)}
          >
            <ChevronRight size={14} />
          </button>
        )}

        {/* CENTER - GLOBE */}
        <main className="flex-1 relative overflow-hidden">
          <Globe3D 
            onCoordinateChange={handleCoordinateChange}
            onViewerReady={handleViewerReady}
            entities={getAllEntities()}
            onEntitySelect={handleEntitySelect}
          />
          
          {/* Globe overlay info */}
          <div className="absolute top-3 left-3 bg-[#0d1320]/80 backdrop-blur-sm border border-slate-700/30 rounded-md px-3 py-2 text-[10px]">
            <div className="flex items-center gap-2 text-slate-400">
              <Crosshair size={10} className="text-cyan-400" />
              <span className="font-mono">
                {coordinates.lat.toFixed(2)}°, {coordinates.lng.toFixed(2)}°
              </span>
            </div>
            <div className="flex items-center gap-2 text-slate-500 mt-0.5">
              <Globe2 size={9} />
              <span className="text-[9px]">CesiumJS · Esri World Imagery</span>
            </div>
          </div>

          {/* Mode indicator */}
          <div className="absolute top-3 right-3 bg-[#0d1320]/80 backdrop-blur-sm border border-cyan-900/30 rounded-md px-3 py-1.5">
            <span className="text-[10px] font-bold text-cyan-300 uppercase tracking-wider">
              {t(`modes.${activeMode}`, locale)}
            </span>
          </div>

          {/* Globe controls */}
          <div className="absolute bottom-16 right-3 flex flex-col gap-1">
            <button className="p-2 bg-[#0d1320]/80 backdrop-blur-sm border border-slate-700/30 rounded-md text-slate-400 hover:text-cyan-300 hover:border-cyan-500/30 transition-colors" title={t('globe.reset', locale)}>
              <Globe2 size={14} />
            </button>
            <button className="p-2 bg-[#0d1320]/80 backdrop-blur-sm border border-slate-700/30 rounded-md text-slate-400 hover:text-cyan-300 hover:border-cyan-500/30 transition-colors" title={t('globe.north', locale)}>
              <Navigation size={14} />
            </button>
          </div>

          {/* Upstream attribution */}
          <div className="absolute bottom-2 left-3 text-[8px] text-slate-600">
            Motor: CesiumJS · Basado en God's Eye View (MIT) · bilawalsidhu/gods-eye-view
          </div>
        </main>

        {/* RIGHT PANEL - Context Inspector */}
        <aside
          className={`${rightPanelOpen ? 'w-72 min-w-[288px]' : 'w-0 min-w-0'} transition-all duration-300 bg-[#0d1320] border-l border-slate-800/50 overflow-hidden flex flex-col z-30`}
        >
          <div className="p-3 border-b border-slate-800/50 flex items-center justify-between">
            <h2 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              {t('panels.context', locale)}
            </h2>
            <button
              onClick={() => setRightPanelOpen(false)}
              className="p-1 rounded hover:bg-slate-800/50 text-slate-500 hover:text-slate-300"
              aria-label={t('panels.collapse', locale)}
            >
              <ChevronRight size={14} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar p-3">
            {!selectedEntity ? (
              <div className="flex flex-col items-center justify-center h-full text-center px-4">
                <MapPin size={32} className="text-slate-700 mb-3" />
                <p className="text-xs text-slate-500 mb-1">{t('context.noSelection', locale)}</p>
                <p className="text-[10px] text-slate-600">{t('context.selectHint', locale)}</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Selected Object */}
                <section>
                  <h3 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
                    {t('context.selectedObject', locale)}
                  </h3>
                  <div className="bg-slate-800/30 rounded-md p-2.5 border border-slate-700/30">
                    <p className="text-xs text-slate-200 font-medium">
                      {selectedEntity.name || selectedEntity.type}
                    </p>
                    <p className="text-[10px] text-slate-500 mt-0.5">
                      Tipo: {selectedEntity.type} {selectedEntity.subtype && `(${selectedEntity.subtype})`}
                    </p>
                  </div>
                </section>

                {/* Source */}
                <section>
                  <h3 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
                    {t('context.source', locale)}
                  </h3>
                  <div className="bg-slate-800/30 rounded-md p-2.5 border border-slate-700/30">
                    <p className="text-xs text-slate-300">
                      {selectedEntity.provenance.sourceName}
                    </p>
                    {selectedEntity.provenance.sourceUrl && (
                      <a 
                        href={selectedEntity.provenance.sourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[10px] text-cyan-400 hover:text-cyan-300 underline mt-1 block"
                      >
                        Abrir fuente original
                      </a>
                    )}
                  </div>
                </section>

                {/* Coordinates */}
                <section>
                  <h3 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
                    {t('context.coordinates', locale)}
                  </h3>
                  <div className="bg-slate-800/30 rounded-md p-2.5 border border-slate-700/30 font-mono text-[11px] text-cyan-300/80">
                    <div>LAT {selectedEntity.position.latitude.toFixed(4)}°</div>
                    <div>LNG {selectedEntity.position.longitude.toFixed(4)}°</div>
                    {selectedEntity.position.altitude && (
                      <div>ALT {selectedEntity.position.altitude.toFixed(0)}m</div>
                    )}
                  </div>
                </section>

                {/* Timestamp */}
                <section>
                  <h3 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
                    {t('context.dateTime', locale)}
                  </h3>
                  <div className="bg-slate-800/30 rounded-md p-2.5 border border-slate-700/30">
                    <p className="text-[10px] text-slate-400 font-mono">
                      {new Date(selectedEntity.timestamp).toLocaleString('es-ES')}
                    </p>
                  </div>
                </section>

                {/* Properties */}
                <section>
                  <h3 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
                    {t('context.metadata', locale)}
                  </h3>
                  <div className="bg-slate-800/30 rounded-md p-2.5 border border-slate-700/30">
                    {Object.entries(selectedEntity.properties).slice(0, 8).map(([key, value]) => (
                      <div key={key} className="flex justify-between text-[10px] py-0.5">
                        <span className="text-slate-500">{key}:</span>
                        <span className="text-slate-300 font-mono max-w-[120px] truncate">
                          {typeof value === 'number' ? value.toFixed(2) : String(value || '—')}
                        </span>
                      </div>
                    ))}
                  </div>
                </section>

                {/* Evidence */}
                <section>
                  <h3 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
                    {t('context.evidence', locale)}
                  </h3>
                  <div className="bg-slate-800/30 rounded-md p-2.5 border border-slate-700/30">
                    <p className="text-[10px] text-slate-500">
                      {evidenceCount > 0 
                        ? `${evidenceCount} evidencias registradas`
                        : t('evidence.noEvidence', locale)
                      }
                    </p>
                  </div>
                </section>

                {/* Actions */}
                <section>
                  <h3 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
                    {t('context.actions', locale)}
                  </h3>
                  <div className="flex flex-wrap gap-1.5">
                    <button 
                      onClick={handleCaptureEvidence}
                      className="flex items-center gap-1 px-2 py-1 bg-cyan-500/10 border border-cyan-500/30 rounded text-[10px] text-cyan-300 hover:bg-cyan-500/20 transition-colors"
                    >
                      <Shield size={10} /> Capturar evidencia
                    </button>
                    <button className="flex items-center gap-1 px-2 py-1 bg-slate-700/30 border border-slate-600/30 rounded text-[10px] text-slate-400 hover:bg-slate-700/50 transition-colors">
                      <Download size={10} /> Exportar
                    </button>
                  </div>
                </section>
              </div>
            )}
          </div>
        </aside>

        {/* Right panel toggle when closed */}
        {!rightPanelOpen && (
          <button
            onClick={() => setRightPanelOpen(true)}
            className="absolute right-0 top-1/2 -translate-y-1/2 z-40 bg-[#0d1320] border border-slate-800/50 rounded-l-md p-1.5 hover:bg-slate-800/50 text-slate-400 hover:text-cyan-300"
            aria-label={t('panels.expand', locale)}
          >
            <ChevronLeft size={14} />
          </button>
        )}
      </div>

      {/* BOTTOM TOOLBAR */}
      <footer className="h-12 min-h-[48px] bg-[#0d1320] border-t border-cyan-900/30 flex items-center px-3 gap-1 z-50">
        <div className="flex items-center gap-1 flex-1">
          {[
            { icon: <MapPin size={14} />, label: t('tools.location', locale), active: false },
            { icon: <Clock size={14} />, label: t('tools.timeline', locale), active: false },
            { icon: <BarChart3 size={14} />, label: t('tools.compare', locale), active: false },
            { icon: <Ruler size={14} />, label: t('tools.measure', locale), active: false },
            { icon: <Shield size={14} />, label: t('tools.captureEvidence', locale), active: false },
            { icon: <Download size={14} />, label: t('tools.export', locale), active: false },
          ].map((tool, i) => (
            <button
              key={i}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded text-[10px] transition-all ${
                tool.active
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/50'
              }`}
              title={tool.label}
            >
              {tool.icon}
              <span className="hidden md:inline">{tool.label}</span>
            </button>
          ))}
        </div>

        {/* Microphone / AI Assistant */}
        <div className="flex items-center gap-2 ml-2 border-l border-slate-800/50 pl-2">
          <button
            onClick={toggleMic}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded text-[10px] transition-all ${
              micState !== 'deactivated'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/50'
            }`}
            title={t('microphone.title', locale)}
          >
            {micState !== 'deactivated' ? <Mic size={14} /> : <MicOff size={14} />}
            <span className="hidden md:inline">{t('tools.microphone', locale)}</span>
          </button>

          <button
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded text-[10px] text-slate-500 hover:text-slate-300 hover:bg-slate-800/50 transition-all"
            title={t('tools.aiAgent', locale)}
          >
            <Bot size={14} />
            <span className="hidden md:inline">{t('tools.aiAgent', locale)}</span>
          </button>

          <button
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded text-[10px] text-slate-500 hover:text-slate-300 hover:bg-slate-800/50 transition-all"
            title={t('tools.presets', locale)}
          >
            <Palette size={14} />
            <span className="hidden md:inline">{t('tools.presets', locale)}</span>
          </button>

          <button
            onClick={() => setShowFoundationModel(!showFoundationModel)}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded text-[10px] transition-all ${
              showFoundationModel
                ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/50'
            }`}
            title="Foundation Model"
          >
            <Brain size={14} />
            <span className="hidden md:inline">AI Model</span>
          </button>
        </div>

        {/* Coordinates display */}
        <div className="hidden sm:flex items-center gap-3 ml-3 border-l border-slate-800/50 pl-3 text-[10px] font-mono text-slate-500">
          <span>LAT {coordinates.lat.toFixed(2)}°</span>
          <span>LNG {coordinates.lng.toFixed(2)}°</span>
        </div>
      </footer>

      {/* FOUNDATION MODEL PANEL */}
      {showFoundationModel && (
        <div className="fixed bottom-14 left-3 z-50 w-80 max-h-[70vh] overflow-y-auto custom-scrollbar">
          <FoundationModelPanel />
        </div>
      )}

      {/* MISSION MODAL */}
      {showMission && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-[#0d1320] border border-cyan-900/30 rounded-xl shadow-2xl shadow-cyan-500/5 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-800/50">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-cyan-300">{t('mission.title', locale)}</h2>
                  <p className="text-xs text-slate-500 mt-0.5">{t('mission.subtitle', locale)}</p>
                </div>
                <button
                  onClick={() => setShowMission(false)}
                  className="p-1.5 rounded hover:bg-slate-800/50 text-slate-500 hover:text-slate-300"
                  aria-label={t('mission.close', locale)}
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
              </div>
            </div>

            <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
              {missionOptions.map(option => (
                <button
                  key={option.id}
                  onClick={() => handleMissionSelect(option.id)}
                  disabled={!option.available}
                  className={`flex flex-col items-start p-4 rounded-lg border text-left transition-all ${
                    option.available
                      ? 'bg-slate-800/30 border-slate-700/40 hover:border-cyan-500/40 hover:bg-slate-800/50 hover:shadow-lg hover:shadow-cyan-500/5'
                      : 'bg-slate-900/30 border-slate-800/30 opacity-50 cursor-not-allowed'
                  }`}
                >
                  <div className={`mb-2 ${option.available ? 'text-cyan-400' : 'text-slate-600'}`}>
                    {option.icon}
                  </div>
                  <h3 className={`text-xs font-bold mb-1 ${option.available ? 'text-slate-200' : 'text-slate-500'}`}>
                    {t(option.titleKey, locale)}
                  </h3>
                  <p className="text-[10px] text-slate-500 leading-relaxed">
                    {t(option.descKey, locale)}
                  </p>
                  {!option.available && (
                    <span className="mt-2 text-[9px] text-amber-500/70 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                      {t('status.comingSoon', locale)}
                    </span>
                  )}
                </button>
              ))}
            </div>

            <div className="p-4 border-t border-slate-800/50 flex items-center justify-between">
              <label className="flex items-center gap-2 text-[10px] text-slate-500 cursor-pointer">
                <input
                  type="checkbox"
                  checked={dontShowMission}
                  onChange={(e) => {
                    setDontShowMission(e.target.checked);
                    if (e.target.checked) handleDontShow();
                  }}
                  className="w-3 h-3 rounded border-slate-600 bg-slate-800 text-cyan-500 focus:ring-cyan-500/30"
                />
                {t('mission.dontShowAgain', locale)}
              </label>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowMission(false)}
                  className="px-3 py-1.5 text-[10px] text-slate-400 hover:text-slate-200 rounded border border-slate-700/50 hover:border-slate-600 transition-colors"
                >
                  {t('mission.help', locale)}
                </button>
                <button
                  onClick={() => { setShowMission(false); setActiveMode('operational'); }}
                  className="px-4 py-1.5 text-[10px] font-medium text-cyan-300 bg-cyan-500/10 border border-cyan-500/30 rounded hover:bg-cyan-500/20 transition-colors"
                >
                  {t('mission.close', locale)}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
