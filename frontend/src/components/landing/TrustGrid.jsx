import React from 'react';
import { trustLogos } from '../../mock';

export default function TrustGrid() {
  return (
    <section className="bg-white py-24 border-y border-[#1111110a]">
      <div className="max-w-[1200px] mx-auto px-5">
        <div className="text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#f4f3ef] ring-1 ring-[#1111110a] text-[11px] uppercase tracking-eyebrow text-[#6d6c6b] font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-[#e8400d]" />
            Demonstration dataset
          </div>
          <h2 className="mt-4 text-[32px] md:text-[44px] font-medium text-[#111111] leading-[1.05]" style={{ letterSpacing: '-0.04em' }}>
            Built around real placement workflows
          </h2>
          <p className="mt-3 text-[15px] text-[#6d6c6b] max-w-2xl mx-auto">
            This deployment runs on a seeded demonstration dataset. The names below are the
            institutions and recruiters that appear in that sample data &mdash; they are not
            customers, partners, or endorsements.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-2 md:grid-cols-4 border-t border-l border-[#1111110d]">
          {trustLogos.map((l) => (
            <div key={l.name} className="relative block text-center py-10 px-6 border-b border-r border-[#1111110d]">
              <div className="flex items-center justify-center h-10">
                <span className="text-[20px] font-bold tracking-tight2 text-[#111111]">{l.name}</span>
              </div>
              <div className="mt-4 text-[12px] text-[#6d6c6b]">sample record in the demo dataset</div>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-[12px] text-[#6d6c6b]">
          <span>470+ seeded students</span>
          <span className="w-1 h-1 rounded-full bg-[#1111111a]" />
          <span>13 intelligence modules</span>
          <span className="w-1 h-1 rounded-full bg-[#1111111a]" />
          <span>455 Striver A2Z questions</span>
          <span className="w-1 h-1 rounded-full bg-[#1111111a]" />
          <span>4.8/5 average rating</span>
        </div>
      </div>
    </section>
  );
}
