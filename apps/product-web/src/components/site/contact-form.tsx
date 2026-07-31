'use client';

import { useState } from 'react';
import { CheckCircle2, Loader2, Send } from 'lucide-react';

import { cn } from '@/lib/cn';

export function ContactForm() {
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setStatus('loading');

    const form = e.currentTarget;
    const formData = new FormData(form);
    
    // We inject the subject and other formsubmit config fields
    formData.append('_subject', 'New Contact Request from FreightPilot Website');
    formData.append('_captcha', 'false');

    try {
      const response = await fetch('https://formsubmit.co/ajax/nahomgwmichael@gmail.com', {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
        },
        body: formData,
      });

      if (response.ok) {
        setStatus('success');
        form.reset();
      } else {
        setStatus('error');
      }
    } catch (error) {
      setStatus('error');
    }
  };

  if (status === 'success') {
    return (
      <div className="flex flex-col items-center justify-center space-y-4 rounded-3xl border border-emerald-500/20 bg-emerald-500/10 p-12 text-center backdrop-blur-xl">
        <CheckCircle2 className="h-12 w-12 text-emerald-400" />
        <div className="space-y-2">
          <h3 className="font-display text-xl text-white">Message sent</h3>
          <p className="text-sm text-white/60">
            Thank you for reaching out. Our team will get back to you shortly.
          </p>
        </div>
        <button
          onClick={() => setStatus('idle')}
          className="mt-6 rounded-full border border-white/10 bg-white/5 px-6 py-2 text-sm font-medium text-white transition hover:bg-white/10"
        >
          Send another message
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="grid gap-5 sm:grid-cols-2">
        <div className="space-y-2">
          <label htmlFor="name" className="text-xs font-medium text-white/70">
            Full Name
          </label>
          <input
            id="name"
            name="name"
            required
            type="text"
            className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white placeholder-white/30 outline-none transition focus:border-cyan-400/50 focus:bg-white/5"
            placeholder="Jane Doe"
          />
        </div>
        <div className="space-y-2">
          <label htmlFor="email" className="text-xs font-medium text-white/70">
            Work Email
          </label>
          <input
            id="email"
            name="email"
            required
            type="email"
            className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white placeholder-white/30 outline-none transition focus:border-cyan-400/50 focus:bg-white/5"
            placeholder="jane@company.com"
          />
        </div>
      </div>

      <div className="space-y-2">
        <label htmlFor="company" className="text-xs font-medium text-white/70">
          Company Name
        </label>
        <input
          id="company"
          name="company"
          required
          type="text"
          className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white placeholder-white/30 outline-none transition focus:border-cyan-400/50 focus:bg-white/5"
          placeholder="Acme Logistics"
        />
      </div>

      <div className="space-y-2">
        <label htmlFor="message" className="text-xs font-medium text-white/70">
          Message
        </label>
        <textarea
          id="message"
          name="message"
          required
          rows={4}
          className="w-full resize-none rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white placeholder-white/30 outline-none transition focus:border-cyan-400/50 focus:bg-white/5"
          placeholder="How can we help your team?"
        />
      </div>

      {status === 'error' && (
        <p className="text-sm text-red-400">
          Something went wrong. Please try again later.
        </p>
      )}

      <button
        type="submit"
        disabled={status === 'loading'}
        className={cn(
          'inline-flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-400 px-6 py-3.5 text-sm font-semibold text-slate-950 transition',
          status === 'loading' ? 'cursor-not-allowed opacity-70' : 'hover:bg-cyan-300'
        )}
      >
        {status === 'loading' ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Sending...
          </>
        ) : (
          <>
            Send Message
            <Send className="h-4 w-4" />
          </>
        )}
      </button>
    </form>
  );
}
