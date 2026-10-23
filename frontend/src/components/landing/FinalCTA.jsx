import React, { useState } from 'react';

export default function FinalCTA() {
  const [email, setEmail] = useState('');
  const [done, setDone] = useState(false);
  const submit = (e) => {
    e.preventDefault();
    if (!email) return;
    setDone(true);
    setTimeout(() => { setDone(false); setEmail(''); }, 2400);
  };
  return (
    <section className="relative bg-[#272625] text-white overflow-hidden">
      <div className="absolute inset-0 pointer-events-none" style={{
        background: 'radial-gradient(50% 50% at 100% 0%, rgba(232, 64, 13, 0.25) 0%, rgba(0,0,0,0) 60%), radial-gradient(60% 60% at 0% 100%, rgba(16, 5, 77, 0.6) 0%, rgba(0,0,0,0) 60%)'
      }} />
      <div className="relative max-w-[1200px] mx-auto px-5 py-24 text-center">
        <h2 className="font-display font-medium tracking-display leading-[1.02] text-[40px] md:text-[64px] max-w-3xl mx-auto">
          Deploy your placement intelligence layer
        </h2>

        <form onSubmit={submit} className="mt-10 max-w-[520px] mx-auto">
          <div className="flex items-center bg-[#2e2460] rounded-xl h-[56px] p-1.5 pl-4 ring-1 ring-white/10">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your institute email"
              className="flex-1 outline-none bg-transparent text-[15px] text-white placeholder:text-white/50"
            />
            <button type="submit" className="shrink-0 inline-flex items-center px-4 h-[42px] rounded-[10px] bg-white text-[#111111] text-[14px] font-medium hover:bg-[#f4f3ef] transition-colors">
              {done ? 'Thanks' : 'Request demo'}
            </button>
          </div>
        </form>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-8 text-white/70">
          <div className="flex items-center gap-2">
            <div className="text-[10px] uppercase tracking-eyebrow text-inherit opacity-70">Illustrative &middot; not a customer review</div>
            <span className="text-[12px]">Readiness scoring</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="text-[10px] uppercase tracking-eyebrow text-inherit opacity-70">Illustrative &middot; not a customer review</div>
            <span className="text-[12px]">Placement reports</span>
          </div>
          <div className="flex items-center gap-2 text-[12px]">
            <span>Built for</span>
            <span className="font-bold text-white">campus placement teams</span>
          </div>
        </div>
      </div>
    </section>
  );
}
