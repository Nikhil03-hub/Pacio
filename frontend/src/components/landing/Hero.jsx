import React, { useState } from 'react';
import { ArrowRight, Play, Mail } from 'lucide-react';
import { heroQuote } from '../../mock';

const RocketIllustration = () => (
  <svg viewBox="0 0 520 640" className="w-full h-full" fill="none" stroke="#111111" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
    {/* sparkles around */}
    <g stroke="#111" strokeWidth="1.4">
      <path d="M70 90 L75 102 L87 107 L75 112 L70 124 L65 112 L53 107 L65 102 Z" />
      <path d="M420 60 L424 70 L434 74 L424 78 L420 88 L416 78 L406 74 L416 70 Z" />
      <path d="M460 220 L463 228 L471 231 L463 234 L460 242 L457 234 L449 231 L457 228 Z" />
      <circle cx="40" cy="200" r="2.5" fill="#111" />
      <circle cx="490" cy="380" r="3" fill="#111" />
      <circle cx="100" cy="380" r="2" fill="#111" />
      <circle cx="430" cy="500" r="2.5" fill="#111" />
      <path d="M150 50 L153 58 L161 61 L153 64 L150 72 L147 64 L139 61 L147 58 Z" />
    </g>

    {/* curved orbit path */}
    <path d="M30 580 Q 260 640 490 580" strokeDasharray="3 8" />
    <path d="M60 540 Q 260 595 460 540" strokeDasharray="2 7" opacity="0.5" />

    {/* clouds / puffs around bottom */}
    <g>
      <path d="M120 470 q 10 -22 30 -18 q 6 -16 24 -10 q 12 -10 26 0 q 8 -8 20 0" />
      <path d="M340 450 q 12 -20 30 -14 q 10 -14 26 -6" />
    </g>

    {/* rocket body */}
    <g transform="translate(0,0)">
      {/* nose cone */}
      <path d="M260 70 C 290 110 310 165 318 220 L202 220 C210 165 230 110 260 70 Z" />
      <path d="M260 70 C 256 88 256 100 260 110 C 264 100 264 88 260 70 Z" fill="#111" />
      {/* mid body */}
      <path d="M202 220 L318 220 L320 340 L200 340 Z" />
      {/* bottom body */}
      <path d="M200 340 L320 340 L324 410 L196 410 Z" />
      {/* horizontal bands */}
      <line x1="202" y1="260" x2="318" y2="260" />
      <line x1="200" y1="370" x2="320" y2="370" />
      {/* window */}
      <circle cx="260" cy="170" r="30" />
      <circle cx="260" cy="170" r="20" />
      <path d="M250 162 a 12 12 0 0 1 18 0" />
      {/* small badge */}
      <rect x="240" y="285" width="40" height="22" rx="3" />
      <line x1="248" y1="296" x2="272" y2="296" />
      {/* rivets */}
      <circle cx="215" cy="245" r="1.6" fill="#111" />
      <circle cx="305" cy="245" r="1.6" fill="#111" />
      <circle cx="215" cy="325" r="1.6" fill="#111" />
      <circle cx="305" cy="325" r="1.6" fill="#111" />
      <circle cx="210" cy="395" r="1.6" fill="#111" />
      <circle cx="310" cy="395" r="1.6" fill="#111" />

      {/* left fin */}
      <path d="M200 340 L140 420 L140 460 L196 410 Z" />
      <line x1="170" y1="395" x2="170" y2="445" />
      {/* right fin */}
      <path d="M320 340 L380 420 L380 460 L324 410 Z" />
      <line x1="350" y1="395" x2="350" y2="445" />

      {/* exhaust ring */}
      <ellipse cx="260" cy="412" rx="64" ry="6" />

      {/* flames */}
      <path d="M220 416 Q 232 470 244 416" />
      <path d="M242 416 Q 260 490 278 416" />
      <path d="M276 416 Q 288 470 300 416" />
      <path d="M232 420 Q 240 450 250 420" opacity="0.8" />
      <path d="M270 420 Q 280 450 290 420" opacity="0.8" />
    </g>
  </svg>
);

const GoogleG = () => (
  <svg viewBox="0 0 24 24" className="w-4 h-4">
    <path fill="#4285F4" d="M23 12.3c0-.8-.1-1.6-.2-2.3H12v4.4h6.2a5.3 5.3 0 0 1-2.3 3.5v2.9h3.8c2.2-2 3.3-5 3.3-8.5z"/>
    <path fill="#34A853" d="M12 24c3.1 0 5.8-1 7.7-2.8l-3.8-2.9c-1 .7-2.4 1.1-3.9 1.1-3 0-5.6-2-6.5-4.8H1.6v3C3.5 21.4 7.4 24 12 24z"/>
    <path fill="#FBBC05" d="M5.5 14.6a7.4 7.4 0 0 1 0-5.2v-3H1.6a12 12 0 0 0 0 11l3.9-3z"/>
    <path fill="#EA4335" d="M12 4.8c1.7 0 3.2.6 4.4 1.7l3.3-3.3C17.8 1.2 15.1 0 12 0 7.4 0 3.5 2.6 1.6 6.4l3.9 3C6.4 6.7 9 4.8 12 4.8z"/>
  </svg>
);

const VideoCard = () => (
  <div className="relative rounded-2xl overflow-hidden shadow-card-xl group cursor-pointer ring-subtle h-full bg-[#10054d]">
    <div className="absolute inset-0" style={{
      background: 'radial-gradient(60% 80% at 30% 20%, rgba(232, 64, 13, 0.35) 0%, transparent 60%), radial-gradient(70% 70% at 100% 100%, rgba(46, 36, 96, 1) 0%, rgba(16, 5, 77, 1) 70%)'
    }} />
    {/* decorative grid */}
    <div className="absolute inset-0 opacity-[0.08]" style={{
      backgroundImage: 'linear-gradient(rgba(255,255,255,0.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.6) 1px, transparent 1px)',
      backgroundSize: '32px 32px'
    }} />
    <div className="relative aspect-[16/10] p-6 flex flex-col justify-between">
      {/* top eyebrow */}
      <div className="flex items-center gap-2">
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/10 ring-1 ring-white/20 backdrop-blur-sm text-white text-[11px] font-medium tracking-eyebrow">
          <span className="w-1.5 h-1.5 rounded-full bg-[#e8400d] animate-pulse" />
          WATCH 1:42
        </span>
      </div>

      {/* Center play button */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="relative">
          <div className="absolute inset-0 rounded-full bg-white/20 blur-xl scale-150" />
          <div className="relative w-16 h-16 rounded-full bg-white flex items-center justify-center group-hover:scale-110 transition-transform shadow-card-xl">
            <Play className="w-6 h-6 text-[#10054d] ml-1 fill-[#10054d]" />
          </div>
        </div>
      </div>

      {/* bottom title */}
      <div className="text-white relative">
        <div className="text-[10px] uppercase tracking-eyebrow opacity-60 mb-1">READINESS ENGINE</div>
        <div className="text-[18px] md:text-[22px] font-medium leading-snug max-w-[400px] tracking-tight2">
          See the next best action for every student, drive, and recruiter
        </div>
      </div>
    </div>
  </div>
);

export default function Hero() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const submit = (e) => {
    e.preventDefault();
    if (!email) return;
    setSubmitted(true);
    setTimeout(() => { setSubmitted(false); setEmail(''); }, 2400);
  };

  return (
    <section className="relative overflow-hidden">
      {/* layered radial atmosphere — corner anchored sunlight effect */}
      <div className="absolute inset-0 pointer-events-none" style={{
        background: `
          radial-gradient(70% 60% at -10% -10%, rgba(232, 64, 13, 0.75) 0%, rgba(255, 222, 178, 0.7) 18%, rgba(255, 238, 216, 0.6) 35%, rgba(208, 178, 255, 0.5) 60%, rgba(255,255,255,0) 80%),
          radial-gradient(50% 50% at 100% 0%, rgba(183, 239, 178, 0.45) 0%, rgba(226, 221, 253, 0.35) 40%, rgba(255,255,255,0) 70%),
          radial-gradient(50% 60% at 110% 100%, rgba(208, 178, 255, 0.4) 0%, rgba(255,255,255,0) 60%),
          #ffffff
        `
      }} />
      {/* subtle grain */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.06] mix-blend-multiply" style={{
        backgroundImage: 'url("data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'200\' height=\'200\'><filter id=\'n\'><feTurbulence type=\'fractalNoise\' baseFrequency=\'0.9\' numOctaves=\'2\'/></filter><rect width=\'200\' height=\'200\' filter=\'url(%23n)\' opacity=\'0.6\'/></svg>")'
      }} />

      <div className="relative max-w-[1200px] mx-auto px-5 pt-[120px] pb-[60px] md:pt-[140px] md:pb-[80px]">
        {/* NEW eyebrow pill */}
        <div className="flex justify-center mb-9">
          <a href="/login" className="group inline-flex items-center bg-white border border-[#111111] rounded-full overflow-hidden text-[12px] shadow-card-xl hover:translate-y-[-1px] transition-transform">
            <span className="bg-[#111111] text-white font-bold px-2.5 py-1.5 tracking-eyebrow">NEW</span>
            <span className="px-3 py-1.5 text-[#111111] font-medium flex items-center gap-1.5">
              CareerOS V3 intelligence workspace is live
              <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
            </span>
          </a>
        </div>

        <div className="grid lg:grid-cols-[1.35fr_1fr] gap-8 items-center">
          <div className="relative z-10">
            <h1 className="font-display font-medium text-[#111111] leading-[0.88] text-[52px] sm:text-[70px] md:text-[88px] lg:text-[104px]"
                style={{ letterSpacing: '-0.055em' }}>
              The operating system for placement intelligence
            </h1>
            <p className="mt-7 text-[18px] md:text-[20px] text-[#6d6c6b] max-w-[520px] tracking-tight2 leading-relaxed">
              Connect student preparation, faculty coaching, recruiter movement, applications, interviews, offers, and board reports in one intelligence layer.
            </p>

            <form onSubmit={submit} className="mt-8 max-w-[500px]">
              <div className="relative flex items-center bg-white border border-[#111111] rounded-xl h-[58px] p-1.5 pl-5 shadow-card-xl">
                <Mail className="w-4 h-4 text-[#6d6c6b] mr-2.5 shrink-0" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your institute email"
                  className="flex-1 outline-none bg-transparent text-[15px] text-[#111111] placeholder:text-[#6d6c6b]"
                />
                <button type="submit" className="shrink-0 inline-flex items-center gap-1.5 px-4 h-[44px] rounded-[10px] bg-[#111111] text-white text-[14px] font-medium hover:bg-[#272625] transition-colors">
                  {submitted ? 'Thanks' : (<>Request demo <ArrowRight className="w-3.5 h-3.5" /></>)}
                </button>
              </div>
            </form>

            {/* Social proof */}
            <div className="mt-7 flex flex-wrap items-center gap-x-6 gap-y-3 text-[12px]">
              <div className="flex items-center gap-2">
                <GoogleG />
                <div className="text-[10px] uppercase tracking-eyebrow text-[#6d6c6b] mb-3">Illustrative &middot; not a customer review</div>
                <span className="text-[#6d6c6b]">Live readiness scoring</span>
              </div>
              <div className="w-px h-4 bg-[#1111111a]" />
              <div className="flex items-center gap-1.5">
                <span className="text-[#6d6c6b]">Built for</span>
                <span className="font-bold text-[#111111] tracking-tight2">students, TPOs, faculty, and recruiters.</span>
              </div>
            </div>
          </div>

          {/* Rocket illustration */}
          <div className="relative hidden lg:block h-[560px]">
            <div className="absolute -right-16 -top-12 w-[520px] h-[620px] overflow-hidden">
              <RocketIllustration />
            </div>
          </div>
        </div>

        {/* Video / Quote card */}
        <div className="mt-14 grid md:grid-cols-[1.5fr_1fr] gap-5 items-stretch">
          <VideoCard />

          <div className="rounded-2xl bg-white ring-subtle p-6 flex flex-col justify-between shadow-card-xl">
            <div>
              <div className="text-[10px] uppercase tracking-eyebrow text-inherit opacity-70">Illustrative &middot; not a customer review</div>
              <p className="text-[18px] md:text-[22px] leading-[1.25] font-medium text-[#111111] tracking-tight2">
                "{heroQuote.quote}"
              </p>
            </div>
            <div className="mt-5 pt-5 border-t border-[#1111111f] flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#ffd7f0] to-[#e2ddfd] flex items-center justify-center text-[13px] font-bold text-[#111111]">
                GF
              </div>
              <div className="flex-1">
                <div className="text-[14px] font-medium text-[#111111]">{heroQuote.name}</div>
                <div className="text-[12px] text-[#6d6c6b]">{heroQuote.role}</div>
              </div>
              <div className="text-[14px] font-bold tracking-tight2 text-[#111111]">{heroQuote.company}</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
