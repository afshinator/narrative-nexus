import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { parse } from "yaml";

const composePath = resolve(import.meta.dirname, "../../../docker-compose.yml");

function loadCompose(): Record<string, unknown> {
  const raw = readFileSync(composePath, "utf8");
  return parse(raw) as Record<string, unknown>;
}

describe("docker-compose.yml", () => {
  it("exists at project root", () => {
    expect(() => readFileSync(composePath, "utf8")).not.toThrow();
  });

  it("parses as valid YAML", () => {
    expect(() => loadCompose()).not.toThrow();
  });

  it("has services section", () => {
    const compose = loadCompose();
    expect(compose.services).toBeDefined();
  });

  it("has exactly 3 services", () => {
    const compose = loadCompose();
    const services = compose.services as Record<string, unknown>;
    expect(Object.keys(services)).toHaveLength(3);
  });

  describe("app service", () => {
    it("is defined", () => {
      const compose = loadCompose();
      const services = compose.services as Record<string, unknown>;
      expect(services.app).toBeDefined();
    });

    it("exposes port 8000", () => {
      const compose = loadCompose();
      const services = compose.services as Record<string, unknown>;
      const app = services.app as Record<string, unknown>;
      expect(app.ports).toBeDefined();
      const ports = app.ports as string[];
      expect(ports.some((p) => p.startsWith("8000:"))).toBe(true);
    });

    it("has nn-data volume mount", () => {
      const compose = loadCompose();
      const services = compose.services as Record<string, unknown>;
      const app = services.app as Record<string, unknown>;
      const volumes = app.volumes as string[];
      expect(volumes.some((v) => v.startsWith("nn-data"))).toBe(true);
    });

    it("is on nn-network", () => {
      const compose = loadCompose();
      const services = compose.services as Record<string, unknown>;
      const app = services.app as Record<string, unknown>;
      const networks = app.networks as string[] | Record<string, unknown>;
      const names = Array.isArray(networks) ? networks : Object.keys(networks);
      expect(names).toContain("nn-network");
    });
  });

  describe("worker service", () => {
    it("is defined", () => {
      const compose = loadCompose();
      const services = compose.services as Record<string, unknown>;
      expect(services.worker).toBeDefined();
    });

    it("has no published ports", () => {
      const compose = loadCompose();
      const services = compose.services as Record<string, unknown>;
      const worker = services.worker as Record<string, unknown>;
      // Worker should not have ports exposed externally
      expect(worker.ports || []).toEqual([]);
    });

    it("is on nn-network", () => {
      const compose = loadCompose();
      const services = compose.services as Record<string, unknown>;
      const worker = services.worker as Record<string, unknown>;
      const networks = worker.networks as string[] | Record<string, unknown>;
      const names = Array.isArray(networks) ? networks : Object.keys(networks);
      expect(names).toContain("nn-network");
    });
  });

  describe("db service", () => {
    it("is defined", () => {
      const compose = loadCompose();
      const services = compose.services as Record<string, unknown>;
      expect(services.db).toBeDefined();
    });

    it("has nn-data volume mount", () => {
      const compose = loadCompose();
      const services = compose.services as Record<string, unknown>;
      const db = services.db as Record<string, unknown>;
      const volumes = db.volumes as string[];
      expect(volumes.some((v) => v.startsWith("nn-data"))).toBe(true);
    });
  });

  describe("networks", () => {
    it("defines nn-network as bridge", () => {
      const compose = loadCompose();
      const networks = compose.networks as Record<string, unknown>;
      expect(networks).toHaveProperty("nn-network");
      const nn = networks["nn-network"] as Record<string, unknown>;
      expect(nn.driver).toBe("bridge");
    });
  });

  describe("volumes", () => {
    it("defines nn-data volume", () => {
      const compose = loadCompose();
      const volumes = compose.volumes as Record<string, unknown>;
      expect(volumes).toHaveProperty("nn-data");
    });
  });
});
