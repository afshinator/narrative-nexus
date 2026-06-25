import "@testing-library/jest-dom/vitest";

// radix-ui Slider uses ResizeObserver internally — not available in jsdom
globalThis.ResizeObserver = class {
	observe() {}
	unobserve() {}
	disconnect() {}
} as unknown as typeof ResizeObserver;
