import type { VerticalThresholdKey } from "../data/thresholds";
import { VERTICAL_LABELS, VERTICAL_ORDER } from "../data/thresholds";

interface Props {
	vertical: VerticalThresholdKey;
	onChange: (v: VerticalThresholdKey) => void;
}

export default function VerticalPills({ vertical, onChange }: Props) {
	return (
		<div className="flex gap-2">
			{VERTICAL_ORDER.map((v) => (
				<button
					key={v}
					type="button"
					onClick={() => onChange(v)}
					className={`rounded-full border px-4 py-1.5 font-heading text-[0.78rem] font-semibold transition-colors ${
						v === vertical
							? "border-[var(--nn-navy)] text-[var(--nn-navy)]"
							: "border-[var(--nn-border)] text-[var(--nn-text-dim)] hover:border-[var(--nn-text-dim)] hover:text-[var(--nn-text)]"
					}`}
					style={
						v === vertical
							? {
									backgroundColor:
										"color-mix(in srgb, var(--nn-navy) 10%, transparent)",
								}
							: undefined
					}
				>
					{VERTICAL_LABELS[v]}
				</button>
			))}
		</div>
	);
}
