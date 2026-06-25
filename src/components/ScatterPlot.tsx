import * as d3 from "d3";
import { useEffect, useRef, useState } from "react";

interface EnrichedSource {
	sourceId: string;
	name: string;
	tier: number;
}

interface Props {
	data: EnrichedSource[];
	hoveredId: string | null;
	onHover: (id: string | null) => void;
	onSelect: (id: string) => void;
}

export default function ScatterPlot({
	data: _data,
	hoveredId: _hoveredId,
	onHover: _onHover,
	onSelect: _onSelect,
}: Props) {
	const svgRef = useRef<SVGSVGElement>(null);
	const containerRef = useRef<HTMLDivElement>(null);
	const [, setSize] = useState(0);

	// Re-render when container resizes
	useEffect(() => {
		const el = containerRef.current;
		if (!el) return;
		const obs = new ResizeObserver(() => setSize((n) => n + 1));
		obs.observe(el);
		return () => obs.disconnect();
	}, []);

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

		// Top-right quadrant — EARLY BREAKERS (navy)
		svg
			.append("rect")
			.attr("x", xScale(50))
			.attr("y", yScale(100))
			.attr("width", width - xScale(50))
			.attr("height", yScale(50))
			.attr("fill", "var(--nn-navy)")
			.attr("opacity", 0.09);

		// Bottom-right quadrant — NOISE GENERATORS (red)
		svg
			.append("rect")
			.attr("x", xScale(50))
			.attr("y", yScale(50))
			.attr("width", width - xScale(50))
			.attr("height", yScale(50))
			.attr("fill", "var(--nn-red)")
			.attr("opacity", 0.09);

		// Top-left quadrant — SELECTIVE BUT ACCURATE (teal)
		svg
			.append("rect")
			.attr("x", 0)
			.attr("y", yScale(100))
			.attr("width", xScale(50))
			.attr("height", yScale(50))
			.attr("fill", "var(--nn-teal)")
			.attr("opacity", 0.09);

		// Bottom-left quadrant — CONSENSUS FOLLOWERS (slate)
		svg
			.append("rect")
			.attr("x", 0)
			.attr("y", yScale(50))
			.attr("width", xScale(50))
			.attr("height", yScale(50))
			.attr("fill", "var(--nn-slate)")
			.attr("opacity", 0.09);

		// Quadrant labels
		svg
			.append("text")
			.attr("x", width - 10)
			.attr("y", 18)
			.attr("text-anchor", "end")
			.attr("fill", "var(--nn-navy)")
			.style("font-weight", "600")
			.style("font-size", "11.5px")
			.text("EARLY BREAKERS");

		svg
			.append("text")
			.attr("x", width - 10)
			.attr("y", yScale(0) - 10)
			.attr("text-anchor", "end")
			.attr("fill", "var(--nn-red)")
			.style("font-weight", "600")
			.style("font-size", "11.5px")
			.text("NOISE GENERATORS");

		svg
			.append("text")
			.attr("x", 10)
			.attr("y", 18)
			.attr("text-anchor", "start")
			.attr("fill", "var(--nn-teal)")
			.style("font-weight", "600")
			.style("font-size", "11.5px")
			.text("SELECTIVE BUT ACCURATE");

		svg
			.append("text")
			.attr("x", 10)
			.attr("y", yScale(0) - 10)
			.attr("text-anchor", "start")
			.attr("fill", "var(--nn-slate)")
			.style("font-weight", "600")
			.style("font-size", "11.5px")
			.text("CONSENSUS FOLLOWERS");

		// X and Y axes
		svg
			.append("g")
			.call(xAxis)
			.attr("transform", `translate(0,${yScale(0)})`);
		svg
			.append("g")
			.call(yAxis)
			.attr("transform", `translate(${xScale(0)},0)`);
	}, []);

	return (
		<div ref={containerRef} className="relative h-[380px] w-full">
			<svg ref={svgRef} className="h-full w-full" />
		</div>
	);
}
