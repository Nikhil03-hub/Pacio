import React from 'react';
import { wallOfLove } from '../../mock';

const Quote = ({ t }) => (
  <div className="min-w-[300px] max-w-[300px] md:min-w-[340px] md:max-w-[340px] rounded-2xl ring-subtle bg-white p-5 mr-4">
    <p className="text-[14px] leading-relaxed text-[#111111]">
      "{t.text}"
    </p>
    <div className="mt-4 pt-4 border-t border-[#1111111a] flex items-center gap-3">
      <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[#ffd7f0] to-[#e2ddfd] flex items-center justify-center text-[12px] font-bold text-[#111111] shrink-0">
        {t.name.split(' ').map(n => n[0]).join('').slice(0,2)}
      </div>
      <div className="min-w-0">
        <div className="text-[13px] font-medium text-[#111111] truncate">{t.name}</div>
        <div className="text-[11px] text-[#6d6c6b] truncate">{t.role}</div>
      </div>
    </div>
  </div>
);

export default function WallOfLove() {
  const half = Math.ceil(wallOfLove.length / 2);
  const r1 = wallOfLove.slice(0, half);
  const r2 = wallOfLove.slice(half);

  return (
    <section className="bg-white py-24 overflow-hidden">
      <div className="max-w-[1200px] mx-auto px-5">
        <h2 className="font-display font-medium text-[#111111] tracking-display leading-[1.05] text-[32px] md:text-[44px] text-center">
          How each role uses the platform
        </h2>
        <p className="mt-3 text-[14px] text-[#6d6c6b] text-center max-w-2xl mx-auto">
          Written from the product team as role walkthroughs &mdash; these are illustrative, not customer testimonials.
        </p>
      </div>
      <div className="mt-12 space-y-4">
        <div className="overflow-hidden no-scrollbar">
          <div className="flex w-max marquee-left">
            {[...r1, ...r1].map((t, i) => <Quote key={i} t={t} />)}
          </div>
        </div>
        <div className="overflow-hidden no-scrollbar">
          <div className="flex w-max marquee-right">
            {[...r2, ...r2].map((t, i) => <Quote key={i} t={t} />)}
          </div>
        </div>
      </div>
    </section>
  );
}
