import { cn } from '@/lib/cn';

type SectionHeadingProps = {
  eyebrow: string;
  title: string;
  description: string;
  align?: 'left' | 'center';
};

export function SectionHeading({ eyebrow, title, description, align = 'left' }: SectionHeadingProps) {
  return (
    <div className={cn('max-w-[50rem] space-y-4', align === 'center' ? 'mx-auto text-center [&>h2]:mx-auto [&>p]:mx-auto' : '')}>
      <p className="kicker">{eyebrow}</p>
      <h2 className="balanced-headline max-w-[16ch] font-display text-[clamp(2rem,4vw,3.45rem)] leading-[0.96] tracking-[-0.03em] text-white">{title}</h2>
      <p className="max-w-[42rem] text-sm leading-7 text-white/64 sm:text-base sm:leading-8">{description}</p>
    </div>
  );
}