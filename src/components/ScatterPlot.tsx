import * as d3 from "d3";
import { useEffect, useRef, useState } from "react";
import type { Archetype } from "../store";
import { TIER_D3_SYMBOL } from "../utils/shapes";

interface EnrichedSource {
	sourceId: string;
	name: string;
	tier: number;
	R_orig: number;
	R_val: number | null;
	archetype: Archetype;
}

const ARCHETYPE_FILL: Record<string, string> = {
	EARLY_BREAKER: "var(--nn-navy)",
	NOISE_GENERATOR: "var(--nn-red)",
	SELECTIVE_ACCURATE: "var(--nn-teal)",
	CONSENSUS_FOLLOWER: "var(--nn-slate)",
};

interface Region {
	yMin: number;
	yMax: number;
	label: string;
	sublabel?: string;
}

interface Props {
	data: EnrichedSource[];
	hoveredId: string | null;
	onHoverPosition?: (id: string | null, x: number, y: number) => void;
	onSelect: (id: string) => void;
	xScale?: "linear" | "log";
	xLabel?: string;
	yLabel?: string;
	regions?: Region[];
	showQuadrants?: boolean;
}

// E1: standard D3 margin convention. Enough space for:
//  - quadrant labels (11.5px font) at top
//  - y-axis label + tick text (11px) at left
//  - x-axis label + tick text (11px) at bottom
//  - quadrant labels at right
//  - dots at extremes (max radius ~11px)
const M = { top: 32, right: 28, bottom: 38, left: 44 };

export default function ScatterPlot({
	data,
	hoveredId,
	onHoverPosition,
	onSelect,
	xScale: xScaleType = "linear",
	xLabel = "Origination",
	yLabel = "Validation",
	regions,
	showQuadrants = true,
}: Props) {
	// Reduce bottom margin when no x-axis label (coverage landscape mode)
	const adjustedM = { ...M, bottom: xLabel ? M.bottom : 18 };
	const svgRef = useRef<SVGSVGElement>(null);
	const containerRef = useRef<HTMLDivElement>(null);
	const [dimensions, setDimensions] = useState({ w: 0, h: 0 });

	// ResizeObserver
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

	// ── Data / layout effect ──
	useEffect(() => {
		const svg = d3.select(svgRef.current);
		if (!svg.node()) return;
		svg.selectAll("*").remove();

		const node = svg.node();
		if (!node) return;
		const { width, height } = node.getBoundingClientRect();

		// Plot area = SVG minus margins (fallback to minimum on jsdom)
		const pw = Math.max(width - adjustedM.left - adjustedM.right, 300);
		const ph = Math.max(height - adjustedM.top - adjustedM.bottom, 200);

		// Root group, translated to the plot area
		const g = svg.append("g").attr("transform", `translate(${adjustedM.left},${adjustedM.top})`);

		// Scales: domain [0,100] → plot area (pw × ph)
		const xScale = xScaleType === "log"
			? d3.scaleLog().domain([1, d3.max(data, (d) => d.R_orig) || 100]).range([0, pw])
			: d3.scaleLinear().domain([0, 100]).range([0, pw]);
		const yScale = d3.scaleLinear().domain([0, 100]).range([ph, 0]);

		// Axes
		const xAxis = d3.axisBottom(xScale).tickFormat(d3.format("d"));
		const yAxis = d3.axisLeft(yScale).tickFormat(d3.format("d"));

		// Region backgrounds
		if (regions) {
			for (const r of regions) {
				const ry = yScale(r.yMax);
				const rh = yScale(r.yMin) - yScale(r.yMax);
				g.append("rect")
					.attr("x", 0).attr("y", ry)
					.attr("width", pw).attr("height", Math.max(0, rh))
					.attr("fill", "var(--nn-surface2)").attr("opacity", 0.4);
				g.append("text")
					.attr("x", 8).attr("y", ry + 16)
					.attr("fill", "var(--nn-text-dim)")
					.style("font-family", "IBM Plex Sans").style("font-size", "12px")
					.style("font-weight", "600")
					.text(r.label);
				if (r.sublabel) {
					g.append("text")
						.attr("x", 8).attr("y", ry + 32)
						.attr("fill", "var(--nn-text-dim)")
						.style("font-family", "IBM Plex Sans").style("font-size", "11px")
						.text(r.sublabel);
				}
			}
		}

		// Quadrant backgrounds + labels — inside plot area
		if (showQuadrants) {
			const mx = xScale(50);
			const my = yScale(50);
			g.append("rect").attr("x", mx).attr("y", 0).attr("width", pw - mx).attr("height", my)
				.attr("fill", "var(--nn-navy)").attr("opacity", 0.09);
			g.append("rect").attr("x", mx).attr("y", my).attr("width", pw - mx).attr("height", ph - my)
				.attr("fill", "var(--nn-red)").attr("opacity", 0.09);
			g.append("rect").attr("x", 0).attr("y", 0).attr("width", mx).attr("height", my)
				.attr("fill", "var(--nn-teal)").attr("opacity", 0.09);
			g.append("rect").attr("x", 0).attr("y", my).attr("width", mx).attr("height", ph - my)
				.attr("fill", "var(--nn-slate)").attr("opacity", 0.09);

			// Labels: inset 8px from plot corners, semi-transparent, behind dots
			g.append("text").attr("x", pw - 8).attr("y", 16)
				.attr("text-anchor", "end").attr("fill", "var(--nn-navy)")
				.attr("opacity", 0.7)
				.style("font-weight", "600").style("font-size", "11.5px")
				.text("EARLY BREAKERS");
			g.append("text").attr("x", pw - 8).attr("y", ph - 8)
				.attr("text-anchor", "end").attr("fill", "var(--nn-red)")
				.attr("opacity", 0.7)
				.style("font-weight", "600").style("font-size", "11.5px")
				.text("UNMATCHED BREAKERS");
			g.append("text").attr("x", 8).attr("y", 16)
				.attr("text-anchor", "start").attr("fill", "var(--nn-teal)")
				.attr("opacity", 0.7)
				.style("font-weight", "600").style("font-size", "11.5px")
				.text("LATE BUT RELIABLE");
			g.append("text").attr("x", 8).attr("y", ph - 8)
				.attr("text-anchor", "start").attr("fill", "var(--nn-slate)")
				.attr("opacity", 0.7)
				.style("font-weight", "600").style("font-size", "11.5px")
				.text("CONSENSUS ECHO");
		}

		// Axes (drawn in plot coordinate space)
		g.append("g").call(xAxis).attr("transform", `translate(0,${ph})`);
		g.append("g").call(yAxis);

		// Axis labels — positioned in SVG space (outside margins)
		svg.append("text")
			.attr("x", adjustedM.left + pw / 2).attr("y", height - 4)
			.attr("text-anchor", "middle")
			.attr("fill", "var(--nn-text-dim)")
			.style("font-family", "IBM Plex Sans").style("font-size", "11px")
			.text(xLabel);
		svg.append("text")
			.attr("x", adjustedM.left - 8).attr("y", adjustedM.top + ph / 2)
			.attr("text-anchor", "middle")
			.attr("transform", `rotate(-90, ${adjustedM.left - 8}, ${adjustedM.top + ph / 2})`)
			.attr("fill", "var(--nn-text-dim)")
			.style("font-family", "IBM Plex Sans").style("font-size", "11px")
			.text(yLabel);

		// Data markers — in plot coordinates
		if (data.length > 0) {
			const symbol = d3.symbol().size(120);
			g.selectAll("path.marker").data(data).enter().append("path")
				.attr("class", "marker")
				.attr("d", (d) => symbol.type(TIER_D3_SYMBOL[d.tier] ?? d3.symbolCircle)() ?? "")
				.attr("transform", (d) => `translate(${xScale(d.R_orig)},${yScale(d.R_val ?? 0)})`)
				.attr("fill", (d) => ARCHETYPE_FILL[d.archetype ?? "CONSENSUS_FOLLOWER"] ?? "var(--nn-slate)")
				.attr("stroke", "var(--nn-bg)").attr("stroke-width", 1).attr("opacity", 1)
				.attr("role", "button").attr("tabindex", 0)
				.attr("aria-label", (d) => `${d.name}, Origination ${Math.round(d.R_orig)}, Validation ${d.R_val != null ? Math.round(d.R_val) : "ungraded"}`)
				.style("cursor", "pointer")
				.on("mouseenter", (_event, d) => {
					onHoverPosition?.(d.sourceId, _event.clientX, _event.clientY);
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

	// ── Hover effect ──
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
