import type { ReactNode } from "react";

interface Props {
	content: string;
	children: ReactNode;
}

/** Inline tooltip — hover triggers a small popup with design-token styling.
 *  Used for vocabulary explanations, axis labels, archetype names, etc. */
export default function Tooltip({ content, children }: Props) {
	return (
		<span className="group relative cursor-help border-b border-dotted border-[var(--nn-text-dim)]">
			{children}
			<span className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-1.5 -translate-x-1/2 max-w-[320px] whitespace-normal rounded-[8px] border border-[var(--nn-border)] bg-[var(--nn-surface)] px-2.5 py-1.5 font-sans text-[0.78rem] leading-relaxed text-[var(--nn-text)] opacity-0 shadow-lg transition-opacity duration-150 group-hover:opacity-100">
				{content}
			</span>
		</span>
	);
}
