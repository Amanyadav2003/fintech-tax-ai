import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, BarChart3, Check, Coins, ShieldCheck, Target } from 'lucide-react';

const features = [
  { icon: '◈', title: 'AI-powered clarity', text: 'Understand your tax position with plain-English analysis built around your finances.' },
  { icon: '↗', title: 'Find more savings', text: 'Surface overlooked deductions and compare regimes before you file.' },
  { icon: '✓', title: 'Private by design', text: 'Your financial information stays protected with secure account controls.' },
];

function LandingPage({ onGetStarted }) {
  return (
    <main className="min-h-screen overflow-hidden bg-transparent">
      <nav className="border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5 lg:px-8">
          <div className="flex items-center gap-3 text-navy-900">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-navy-700 text-lg font-bold text-white">T</div>
            <span className="text-sm font-bold tracking-[0.2em]">TAXMATE AI</span>
          </div>
          <button onClick={onGetStarted} className="fintech-button px-4 py-2 text-sm">Get started <span className="ml-2">→</span></button>
        </div>
      </nav>

      <section className="relative border-b border-slate-200 bg-white/75">
        <div className="pointer-events-none absolute right-0 top-0 h-full w-1/2 bg-[radial-gradient(circle_at_70%_25%,rgba(45,95,139,0.14),transparent_58%)]" />
        <div className="relative mx-auto grid max-w-7xl items-center gap-14 px-5 py-20 lg:grid-cols-[1.05fr_0.95fr] lg:px-8 lg:py-28">
          <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-mint-500/30 bg-mint-50 px-3 py-1.5 text-xs font-bold uppercase tracking-[0.16em] text-mint-700">
              <span className="h-2 w-2 rounded-full bg-mint-500" /> Built for confident filing
            </div>
            <h1 className="max-w-3xl text-5xl font-bold leading-[1.05] tracking-tight text-navy-900 sm:text-6xl lg:text-7xl">Tax decisions, made <span className="text-navy-500">clear.</span></h1>
            <p className="mt-7 max-w-xl text-lg leading-8 text-slate-600">A calmer way to understand your taxes, uncover legitimate savings, and move from uncertainty to an informed plan.</p>
            <div className="mt-9 flex flex-col gap-4 sm:flex-row sm:items-center">
              <button onClick={onGetStarted} className="fintech-button px-6 py-3.5">Start your free analysis <ArrowRight className="ml-3 h-5 w-5" /></button>
              <span className="text-sm text-slate-500">No credit card required</span>
            </div>
            <div className="mt-12 flex flex-wrap gap-x-8 gap-y-3 border-t border-slate-200 pt-6 text-sm text-slate-500">
              <span className="flex items-center gap-2"><Check className="h-4 w-4 text-mint-700" /> Encrypted account data</span>
              <span className="flex items-center gap-2"><Check className="h-4 w-4 text-mint-700" /> India-first tax guidance</span>
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.6, delay: 0.15 }} className="relative mx-auto w-full max-w-md pb-2">
            <div className="rounded-2xl border border-navy-100 bg-navy-900 p-5 shadow-2xl shadow-navy-900/20">
              <div className="flex items-center justify-between border-b border-white/10 pb-5 text-white"><span className="text-sm font-semibold">Your tax overview</span><span className="rounded-full bg-white/10 px-3 py-1 text-xs text-slate-300">FY 2025-26</span></div>
              <div className="py-8"><p className="text-xs uppercase tracking-[0.16em] text-slate-400">Estimated savings</p><p className="mt-2 text-5xl font-bold text-white">₹42,850</p><div className="mt-5 h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full w-3/4 rounded-full bg-mint-500" /></div><div className="mt-2 flex justify-between text-xs text-slate-400"><span>Analysis complete</span><span>75%</span></div></div>
              <div className="grid grid-cols-2 gap-3"><div className="rounded-lg bg-white/10 p-4"><p className="text-xs text-slate-400">Recommended</p><p className="mt-1 font-semibold text-mint-500">New regime</p></div><div className="rounded-lg bg-white/10 p-4"><p className="text-xs text-slate-400">Risk level</p><p className="mt-1 font-semibold text-white">Low</p></div></div>
            </div>
            <div className="mt-4 flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-soft"><ShieldCheck className="h-5 w-5 shrink-0 text-mint-700" /><div><p className="text-xs text-slate-500">Protected workspace</p><p className="mt-1 text-sm font-semibold text-navy-900">Bank-grade encryption</p></div></div>
            <div className="pointer-events-none absolute -right-5 top-12 hidden sm:block"><motion.div animate={{ y: [0, -12, 0] }} transition={{ duration: 4.2, repeat: Infinity, ease: 'easeInOut' }} className="flex h-14 w-14 items-center justify-center rounded-xl border border-navy-100 bg-white text-navy-500 shadow-soft"><BarChart3 className="h-7 w-7" /></motion.div></div>
            <div className="pointer-events-none absolute -left-7 top-36 hidden sm:block"><motion.div animate={{ y: [0, 14, 0] }} transition={{ duration: 5.1, repeat: Infinity, ease: 'easeInOut' }} className="flex h-14 w-14 items-center justify-center rounded-xl border border-mint-500/20 bg-mint-50 text-mint-700 shadow-soft"><Coins className="h-7 w-7" /></motion.div></div>
            <div className="pointer-events-none absolute -right-8 bottom-24 hidden sm:block"><motion.div animate={{ y: [0, -9, 0] }} transition={{ duration: 3.6, repeat: Infinity, ease: 'easeInOut' }} className="flex h-14 w-14 items-center justify-center rounded-xl border border-amber-200 bg-amber-50 text-amber-600 shadow-soft"><Target className="h-7 w-7" /></motion.div></div>
          </motion.div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-20 lg:px-8">
        <div className="max-w-2xl"><p className="text-sm font-bold uppercase tracking-[0.16em] text-navy-500">A better tax workflow</p><h2 className="mt-3 text-3xl font-bold tracking-tight text-navy-900 sm:text-4xl">The confidence to make your next move.</h2></div>
        <div className="mt-10 grid gap-5 md:grid-cols-3">{features.map((feature, index) => <motion.article key={feature.title} initial={{ opacity: 0, y: 28, scale: 0.96 }} whileInView={{ opacity: 1, y: 0, scale: 1 }} viewport={{ once: true, amount: 0.35 }} transition={{ delay: index * 0.16, duration: 0.55, ease: 'easeOut' }} className="fintech-card p-6"><div className="flex h-11 w-11 items-center justify-center rounded-lg bg-navy-50 text-xl font-bold text-navy-700">{feature.icon}</div><h3 className="mt-6 text-lg font-bold text-navy-900">{feature.title}</h3><p className="mt-3 leading-7 text-slate-600">{feature.text}</p></motion.article>)}</div>
      </section>
      <footer className="border-t border-slate-200 bg-white"><div className="mx-auto flex max-w-7xl flex-col gap-3 px-5 py-7 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between lg:px-8"><span className="font-bold tracking-[0.16em] text-navy-700">TAXMATE AI</span><span>Secure guidance for better financial decisions.</span></div></footer>
    </main>
  );
}

export default LandingPage;
