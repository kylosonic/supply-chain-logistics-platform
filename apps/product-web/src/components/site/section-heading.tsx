import { cn } from '@/lib/cn';

type SectionHeadingProps = {
  eyebrow: string;
  title: string;
  description: string;
  align?: 'left' | 'center';
};

export function SectionHeading({ eyebrow, title, description, align = 'left' }: SectionHeadingProps) {
  return (
    <div className={cn('max-w-3xl space-y-4', align === 'center' ? 'mx-auto text-center' : '')}>
      <p className="kicker">{eyebrow}</p>
      <h2 className="font-display text-[clamp(2rem,4vw,3.6rem)] leading-[0.96] text-white">{title}</h2>
      <p className="max-w-2xl text-sm leading-7 text-white/64">{description}</p>
    </div>
  );
}