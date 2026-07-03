import type { FC } from "react";

interface Props {
	lens: "consensus" | "coverage";
	onChange: (lens: "consensus" | "coverage") => void;
}

const LensToggle: FC<Props> = ({ lens, onChange }) => {
	const base =
		"rounded-full px-[14px] py-[6px] font-sans text-[13px] transition-colors cursor-pointer border-0";
	const active = `${base} bg-[var(--nn-navy-dim)] text-[var(--nn-navy)] font-medium`;
	const inactive = `${base} text-[var(--nn-text-dim)] hover:text-[var(--nn-text)]`;

	return (
		<div className="inline-flex gap-1 rounded-full border border-[var(--nn-border)] bg-[var(--nn-surface2)] p-[3px]">
			<button
				type="button"
				className={lens === "consensus" ? active : inactive}
				onClick={() => onChange("consensus")}
			>
				Consensus
			</button>
			<button
				type="button"
				className={lens === "coverage" ? active : inactive}
				onClick={() => onChange("coverage")}
			>
				Coverage
			</button>
		</div>
	);
};

export default LensToggle;
