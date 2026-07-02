import * as d3 from "d3";
import { useEffect, useRef, useState } from "react";
import type { Archetype } from "../store";
import { TIER_D3_SYMBOL } from "../utils/shapes";

interface EnrichedSource {
	sourceId: string;
	name: string;
	tier: number;
	R_orig: number;
	R_val: number;
	archetype: Archetype;
}

const ARCHETYPE_FILL: Record<string, string> = {
	EARLY_BREAKER: "var(--nn-navy)",
	NOISE_GENERATOR: "var(--nn-red)",
	SELECTIVE_ACCURATE: "var(--nn-teal)",
	CONSENSUS_FOLLOWER: "var(--nn-slate)",
};

interface Props {
	data: EnrichedSource[];
	hoveredId: string | null;
	onHoverPosition?: (id: string | null, x: number, y: number) => void;
	onSelect: (id: string) => void;
}

export default function ScatterPlot({
	data,
	hoveredId,
	onHoverPosition,
	onSelect,
}: Props) {
	const svgRef = useRef<SVGSVGElement>(null);
	const containerRef = useRef<HTMLDivElement>(null);
	const [dimensions, setDimensions] = useState({ w: 0, h: 0 });

	// ResizeObserver — only update when dimensions actually change (≥2px)
	useEffect(() => {
		const el = containerRef.current;
		if (!el) return;
		const obs = new ResizeObserver(([entry]) => {
			const { width, height } = entry.contentRect;
			if (!width || !height) return;
			setDimensions((prev) => {
				if (Math.abs(prev.w - width) > 1 || Math.abs(prev.h - height) > 1) {
					return { w: Math.round(width), h: Math.round(height) };
				}
				return prev;
			});
		});
		obs.observe(el);
		return () => obs.disconnect();
	}, []);

	// ── Data / layout effect (axes, quadrants, markers) ──────────────────
	// hoveredId is deliberately excluded — hover is applied in a separate,
	// lightweight effect below that only tweaks opacity on existing markers.
	// Including hoveredId triggers svg.selectAll("*").remove() on every hover,
	// which recreates DOM elements under the cursor and fires mouseenter again,
	// creating an infinite cycle.
	useEffect(() => {
		const svg = d3.select(svgRef.current);
		if (!svg.node()) return;
		svg.selectAll("*").remove();

		const node = svg.node();
		if (!node) return;
		const { width, height } = node.getBoundingClientRect();

		const xScale = d3.scaleLinear().domain([0, 100]).range([0, width]);
		const yScale = d3.scaleLinear().domain([0, 100]).range([height, 0]);

		const xAxis = d3.axisBottom(xScale).tickFormat(d3.format("d"));
		const yAxis = d3.axisLeft(yScale).tickFormat(d3.format("d"));

		// Quadrant backgrounds
		svg.append("rect").attr("x", xScale(50)).attr("y", yScale(100))
			.attr("width", width - xScale(50)).attr("height", yScale(50))
			.attr("fill", "var(--nn-navy)").attr("opacity", 0.09);
		svg.append("rect").attr("x", xScale(50)).attr("y", yScale(50))
			.attr("width", width - xScale(50)).attr("height", yScale(50))
			.attr("fill", "var(--nn-red)").attr("opacity", 0.09);
		svg.append("rect").attr("x", 0).attr("y", yScale(100))
			.attr("width", xScale(50)).attr("height", yScale(50))
			.attr("fill", "var(--nn-teal)").attr("opacity", 0.09);
		svg.append("rect").attr("x", 0).attr("y", yScale(50))
			.attr("width", xScale(50)).attr("height", yScale(50))
			.attr("fill", "var(--nn-slate)").attr("opacity", 0.09);

		// Quadrant labels
		svg.append("text").attr("x", width - 10).attr("y", 18)
			.attr("text-anchor", "end").attr("fill", "var(--nn-navy)")
			.style("font-weight", "600").style("font-size", "11.5px")
			.text("EARLY BREAKERS");
		svg.append("text").attr("x", width - 10).attr("y", yScale(0) - 10)
			.attr("text-anchor", "end").attr("fill", "var(--nn-red)")
			.style("font-weight", "600").style("font-size", "11.5px")
			.text("NOISE GENERATORS");
		svg.append("text").attr("x", 10).attr("y", 18)
			.attr("text-anchor", "start").attr("fill", "var(--nn-teal)")
			.style("font-weight", "600").style("font-size", "11.5px")
			.text("SELECTIVE BUT ACCURATE");
		svg.append("text").attr("x", 10).attr("y", yScale(0) - 10)
			.attr("text-anchor", "start").attr("fill", "var(--nn-slate)")
			.style("font-weight", "600").style("font-size", "11.5px")
			.text("CONSENSUS FOLLOWERS");

		// Axes
		svg.append("g").call(xAxis).attr("transform", `translate(0,${yScale(0)})`);
		svg.append("g").call(yAxis).attr("transform", `translate(${xScale(0)},0)`);

		// Data markers
		if (data.length > 0) {
			const symbol = d3.symbol().size(120);
			svg.selectAll("path.marker").data(data).enter().append("path")
				.attr("class", "marker")
				.attr("d", (d) => symbol.type(TIER_D3_SYMBOL[d.tier] ?? d3.symbolCircle)() ?? "")
				.attr("transform", (d) => `translate(${xScale(d.R_orig)},${yScale(d.R_val)})`)
				.attr("fill", (d) => ARCHETYPE_FILL[d.archetype ?? "CONSENSUS_FOLLOWER"] ?? "var(--nn-slate)")
				.attr("stroke", "var(--nn-bg)").attr("stroke-width", 1).attr("opacity", 1)
				.attr("role", "button").attr("tabindex", 0)
				.attr("aria-label", (d) => `${d.name}, Origination ${Math.round(d.R_orig)}, Validation ${Math.round(d.R_val)}`)
				.style("cursor", "pointer")
				.on("mouseenter", (_event, d) => {
					// ponytail: only call onHoverPosition — it sets both hover ID and position.
					// Calling onHover here too would double-set hover state.
					onHoverPosition?.(d.sourceId, _event.pageX, _event.pageY);
				})
				.on("mouseleave", () => {
					onHoverPosition?.(null, 0, 0);
				})
				.on("click", (_e, d) => onSelect(d.sourceId))
				.on("keydown", (event, d) => {
					if (event.key === "Enter" || event.key === " ") {
						event.preventDefault();
						onSelect(d.sourceId);
					}
				});
		}
	}, [data, onHoverPosition, onSelect, dimensions]);

	// ── Hover effect — lightweight, only tweaks opacity on existing markers ─
	// This runs on every hover change WITHOUT destroying/recreating DOM elements,
	// breaking the mouseenter→destroy→recreate→mouseenter infinite loop.
	useEffect(() => {
		const svg = d3.select(svgRef.current);
		if (!svg.node()) return;
		const markers = svg.selectAll<SVGPathElement, EnrichedSource>("path.marker");
		if (markers.empty()) return;
		if (hoveredId) {
			markers.attr("opacity", (d) => (d.sourceId === hoveredId ? 1 : 0.15));
		} else {
			markers.attr("opacity", 1);
		}
	}, [hoveredId]);

	return (
		<div ref={containerRef} className="relative h-[380px] w-full">
			<svg ref={svgRef} className="h-full w-full" />
		</div>
	);
}
