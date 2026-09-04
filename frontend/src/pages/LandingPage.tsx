import React, { useEffect } from 'react';
import type { NavigationTab } from '../types';

interface LandingPageProps {
  onNavigate: (tab: NavigationTab) => void;
}

const HeroSection: React.FC<{ onNavigate: (tab: NavigationTab) => void }> = ({ onNavigate }) => {
  return (
    <section className="relative w-full min-h-[85vh] flex items-center justify-center pt-24 pb-16 overflow-hidden">
      <div className="max-w-[1400px] w-full px-6 lg:px-12 flex flex-col lg:flex-row items-center gap-16 relative z-10">
        
        {/* LEFT: Content */}
        <div className="w-full lg:w-[50%] flex flex-col items-start z-20">
          <div className="flex items-center gap-2 mb-8">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_8px_rgba(34,211,238,0.8)]" />
            <span className="font-mono text-[11px] font-bold text-slate-300 uppercase tracking-widest">
              SYSTEM ONLINE • MULTIMODAL REMOTE SENSING
            </span>
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-[4.5rem] font-bold text-white leading-[1.05] tracking-tight mb-6 max-w-[650px]">
            TURN SATELLITE<br/>
            IMAGERY INTO<br/>
            <span className="text-cyan-400">GROUNDED INTELLIGENCE.</span>
          </h1>

          <p className="text-[17px] text-slate-400 font-sans leading-relaxed mb-10 max-w-[600px] font-normal">
            SatQuery AI routes remote-sensing queries to the right specialist model, combines visual evidence, and returns an auditable, grounded answer.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-4 mb-12 w-full sm:w-auto">
            <button
              onClick={() => onNavigate('workspace')}
              className="w-full sm:w-auto px-8 h-[50px] rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-mono font-bold text-[13px] tracking-wider uppercase transition-all flex items-center justify-center gap-2"
            >
              ENTER DASHBOARD →
            </button>
            <button
              onClick={() => onNavigate('about')}
              className="w-full sm:w-auto px-8 h-[50px] rounded-xl bg-transparent hover:bg-white/[0.02] border border-white/10 hover:border-white/20 text-white font-mono font-bold text-[13px] tracking-wider uppercase transition-all flex items-center justify-center"
            >
              EXPLORE ARCHITECTURE
            </button>
          </div>

          {/* Micro-metadata */}
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 font-mono text-[10px] text-slate-500 uppercase tracking-widest">
            <span>OPTICAL</span>
            <span>SAR</span>
            <span>BI-TEMPORAL</span>
            <span>GROUNDING</span>
            <span className="text-cyan-500/80">EVIDENCE-GROUNDED</span>
          </div>
        </div>

        {/* RIGHT: Visual */}
        <div className="w-full lg:w-[50%] relative h-[600px] flex items-center justify-center">
          <div className="absolute inset-0 bg-[#050b18] rounded-[2rem] border border-white/5 overflow-hidden shadow-2xl">
            {/* Abstract Satellite Texture */}
            <div className="absolute inset-0 opacity-[0.25] bg-[url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop')] bg-cover bg-center mix-blend-luminosity" />
            <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
            
            {/* Bounding boxes & markers */}
            <div className="absolute top-[30%] left-[20%] w-[120px] h-[80px] border border-cyan-400/50 bg-cyan-400/10" />
            <div className="absolute top-[30%] left-[20%] w-2 h-2 bg-cyan-400 -mt-1 -ml-1" />
            
            <div className="absolute top-[60%] right-[30%] w-[90px] h-[90px] border border-emerald-400/50 bg-emerald-400/10" />
            <div className="absolute top-[60%] right-[30%] w-2 h-2 bg-emerald-400 -mt-1 -ml-1" />

            <div className="absolute top-6 left-6 font-mono text-[10px] text-slate-400">
              37.7749° N, 122.4194° W<br/>
              ALT: 500KM LEO
            </div>

            {/* Floating Cards */}
            <div className="absolute top-12 right-12 p-4 bg-[#030712]/90 backdrop-blur-md border border-white/10 rounded-xl flex flex-col gap-3 shadow-xl">
              <div>
                <div className="font-mono text-[9px] text-slate-500 uppercase tracking-widest mb-1">MODEL</div>
                <div className="font-mono text-xs text-white font-bold">RS SPECIALIST</div>
              </div>
              <div className="flex gap-6">
                <div>
                  <div className="font-mono text-[9px] text-slate-500 uppercase tracking-widest mb-1">CONFIDENCE</div>
                  <div className="font-mono text-xs text-emerald-400 font-bold">92%</div>
                </div>
                <div>
                  <div className="font-mono text-[9px] text-slate-500 uppercase tracking-widest mb-1">MODE</div>
                  <div className="font-mono text-xs text-cyan-400 font-bold">BI-TEMPORAL</div>
                </div>
              </div>
            </div>

            <div className="absolute bottom-12 left-12 p-3 px-4 bg-[#030712]/90 backdrop-blur-md border border-white/10 rounded-xl shadow-xl">
              <div className="font-mono text-[9px] text-slate-500 uppercase tracking-widest mb-1">ROUTER</div>
              <div className="font-mono text-xs text-white font-bold">CHANGE DETECTION</div>
            </div>

          </div>
        </div>

      </div>
    </section>
  );
};

const TrustStrip: React.FC = () => {
  return (
    <div className="w-full py-12 border-t border-b border-white/[0.05] bg-[#030712]/50">
      <div className="max-w-[1400px] mx-auto px-6 lg:px-12">
        <h3 className="font-mono text-[10px] font-bold text-slate-500 tracking-[0.2em] uppercase mb-8 text-center">
          BUILT FOR CONTROLLED REMOTE-SENSING ANALYSIS
        </h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 text-center">
          {[
            { num: '01', title: 'SPECIALIST ROUTING' },
            { num: '02', title: 'MULTIMODAL ANALYSIS' },
            { num: '03', title: 'EVIDENCE-GROUNDED' },
            { num: '04', title: 'AUDITABLE EXECUTION' },
          ].map((item, idx) => (
            <div key={idx} className="flex flex-col items-center">
              <span className="font-mono text-sm font-bold text-cyan-500/50 mb-2">{item.num}</span>
              <span className="font-mono text-xs font-bold text-slate-300 tracking-wider uppercase">{item.title}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const HowItWorks: React.FC = () => {
  const steps = [
    { num: '01', title: 'UPLOAD', desc: 'Imagery validation' },
    { num: '02', title: 'UNDERSTAND', desc: 'Query + configuration' },
    { num: '03', title: 'ROUTE', desc: 'Specialist selection' },
    { num: '04', title: 'ANALYZE', desc: 'Task-specific inference' },
    { num: '05', title: 'VERIFY', desc: 'Evidence + confidence' },
  ];

  return (
    <section className="py-32 px-6 lg:px-12 max-w-[1400px] mx-auto text-center flex flex-col items-center">
      <div className="mb-20">
        <h2 className="text-3xl lg:text-4xl font-bold text-white tracking-tight mb-4">
          FROM IMAGERY<br />TO INTELLIGENCE.
        </h2>
        <p className="text-slate-400 font-sans text-sm max-w-md mx-auto">
          A controlled execution pipeline connects the user's query to the right remote-sensing specialist.
        </p>
      </div>

      <div className="w-full flex flex-col lg:flex-row items-center justify-between relative gap-8 lg:gap-0">
        <div className="hidden lg:block absolute top-[1.25rem] left-[10%] right-[10%] h-[1px] bg-white/[0.1]" />
        
        {steps.map((step, idx) => (
          <div key={idx} className="flex flex-col items-center flex-1 relative group">
            <div className="w-10 h-10 rounded-full bg-[#030712] border border-white/20 flex items-center justify-center mb-6 relative z-10">
              <span className="font-mono text-xs font-bold text-slate-400">{step.num}</span>
            </div>
            <h4 className="font-mono text-xs font-bold text-white uppercase tracking-wider mb-2">
              {step.title}
            </h4>
            <p className="text-[13px] text-slate-500 font-sans">{step.desc}</p>
            
            {idx < steps.length - 1 && (
              <div className="lg:hidden font-bold text-cyan-500/30 my-4">↓</div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
};

const AnalysisModes: React.FC<{ onNavigate: (tab: NavigationTab) => void }> = ({ onNavigate }) => {
  const modes = [
    {
      num: '01', label: 'MODE', title: 'SINGLE SCENE',
      desc: 'Analyze a single optical or SAR image. Capabilities include VQA, Captioning, and Grounding.'
    },
    {
      num: '02', label: 'MODE', title: 'GROUNDING',
      desc: 'Ask natural-language questions and locate relevant regions directly in the imagery.'
    },
    {
      num: '03', label: 'MODE', title: 'OPTICAL + SAR',
      desc: 'Combine complementary optical and radar information into a single fused inference.'
    },
    {
      num: '04', label: 'MODE', title: 'BI-TEMPORAL CHANGE',
      desc: 'Compare imagery across two time points and describe structurally detected changes.'
    }
  ];

  return (
    <section className="py-32 px-6 lg:px-12 max-w-[1400px] mx-auto bg-[#050b18]/50 rounded-[2rem] border border-white/[0.02]">
      <h2 className="text-3xl lg:text-4xl font-bold text-white tracking-tight mb-16 text-center lg:text-left">
        ONE WORKSPACE.<br />
        <span className="text-slate-500">FOUR ANALYSIS MODES.</span>
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {modes.map((mode, i) => (
          <div key={i} onClick={() => onNavigate('workspace')} className="group p-8 rounded-2xl bg-white/[0.02] border border-white/5 hover:-translate-y-1 hover:border-white/10 hover:bg-white/[0.04] transition-all duration-300 cursor-pointer flex flex-col justify-between min-h-[220px]">
            <div className="flex justify-between items-start mb-6">
              <span className="font-mono text-[10px] font-bold text-cyan-500 uppercase tracking-widest">{mode.label} {mode.num}</span>
              <div className="w-8 h-8 rounded border border-white/10 bg-[#030712] flex items-center justify-center opacity-50 group-hover:opacity-100 transition-opacity">
                <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full group-hover:scale-150 transition-transform" />
              </div>
            </div>
            <div>
              <h3 className="text-xl font-bold text-white mb-3 tracking-tight group-hover:text-cyan-300 transition-colors">{mode.title}</h3>
              <p className="text-[14px] text-slate-400 font-sans leading-relaxed">{mode.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

const RoutingVisual: React.FC = () => {
  return (
    <section className="py-32 px-6 lg:px-12 max-w-[1400px] mx-auto text-center">
      <h2 className="text-3xl lg:text-4xl font-bold text-white tracking-tight mb-20">
        THE RIGHT MODEL.<br />
        <span className="text-slate-500">FOR THE RIGHT QUESTION.</span>
      </h2>

      <div className="flex flex-col items-center font-mono text-[11px] font-bold tracking-widest uppercase gap-3">
        <div className="px-6 py-3 border border-white/10 rounded-lg text-white">USER QUERY</div>
        <div className="text-cyan-500/50">↓</div>
        <div className="px-6 py-3 border border-white/10 rounded-lg text-slate-300">QUERY INTERPRETATION</div>
        <div className="text-cyan-500/50">↓</div>
        <div className="px-6 py-3 border border-cyan-500/40 rounded-lg text-cyan-300 bg-cyan-950/20">DETERMINISTIC ROUTER</div>
        <div className="text-cyan-500/50">↓</div>
        <div className="px-6 py-3 border border-white/10 rounded-lg text-slate-300">SPECIALIST MODEL</div>
        
        <div className="w-[1px] h-6 bg-cyan-500/50" />
        <div className="w-[280px] sm:w-[400px] h-[1px] bg-cyan-500/50" />
        <div className="flex justify-between w-[280px] sm:w-[400px]">
          <div className="w-[1px] h-6 bg-cyan-500/50" />
          <div className="w-[1px] h-6 bg-cyan-500/50" />
          <div className="w-[1px] h-6 bg-cyan-500/50" />
          <div className="w-[1px] h-6 bg-cyan-500/50" />
        </div>
        
        <div className="flex justify-between w-[320px] sm:w-[440px] text-[9px] text-slate-400">
          <div className="w-16 text-center">VQA</div>
          <div className="w-16 text-center">GROUNDING</div>
          <div className="w-16 text-center">OPT + SAR</div>
          <div className="w-16 text-center">CHANGE DETECT</div>
        </div>

        <div className="text-cyan-500/50 mt-4">↓</div>
        <div className="px-6 py-3 border border-white/10 rounded-lg text-slate-300">EVIDENCE SYNTHESIS</div>
        <div className="text-cyan-500/50">↓</div>
        <div className="px-6 py-3 border border-emerald-500/40 rounded-lg text-emerald-400 bg-emerald-950/20">GROUNDED ANSWER</div>
      </div>
    </section>
  );
};

const EvidenceSection: React.FC = () => {
  return (
    <section className="py-32 px-6 lg:px-12 max-w-[1400px] mx-auto border-t border-white/[0.05]">
      <div className="flex flex-col lg:flex-row items-center gap-16">
        <div className="lg:w-1/2">
          <h2 className="text-3xl lg:text-4xl font-bold text-white tracking-tight mb-6">
            BUILT FOR EVIDENCE.
          </h2>
          <p className="text-[17px] text-slate-400 font-sans leading-relaxed max-w-md">
            Responses are inherently tied to visual evidence, specialist outputs, and execution metadata. Never trust a black box.
          </p>
        </div>

        <div className="lg:w-1/2 w-full flex justify-center lg:justify-end">
          <div className="w-full max-w-md bg-[#050b18] border border-white/10 rounded-2xl p-8 shadow-2xl">
            <h4 className="font-mono text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-6">ANALYSIS RESULT (DEMO)</h4>
            
            <div className="space-y-4 font-mono text-[11px] lg:text-xs">
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-slate-400">Confidence</span>
                <span className="text-emerald-400 font-bold">92%</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-slate-400">Specialist</span>
                <span className="text-white">Change Detection</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-slate-400">Evidence</span>
                <span className="text-cyan-400">3 regions detected</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-slate-400">Execution</span>
                <span className="text-white">7 steps completed</span>
              </div>
              <div className="flex justify-between pt-1">
                <span className="text-slate-400">Status</span>
                <span className="text-emerald-400 font-bold">Verified</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

const ExecutionTrace: React.FC = () => {
  const steps = [
    { label: 'INPUT VALIDATION', time: '0.01s' },
    { label: 'CONFIGURATION DETECTION', time: '0.04s' },
    { label: 'INTENT DETECTION', time: '0.12s' },
    { label: 'SPECIALIST SELECTION', time: '0.15s' },
    { label: 'MODEL EXECUTION', time: '1.42s' },
    { label: 'EVIDENCE SYNTHESIS', time: '1.58s' },
    { label: 'CONFIDENCE CALCULATION', time: '1.61s' },
    { label: 'RESULT READY', time: '1.65s' },
  ];

  return (
    <section className="py-32 px-6 lg:px-12 max-w-[1400px] mx-auto text-center">
      <h2 className="text-3xl lg:text-4xl font-bold text-white tracking-tight mb-16">
        WATCH THE INTELLIGENCE FLOW.
      </h2>

      <div className="max-w-2xl mx-auto bg-[#030712] border border-white/10 rounded-2xl p-8 lg:p-12 text-left shadow-2xl">
        <div className="space-y-6 font-mono text-[11px] lg:text-xs">
          {steps.map((step, i) => (
            <div key={i} className="flex items-center gap-4">
              <span className="text-emerald-400">✓</span>
              <span className="text-white font-bold">{step.label}</span>
              <span className="text-slate-600 ml-auto">{step.time}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const SatelliteVisualization: React.FC = () => {
  return (
    <section className="py-32 px-6 lg:px-12 max-w-[1400px] mx-auto border-y border-white/[0.05]">
      <div className="relative w-full h-[500px] lg:h-[700px] bg-[#050b18] border border-white/5 rounded-[2rem] overflow-hidden shadow-2xl">
        <div className="absolute inset-0 opacity-[0.4] bg-[url('https://images.unsplash.com/photo-1542224566-6e85f2e6772f?q=80&w=2000&auto=format&fit=crop')] bg-cover bg-center mix-blend-luminosity" />
        <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)', backgroundSize: '60px 60px' }} />
        
        <div className="absolute top-[40%] left-[30%] w-[150px] h-[100px] border-2 border-rose-500/50 bg-rose-500/10 flex items-end p-2">
          <span className="font-mono text-[9px] text-rose-400 bg-[#030712]/80 px-1">CHANGE: -12%</span>
        </div>

        <div className="absolute top-[20%] right-[20%] w-[80px] h-[80px] border-2 border-cyan-400/50 bg-cyan-400/10 flex items-end p-2">
          <span className="font-mono text-[9px] text-cyan-400 bg-[#030712]/80 px-1">OBJ: VEHICLE</span>
        </div>

        <div className="absolute bottom-8 left-8 flex gap-8">
          <div>
            <div className="font-mono text-[9px] text-slate-400 tracking-widest mb-1">SENSOR</div>
            <div className="font-mono text-xs text-white">MULTISPECTRAL</div>
          </div>
          <div>
            <div className="font-mono text-[9px] text-slate-400 tracking-widest mb-1">GSD</div>
            <div className="font-mono text-xs text-white">0.5 m/px</div>
          </div>
          <div className="hidden sm:block">
            <div className="font-mono text-[9px] text-slate-400 tracking-widest mb-1">CRS</div>
            <div className="font-mono text-xs text-white">EPSG:4326</div>
          </div>
          <div className="hidden md:block">
            <div className="font-mono text-[9px] text-slate-400 tracking-widest mb-1">MODE</div>
            <div className="font-mono text-xs text-cyan-400">OPTICAL + SAR</div>
          </div>
        </div>
      </div>
    </section>
  );
};

const Differentiation: React.FC = () => {
  return (
    <section className="py-32 px-6 lg:px-12 max-w-[1400px] mx-auto">
      <h2 className="text-3xl lg:text-4xl font-bold text-white tracking-tight mb-16 max-w-lg">
        NOT ANOTHER<br />
        <span className="text-slate-500">REMOTE-SENSING CHATBOT.</span>
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-12 lg:gap-16">
        {[
          { title: 'BOUNDED EXECUTION', desc: 'Controlled execution graph instead of uncontrolled agent loops.' },
          { title: 'SPECIALIST ROUTING', desc: 'Different tasks go to appropriate specialist models.' },
          { title: 'EVIDENCE-GROUNDED', desc: 'Answers are tied to visual/model evidence.' },
          { title: 'AUDITABLE', desc: 'Routing and execution steps can be fully inspected.' },
        ].map((item, i) => (
          <div key={i}>
            <h3 className="font-mono text-[11px] font-bold text-cyan-500 uppercase tracking-widest mb-3">{item.title}</h3>
            <p className="text-[15px] text-slate-400 font-sans leading-relaxed">{item.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
};

const FinalCTA: React.FC<{ onNavigate: (tab: NavigationTab) => void }> = ({ onNavigate }) => {
  return (
    <section className="py-40 px-6 lg:px-12 flex flex-col items-center text-center">
      <h2 className="text-4xl lg:text-5xl font-bold text-white tracking-tight mb-6">
        READY TO ANALYZE<br />THE EARTH?
      </h2>
      <p className="text-[16px] text-slate-400 font-sans mb-12 max-w-lg">
        Upload satellite imagery, ask a question, and let SatQuery AI route the analysis.
      </p>
      
      <div className="flex flex-col items-center gap-4 w-full sm:w-auto">
        <button 
          onClick={() => onNavigate('workspace')}
          className="w-full sm:w-auto px-8 h-[50px] rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-mono font-bold text-[13px] tracking-wider uppercase transition-all flex items-center justify-center"
        >
          ENTER THE DASHBOARD →
        </button>
        <button 
          onClick={() => onNavigate('about')}
          className="text-[12px] font-mono font-bold text-slate-400 hover:text-white uppercase tracking-widest transition-colors mt-2"
        >
          VIEW ARCHITECTURE
        </button>
      </div>
    </section>
  );
};

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="landing-page w-full min-h-screen bg-[#030712] text-slate-200 font-sans selection:bg-cyan-500/30 selection:text-cyan-100 flex flex-col">
      <HeroSection onNavigate={onNavigate} />
      <TrustStrip />
      <HowItWorks />
      <AnalysisModes onNavigate={onNavigate} />
      <RoutingVisual />
      <EvidenceSection />
      <ExecutionTrace />
      <SatelliteVisualization />
      <Differentiation />
      <FinalCTA onNavigate={onNavigate} />
    </div>
  );
};
