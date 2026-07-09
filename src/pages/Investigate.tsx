import { Search, Send, Loader2, CheckCircle2, Circle, AlertTriangle, X, ExternalLink, Clock } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Slider } from "@/components/ui/slider";

interface StageState { stage: string; status: "pending" | "running" | "done"; }
interface ArtData { title: string; url: string; source_domain: string; body: string; error: string|null; claims: Array<{text:string;entities:string[]}>; framing_score: number|null; }
interface CanClaim { text: string; source_count: number; variants: Array<{source:string;article:string;text:string}>; }
interface ConClaim { claim_text: string; source_count: number; t1t2_reporting: number; pool_size: number; pct: number; threshold: number; would_absorb: boolean; would_need_for_absorption: string; }
interface Stored { query: string; timestamp: number; totalMs: number|null; articles: ArtData[]; canonicalClaims: CanClaim[]; consensusClaims: ConClaim[]; }

const STAGES = ["search","fetch","embed","extract","match","consensus"];
const PRESETS = ["Iran deal","Venezuela earthquake","Anthropic export ban"];
const LS_KEY = "nn_investigate_history";
const MAX_HIST = 20;

function sl(s:string):string{const m:Record<string,string>={search:"Search",fetch:"Fetch",embed:"Embed",extract:"Extract",match:"Match",consensus:"Consensus"};return m[s]||s;}
function rtime(ts:number):string{const d=Math.round((Date.now()-ts)/1000);if(d<60)return"just now";if(d<3600)return Math.round(d/60)+" min ago";if(d<86400)return Math.round(d/3600)+" hr ago";return new Date(ts).toLocaleDateString();}
function recomp(cs:ConClaim[],t:number):ConClaim[]{return cs.map(c=>({...c,threshold:t,would_absorb:c.t1t2_reporting>=2&&c.pool_size>0&&(c.t1t2_reporting/c.pool_size*100)>=t}));}
function loadH():Stored[]{try{const r=localStorage.getItem(LS_KEY);return r?JSON.parse(r):[];}catch{return[];}}
function saveH(e:Stored[]){try{localStorage.setItem(LS_KEY,JSON.stringify(e.slice(-MAX_HIST)));}catch{}}

export default function InvestigatePage() {
  const [q,setQ]=useState(""); const [running,setR]=useState(false);
  const [stages,setSt]=useState<StageState[]>(STAGES.map(s=>({stage:s,status:"pending"})));
  const [arts,setArts]=useState<ArtData[]>([]); const [_canons,setCanons]=useState<CanClaim[]>([]);
  const [cons,setCons]=useState<ConClaim[]>([]); const [warn,setWarn]=useState<string|null>(null);
  const [err,setErr]=useState<string|null>(null); const [sTimes,setSTimes]=useState<Record<string,number>>({});
  const [_totalMs,setT]=useState<number|null>(null); const [threshold,setTh]=useState(65);
  const [qRan,setQRan]=useState(""); const [cachedAt,setCAt]=useState<number|null>(null);
  const [history,setHist]=useState<Stored[]>(loadH);
  const abortRef=useRef<AbortController|null>(null); const timesRef=useRef<Record<string,number>>({});
  const adjCons=useMemo(()=>recomp(cons,threshold),[cons,threshold]);
  const allDone=stages.every(s=>s.status==="done")&&!running;
  const showBadge=stages.some(s=>s.status==="running");
  useEffect(()=>{return()=>{if(abortRef.current)abortRef.current.abort();};},[]);
  const upStage=useCallback((s:string,st:"pending"|"running"|"done")=>{setSt(p=>p.map(x=>x.stage===s?{...x,status:st}:x));},[]);

  const runQ=useCallback(async(t0:string)=>{const t=t0.trim();if(!t||running)return;
    if(abortRef.current)abortRef.current.abort();const ctrl=new AbortController();abortRef.current=ctrl;
    setR(true);setErr(null);setWarn(null);setArts([]);setCanons([]);setCons([]);
    setSt(STAGES.map(s=>({stage:s,status:"pending"})));timesRef.current={};setSTimes({});setT(null);setCAt(null);setQRan(t);
    const arts0:ArtData[]=[];const seen=new Set<string>();let c0:CanClaim[]=[];let co0:ConClaim[]=[];let re:string|null=null;let tms:number|null=null;
    try{
      const resp=await fetch("/api/investigate/stream",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query:t}),signal:ctrl.signal});
      if(!resp.ok||!resp.body){setErr("Backend error. Try again.");setR(false);return;}
      const reader=resp.body.getReader();const dec=new TextDecoder();let buf="";
      while(true){const{ done,value}=await reader.read();if(done)break;buf+=dec.decode(value,{stream:true});
      const lines=buf.split("\n");buf=lines.pop()||"";let en="";
      for(const ln of lines){
        if(ln.startsWith("event: "))en=ln.slice(7).trim();
        else if(ln.startsWith("data: ")){try{const d=JSON.parse(ln.slice(6));const now=performance.now();
        switch(en){
        case"stage_start":upStage(d.stage,"running");timesRef.current[d.stage]=now;break;
        case"search_result":upStage("search","done");timesRef.current.search=now-(timesRef.current.search||now);
          for(const u of(d.urls||[])){if(!seen.has(u.url)){seen.add(u.url);arts0.push({title:u.title,url:u.url,source_domain:u.source_domain,body:"",claims:[],framing_score:null,error:null});}}setArts([...arts0]);break;
        case"fetch_progress":upStage("fetch","running");
          const fu=arts0.find(a=>a.url===d.url);if(fu){fu.body=d.body||"";fu.error=d.error||null;if(d.status==="error"&&!fu.error)fu.error=d.error||"Fetch failed";}setArts([...arts0]);break;
        case"embed_done":upStage("embed","done");timesRef.current.embed=now-(timesRef.current.embed||now);break;
        case"extract_result":upStage("extract","running");
          const ea=arts0.find(a=>a.url===d.url||a.source_domain===d.source_domain);if(ea){ea.claims=d.claims||[];ea.framing_score=d.framing_score??null;ea.error=d.error||null;setArts([...arts0]);}break;
        case"match_result":upStage("match","done");timesRef.current.match=now-(timesRef.current.match||now);c0=(d.canonical_claims||[]);setCanons([...c0]);break;
        case"consensus_result":upStage("consensus","done");timesRef.current.consensus=now-(timesRef.current.consensus||now);co0=(d.per_claim||[]);setCons(co0);setTh(65);break;
        case"done":tms=d.total_ms;setT(tms);for(const s of STAGES)upStage(s,"done");break;
        case"warning":setWarn((d.message||"Unknown"));break;
        case"error":re=d.stage==="timeout"?"Analysis took too long.":(d.message||d.stage||"Pipeline error");break;
        }}catch{}}}
      }
    }catch(e:unknown){if(e instanceof DOMException&&e.name==="AbortError")return;re=e instanceof Error?e.message:"Connection lost";}
    setSTimes({...timesRef.current});setR(false);
    if(re){setErr(re);}else{const entry:Stored={query:t,timestamp:Date.now(),totalMs:tms,articles:arts0,canonicalClaims:c0,consensusClaims:co0};const h=[...loadH(),entry];saveH(h);setHist(h);}
  },[running,upStage]);

  const preset=useCallback((p:string)=>{setQ(p);runQ(p);},[runQ]);
  const loadCached=useCallback((e:Stored)=>{setArts(e.articles);setCanons(e.canonicalClaims);setCons(e.consensusClaims);setT(e.totalMs);setCAt(e.timestamp);setQRan(e.query);setSt(STAGES.map(s=>({stage:s,status:"done"})));setTh(65);setR(false);setErr(null);setWarn(null);},[]);
  const clearH=useCallback(()=>{localStorage.removeItem(LS_KEY);setHist([]);},[]);

  const hasArts=arts.some(a=>a.claims.length>0);

  return (
    <div className="mx-auto max-w-[900px] space-y-6">
      <div><h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">Investigate</h1>
        <p className="mt-1.5 font-sans text-[0.9rem] text-[var(--nn-text-dim)]">Live analysis — your query runs through our pipeline in real time via Fireworks-hosted DeepSeek V4 Pro. Not cached, not pre-computed.</p></div>
      {showBadge&&<div className="inline-flex items-center gap-1.5 rounded-full border border-[var(--nn-border)] bg-[var(--nn-surface)] px-3 py-1 font-mono text-[0.75rem] text-[var(--nn-text-dim)]"><Loader2 size={12} className="animate-spin"/>fireworks · deepseek-v4-flash</div>}
      {cachedAt&&<div className="inline-flex items-center gap-1.5 rounded-full border border-[var(--nn-slate)] bg-[var(--nn-slate-dim)] px-3 py-1 font-mono text-[0.75rem] text-[var(--nn-slate)]"><Clock size={12}/>Viewing cached analysis from {new Date(cachedAt).toLocaleString()}</div>}
      <div className="rounded-[14px] border border-[var(--nn-amber)] bg-[var(--nn-amber)]/10 px-5 py-4"><p className="font-sans text-[0.82rem] leading-relaxed text-[var(--nn-amber)]">Claim resolution states are not available for ad-hoc reports. This analysis runs pipeline stages 1–3 in read-only mode.</p></div>
      <div className="flex flex-wrap items-center gap-2">{stages.map((s,i)=>(<div key={s.stage} className="flex items-center gap-2"><div className={`flex items-center gap-1.5 rounded-full border px-3 py-1 font-sans text-[0.78rem] transition-colors ${s.status==="running"?"border-[var(--nn-navy)] bg-[var(--nn-navy-dim)] text-[var(--nn-navy)] font-semibold":s.status==="done"?"border-[var(--nn-teal)] bg-[var(--nn-teal-dim)] text-[var(--nn-teal)]":"border-[var(--nn-border)] bg-[var(--nn-surface)] text-[var(--nn-text-dim)]"}`}>{s.status==="running"?<Loader2 size={12} className="animate-spin"/>:s.status==="done"?<CheckCircle2 size={12}/>:<Circle size={12}/>}{sl(s.stage)}{s.status==="done"&&sTimes[s.stage]!=null&&<span className="font-mono text-[0.75rem]">{sTimes[s.stage]<1000?Math.round(sTimes[s.stage])+"ms":(sTimes[s.stage]/1000).toFixed(1)+"s"}</span>}</div>{i<STAGES.length-1&&<span className="text-[var(--nn-text-dim)]">→</span>}</div>))}</div>
      <div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-6"><h2 className="mb-4 font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">Query</h2><div className="mb-3 flex flex-wrap gap-2">{PRESETS.map(p=>(<button key={p} type="button" onClick={()=>preset(p)} disabled={running} className="rounded-full border border-[var(--nn-border)] bg-[var(--nn-surface2)] px-3 py-1 font-sans text-[0.78rem] text-[var(--nn-text)] hover:border-[var(--nn-navy)] transition-colors disabled:opacity-40">{p}</button>))}</div><div className="mb-4 flex gap-3"><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Search any subject..." disabled={running} onKeyDown={e=>e.key==="Enter"&&runQ(q)} className="flex-1 rounded-[10px] border border-[var(--nn-border)] bg-[var(--nn-surface2)] px-4 py-2.5 font-sans text-[0.84rem] text-[var(--nn-text)] placeholder:text-[var(--nn-text-dim)] focus:border-[var(--nn-navy)] focus:outline-none disabled:opacity-40"/><button type="button" onClick={()=>runQ(q)} disabled={!q.trim()||running} className="inline-flex items-center gap-2 rounded-full border border-[var(--nn-navy)] bg-[var(--nn-navy)] px-5 py-2 font-heading text-[0.82rem] font-semibold text-white transition-opacity disabled:opacity-40">{running?<Loader2 size={14} className="animate-spin"/>:<Send size={14}/>}{running?"Running…":"Analyze"}</button></div></div>
      {err&&<div className="rounded-[14px] border border-[var(--nn-red)] bg-[var(--nn-red)]/10 px-5 py-4"><div className="flex items-start gap-3"><AlertTriangle size={18} className="mt-0.5 shrink-0 text-[var(--nn-red)]"/><div><p className="font-sans text-[0.84rem] font-semibold text-[var(--nn-red)]">{err}</p><button type="button" onClick={()=>{setErr(null);setQ(qRan);}} className="mt-2 rounded-full border border-[var(--nn-red)] px-3 py-1 font-sans text-[0.75rem] text-[var(--nn-red)] hover:bg-[var(--nn-red)]/10">Retry</button></div><button onClick={()=>setErr(null)} className="ml-auto shrink-0 rounded p-1 text-[var(--nn-text-dim)] hover:text-[var(--nn-text)]"><X size={14}/></button></div></div>}
      {warn&&!err&&<div className="rounded-[10px] border border-[var(--nn-amber)] bg-[var(--nn-amber)]/10 px-4 py-3 font-sans text-[0.8rem] text-[var(--nn-amber)]"><AlertTriangle size={14} className="mr-2 inline-block"/>{warn}</div>}

      {hasArts?<><div><h2 className="mb-3 font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">Articles ({arts.filter(a=>a.claims.length>0).length} analyzed)</h2><div className="grid grid-cols-1 gap-4 md:grid-cols-2">{arts.map((a,i)=>(<div key={a.url||i} className={`rounded-[14px] border p-5 transition-opacity ${a.error&&!a.body?"border-[var(--nn-border)] bg-[var(--nn-surface)] opacity-60":"border-[var(--nn-border)] bg-[var(--nn-surface)]"}`}><div className="mb-3 flex items-start justify-between gap-3"><a href={a.url} target="_blank" rel="noopener noreferrer" className="font-heading text-[0.9rem] font-semibold text-[var(--nn-navy)] hover:underline">{a.title||"Untitled"}<ExternalLink size={12} className="ml-1 inline-block text-[var(--nn-text-dim)]"/></a><span className="shrink-0 rounded-full border border-[var(--nn-border)] bg-[var(--nn-surface2)] px-2 py-0.5 font-mono text-[0.75rem] text-[var(--nn-text-dim)]">{a.source_domain}</span></div>{a.error&&!a.body?<p className="rounded-[10px] border border-[var(--nn-amber)]/30 bg-[var(--nn-amber)]/5 px-3 py-2 font-sans text-[0.75rem] text-[var(--nn-text-dim)] italic">Body not available — {a.error}</p>:a.body?<><p className="mb-3 font-sans text-[0.78rem] leading-relaxed text-[var(--nn-text-dim)] line-clamp-3">{a.body.slice(0,200)}</p>{a.claims.length>0?<div className="space-y-1.5"><p className="font-mono text-[0.75rem] font-semibold text-[var(--nn-text-dim)] uppercase tracking-wide">Claims ({a.claims.length})</p>{a.claims.slice(0,5).map((c,ci)=>(<div key={ci} className="flex items-start gap-2"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[var(--nn-navy)]"/><p className="font-sans text-[0.78rem] text-[var(--nn-text)]">{c.text}</p></div>))}{a.claims.length>5&&<p className="font-sans text-[0.75rem] italic text-[var(--nn-text-dim)]">+{a.claims.length-5} more</p>}</div>:<p className="font-sans text-[0.75rem] italic text-[var(--nn-text-dim)]">No claims extracted</p>}</>:running?<div className="space-y-2 animate-pulse"><div className="h-3 w-3/4 rounded bg-[var(--nn-border)]"/><div className="h-3 w-full rounded bg-[var(--nn-border)]"/><div className="h-3 w-5/6 rounded bg-[var(--nn-border)]"/></div>:null}</div>))}</div>{arts.some(a=>a.error)&&allDone&&<p className="mt-3 font-sans text-[0.76rem] text-[var(--nn-amber)]">{arts.filter(a=>a.error).length} of {arts.length} sources returned no body — showing partial results.</p>}</div>{adjCons.length>0&&<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-6"><h2 className="mb-4 font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">Consensus Analysis</h2><div className="space-y-3">{[...adjCons].sort((a,b)=>b.source_count-a.source_count).map((c,i)=>(<div key={i} className={`rounded-[10px] border p-4 ${c.would_absorb?"border-[var(--nn-teal)] bg-[var(--nn-teal-dim)]":"border-[var(--nn-border)] bg-[var(--nn-surface2)]"}`}><p className="mb-2 font-sans text-[0.84rem] text-[var(--nn-text)]">{c.claim_text}</p><div className="flex flex-wrap items-center gap-2">{c.would_absorb&&<span className="rounded-full border border-[var(--nn-teal)] bg-[var(--nn-teal)] px-2 py-0.5 font-mono text-[0.75rem] font-semibold text-white">Would enter consensus reality</span>}<span className="font-mono text-[0.75rem] text-[var(--nn-text-dim)]">Reported by {c.t1t2_reporting} of {c.pool_size} consensus-pool sources ({c.pct}%)</span></div></div>))}</div><div className="mt-6 border-t border-[var(--nn-border)] pt-5"><div className="mb-2 flex items-center justify-between"><span className="font-mono text-[0.76rem] font-semibold text-[var(--nn-text)]">Consensus threshold — {threshold}%</span></div><Slider value={[threshold]} min={40} max={90} step={1} onValueChange={([v]:number[])=>setTh(v)} disabled={!cons.length} className="w-full"/><p className="mt-2 font-sans text-[0.75rem] text-[var(--nn-text-dim)]">Consensus reality is a parameter, not a verdict. Drag to see how the threshold changes which claims cross.</p></div></div>}</>:null}

      {allDone&&arts.length===0&&!err&&<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-8 text-center"><Search size={28} className="mx-auto mb-3 text-[var(--nn-text-dim)]"/><p className="font-sans text-[0.84rem] text-[var(--nn-text-dim)]">Not enough panel sources for "{qRan}" — try a broader or more current topic.</p><div className="mt-3 flex justify-center gap-2">{PRESETS.map(p=>(<button key={p} onClick={()=>preset(p)} className="rounded-full border border-[var(--nn-border)] bg-[var(--nn-surface2)] px-3 py-1 font-sans text-[0.78rem] text-[var(--nn-text)] hover:border-[var(--nn-navy)]">{p}</button>))}</div></div>}

      {history.length>0&&!hasArts&&!running&&<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-6"><div className="mb-3 flex items-center justify-between"><h2 className="font-heading text-[1rem] font-bold text-[var(--nn-text)]">Recent analyses</h2><button onClick={clearH} className="font-mono text-[0.75rem] text-[var(--nn-text-dim)] hover:text-[var(--nn-text)]">Clear all</button></div><div className="space-y-2">{history.slice(-3).reverse().map((h,i)=>(<button key={i} onClick={()=>loadCached(h)} className="w-full rounded-[10px] border border-[var(--nn-border)] bg-[var(--nn-surface2)] px-4 py-3 text-left hover:border-[var(--nn-navy)] transition-colors"><p className="font-sans text-[0.82rem] text-[var(--nn-text)]">{h.query}</p><p className="mt-0.5 font-mono text-[0.75rem] text-[var(--nn-text-dim)]">{rtime(h.timestamp)} · {h.articles.length} articles · {h.canonicalClaims.length} claims</p></button>))}</div></div>}

      {!hasArts&&!running&&!err&&history.length===0&&<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-8 text-center"><Search size={28} className="mx-auto mb-3 text-[var(--nn-text-dim)]"/><p className="font-sans text-[0.84rem] text-[var(--nn-text-dim)]">Enter a subject query to analyze coverage from our curated source panel in real time.</p><p className="mt-1 font-sans text-[0.75rem] text-[var(--nn-text-dim)]">The pipeline searches, fetches, embeds, extracts claims, and computes consensus — all live.</p></div>}
    </div>
  );
}
