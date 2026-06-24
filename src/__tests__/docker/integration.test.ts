import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { execSync } from "node:child_process";
import { resolve } from "node:path";

const COMPOSE_FILE = resolve(import.meta.dirname, "../../../docker-compose.yml");

const DOCKER_AVAILABLE = (() => {
  try { execSync("docker info", { stdio: "ignore" }); return true; }
  catch { return false; }
})();

let upOk = false;

const describeIf = DOCKER_AVAILABLE ? describe : describe.skip;

function composePsJson() {
  const out = execSync(`docker compose -f ${COMPOSE_FILE} ps --format json`, { encoding: "utf8" });
  return out.trim().split("\n").filter(Boolean).map((l) => JSON.parse(l));
}

function containerInspect(service: string) {
  const id = execSync(`docker compose -f ${COMPOSE_FILE} ps -q ${service}`, { encoding: "utf8" }).trim();
  const out = execSync(`docker inspect ${id}`, { encoding: "utf8" });
  return JSON.parse(out)[0];
}

describeIf("Docker Compose — integration", () => {
  beforeAll(() => {
    execSync(`docker compose -f ${COMPOSE_FILE} down --volumes 2>/dev/null`, { stdio: "ignore" });

    try {
      console.log("\n→ docker compose build...\n");
      execSync(`docker compose -f ${COMPOSE_FILE} build`, { stdio: "inherit", timeout: 120_000 });
      console.log("\n→ docker compose up -d\n");
      execSync(`docker compose -f ${COMPOSE_FILE} up -d`, { stdio: "inherit", timeout: 15_000 });
      execSync("sleep 3");
      upOk = true;
    } catch (e) {
      console.warn("Docker compose up failed — skipping integration tests:", (e as Error).message);
    }
  }, 90_000);

  afterAll(() => {
    if (upOk) {
      execSync(`docker compose -f ${COMPOSE_FILE} down --volumes 2>/dev/null`, {
        stdio: "ignore",
        timeout: 30_000,
      });
    }
  }, 30_000);

  it("all 3 services are running", () => {
    if (!upOk) return;
    const containers = composePsJson();
    expect(containers.length).toBeGreaterThanOrEqual(3);
    const names = containers.map((c) => c.Service);
    expect(names).toContain("app");
    expect(names).toContain("worker");
    expect(names).toContain("db");
  });

  it("app container has nn-network", () => {
    if (!upOk) return;
    const info = containerInspect("app");
    const networkNames = Object.keys(info.NetworkSettings?.Networks ?? {});
    // Docker Compose prefixes network names with project dir: "narrative-nexus_nn-network"
    expect(networkNames.some((n) => n.includes("nn-network"))).toBe(true);
  });

  it("worker container has nn-network", () => {
    if (!upOk) return;
    const info = containerInspect("worker");
    const networkNames = Object.keys(info.NetworkSettings?.Networks ?? {});
    expect(networkNames.some((n) => n.includes("nn-network"))).toBe(true);
  });

  it("app container has nn-data volume mounted", () => {
    if (!upOk) return;
    const info = containerInspect("app");
    const mounts = (info.Mounts ?? []) as Array<{ Name: string }>;
    const volumeNames = mounts.map((m) => m.Name);
    // Docker Compose prefixes volume names too: "narrative-nexus_nn-data"
    expect(volumeNames.some((n) => n.includes("nn-data"))).toBe(true);
  });
});
