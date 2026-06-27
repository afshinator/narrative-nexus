import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { App } from "./App.tsx";
import { useStore } from "./store";

createRoot(document.getElementById("root")!).render(
	<StrictMode>
		<App />
	</StrictMode>,
);

// Apply theme class to <html> on startup and on every theme change.
// Read persisted theme from localStorage before Zustand rehydrates to avoid
// a dark-theme flash on light-theme users (review-03 M01).
const getPersistedTheme = (): string => {
	try {
		const raw = localStorage.getItem("nn-store");
		if (raw) return JSON.parse(raw)?.state?.theme ?? "dark";
	} catch {
		/* ignore parse errors */
	}
	return "dark";
};
document.documentElement.classList.toggle(
	"dark",
	getPersistedTheme() === "dark",
);

const unsub = useStore.subscribe((state) => {
	document.documentElement.classList.toggle("dark", state.theme === "dark");
	document.documentElement.style.setProperty(
		"--font-scale",
		String(state.fontScale),
	);
});

// Clean up on Vite HMR to prevent subscription leaks (review-03 L04)
if (import.meta.hot) {
	import.meta.hot.dispose(() => {
		unsub();
	});
}
