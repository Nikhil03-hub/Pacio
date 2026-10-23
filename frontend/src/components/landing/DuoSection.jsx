import React from 'react';
import { ArrowRight, Sparkles } from 'lucide-react';
import { signals, duoQuote } from '../../mock';

const row1 = signals.slice(0, 13);
const row2 = signals.slice(13, 26);
const row3 = signals.slice(26);

const SignalPill = ({ text, tone }) => {
  const tones = {
    pink: 'bg-[#ffd7f0] text-[#111111]',
    yellow: 'bg-[#ffef99] text-[#111111]',
    mint: 'bg-[#b7efb2] text-[#111111]',
    lilac: 'bg-[#e2ddfd] text-[#111111]',
    white: 'bg-white/95 text-[#111111] ring-1 ring-white/20',
    dark: 'bg-[#10054d]/90 text-white ring-1 ring-white/20',
  };
  return (
    <span className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-full text-[13px] whitespace-nowrap ${tones[tone] || tones.white}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${tone === 'dark' ? 'bg-[#e8400d]' : 'bg-[#111111]'}`} />
      {text}
    </span>
  );
};

const MarqueeRow = ({ items, direction = 'left', tones }) => (
  <div className="relative overflow-hidden no-scrollbar">
    <div className={`flex gap-3 w-max ${direction === 'left' ? 'marquee-left' : 'marquee-right'}`}>
      {[...items, ...items].map((s, i) => (
        <SignalPill key={i} text={s} tone={tones[i % tones.length]} />
      ))}
    </div>
  </div>
);

export default function DuoSection() {
  return (
    <section className="relative bg-[#272625] text-white overflow-hidden">
      {/* atmospheric tints */}
      <div className="absolute inset-0 pointer-events-none" style={{
        background:
          'radial-gradient(60% 50% at 0% 0%, rgba(232, 64, 13, 0.22) 0%, rgba(0,0,0,0) 50%), radial-gradient(70% 70% at 100% 100%, rgba(16, 5, 77, 0.65) 0%, rgba(0,0,0,0) 60%), radial-gradient(40% 40% at 50% 50%, rgba(46, 36, 96, 0.3) 0%, rgba(0,0,0,0) 70%)'
      }} />
      {/* subtle grid */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.05]" style={{
        backgroundImage: 'linear-gradient(rgba(255,255,255,0.7) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.7) 1px, transparent 1px)',
        backgroundSize: '48px 48px'
      }} />

      <div className="relative max-w-[1200px] mx-auto px-5 pt-28 pb-24">
        <div className="text-center max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-sm ring-1 ring-white/15">
            <span className="w-5 h-5 rounded-md bg-white flex items-center justify-center">
              <Sparkles className="w-3 h-3 text-[#10054d]" />
            </span>
            <span className="text-[11px] font-medium tracking-eyebrow uppercase text-white">CareerOS Intelligence Layer</span>
          </div>
          <h2 className="mt-6 font-display font-medium leading-[1.0] text-[44px] md:text-[68px]" style={{ letterSpacing: '-0.045em' }}>
            Transform the way campuses <span className="italic font-medium" style={{ color: '#e2ddfd' }}>prepare</span><br />and place talent
          </h2>
          <p className="mt-6 text-[16px] md:text-[18px] text-white/65 max-w-[620px] mx-auto tracking-tight2 leading-relaxed">
            Surface readiness risks, recruiter movement, training gaps, interview signals, ATS gaps, and the next action for every role.
          </p>
          <a href="/login" className="mt-9 inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-white text-[#111111] text-[14px] font-medium hover:bg-[#f4f3ef] transition-colors group shadow-card-xl">
            Explore intelligence
            <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </a>
        </div>

        {/* Signals marquees */}
        <div className="mt-16">
          <div className="flex items-center justify-center gap-2 mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-[#e8400d] animate-pulse" />
            <div className="text-[12px] uppercase tracking-eyebrow text-white/55 font-medium">Never miss a placement signal</div>
          </div>
          {/* edge fade mask wrapper */}
          <div className="relative" style={{ maskImage: 'linear-gradient(to right, transparent, black 8%, black 92%, transparent)', WebkitMaskImage: 'linear-gradient(to right, transparent, black 8%, black 92%, transparent)' }}>
            <div className="space-y-3">
              <MarqueeRow items={row1} direction="left" tones={['white','pink','white','mint','dark','yellow','white','lilac','white','white','pink','white','mint']} />
              <MarqueeRow items={row2} direction="right" tones={['white','dark','mint','white','pink','white','yellow','white','lilac','white','white','mint','dark']} />
              <MarqueeRow items={row3} direction="left" tones={['white','lilac','white','dark','pink','white','mint','white','yellow','white','dark','white','lilac']} />
            </div>
          </div>
        </div>

        {/* Deel quote */}
        <div className="mt-20 max-w-3xl mx-auto bg-white/[0.04] ring-1 ring-white/10 backdrop-blur-sm rounded-2xl p-7 md:p-9">
          <div className="text-[11px] uppercase tracking-eyebrow text-white/55 mb-5">
            Illustrative role walkthrough &middot; not a customer review
          </div>
          <p className="text-[22px] md:text-[28px] leading-[1.2] font-medium text-white" style={{ letterSpacing: '-0.03em' }}>
            "{duoQuote.quote}"
          </p>
          <div className="mt-6 pt-6 border-t border-white/15 flex items-center gap-3">
            <div className="w-11 h-11 rounded-full bg-gradient-to-br from-[#e8400d] to-[#ffd7f0] flex items-center justify-center text-[13px] font-bold text-[#111111]">&sect;</div>
            <div className="flex-1">
              <div className="text-[14px] font-medium text-white">{duoQuote.name}</div>
              <div className="text-[12px] text-white/60">{duoQuote.role}</div>
            </div>
            <div className="text-[16px] font-bold tracking-tight2 text-white">{duoQuote.company}</div>
          </div>
        </div>
      </div>
    </section>
  );
}
