import React from 'react';
import { customerStats, featuredTestimonials } from '../../mock';

const tileColors = ['#ffd7f0', '#b7efb2', '#ffef99', '#e2ddfd', '#ffd7f0', '#b7efb2'];

export default function CustomerStories() {
  return (
    <section className="bg-white py-24">
      <div className="max-w-[1200px] mx-auto px-5">
        <h2 className="font-display font-medium text-[#111111] tracking-display leading-[1.05] text-[36px] md:text-[52px] text-center">
          What the demonstration dataset contains
        </h2>
        <p className="mt-3 text-[15px] text-[#6d6c6b] text-center max-w-2xl mx-auto">
          Every figure below is generated sample data shipped with this build so the product can be
          evaluated end to end. None of it is customer or placement-outcome data.
        </p>

        <div className="mt-12 grid grid-cols-2 md:grid-cols-3 gap-4">
          {customerStats.map((c, i) => (
            <div key={c.company} className="relative rounded-2xl p-6 md:p-7 overflow-hidden ring-subtle" style={{ background: tileColors[i] }}>
              <div className="text-[44px] md:text-[52px] font-medium text-[#111111] tracking-hero leading-none">{c.metric}</div>
              <div className="mt-1 text-[14px] text-[#111111]/70">{c.label}</div>
              <div className="mt-8 flex items-end justify-between">
                <div className="text-[13px] font-medium tracking-tight2 text-[#111111]/70">{c.company}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Role walkthroughs written by the product team, deliberately not presented as customer quotes. */}
        <p className="mt-16 mb-5 text-[12px] uppercase tracking-eyebrow text-[#6d6c6b]">
          Illustrative role walkthroughs &mdash; not customer testimonials
        </p>
        <div className="mt-0 grid md:grid-cols-3 gap-5">
          {featuredTestimonials.map((t) => (
            <div key={t.name} className="rounded-2xl ring-subtle p-6 bg-white">
              <p className="text-[17px] md:text-[19px] font-medium text-[#111111] tracking-tight2 leading-snug">
                "{t.quote}"
              </p>
              <div className="mt-5 pt-5 border-t border-[#1111111a] flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[#e2ddfd] to-[#ffd7f0] flex items-center justify-center text-[12px] font-bold text-[#111111]">
                  {t.name.split(' ').map(n => n[0]).join('').slice(0,2)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[13px] font-medium text-[#111111] truncate">{t.name}</div>
                  <div className="text-[11px] text-[#6d6c6b] truncate">{t.role}</div>
                </div>
                <div className="text-[12px] font-bold tracking-tight2 text-[#111111] truncate max-w-[100px] text-right">{t.company}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
