'use client';

import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Minus, Plus } from 'lucide-react';

import type { FaqItem } from '@/lib/site-content';

type FaqAccordionProps = {
  items: FaqItem[];
};

export function FaqAccordion({ items }: FaqAccordionProps) {
  const [openIndex, setOpenIndex] = useState(0);

  return (
    <div className="space-y-3" role="list">
      {items.map((item, index) => {
        const open = openIndex === index;
        const answerId = `faq-answer-${index}`;

        return (
          <article key={item.question} className="overflow-hidden rounded-[26px] border border-white/10 bg-white/[0.04] backdrop-blur-xl" role="listitem">
            <h4 className="m-0">
              <button
                type="button"
                onClick={() => setOpenIndex(open ? -1 : index)}
                className="flex min-h-14 w-full items-center justify-between gap-4 px-5 py-5 text-left"
                aria-expanded={open}
                aria-controls={answerId}
              >
                <span className="text-pretty pr-2 text-base font-semibold text-white">{item.question}</span>
                <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-white/75">
                  {open ? <Minus className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
                </span>
              </button>
            </h4>
            <AnimatePresence initial={false}>
              {open ? (
                <motion.div
                  id={answerId}
                  role="region"
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                >
                  <p className="px-5 pb-5 text-sm leading-7 text-white/68">{item.answer}</p>
                </motion.div>
              ) : null}
            </AnimatePresence>
          </article>
        );
      })}
    </div>
  );
}