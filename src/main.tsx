import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { useStore } from "./store";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

// Apply theme class to <html> on startup and on every theme change
document.documentElement.classList.toggle(
  "dark",
  useStore.getState().theme === "dark",
);

useStore.subscribe((state) => {
  document.documentElement.classList.toggle("dark", state.theme === "dark");
});
