/* comms.js — shared browser<->Claude wiring for interactive dashboards.
 * Served by the engine at /assets/comms.js. Patterns include it only in
 * interactive mode. Exposes window.Dash. No-ops gracefully with no server
 * (falls back to localStorage for state). */
(function () {
  const KEY = "dash-state-" + location.pathname;
  const Dash = {
    async loadState() {
      try {
        const r = await fetch("/state", { cache: "no-store" });
        if (r.ok) return await r.json();
      } catch (e) {}
      try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { return {}; }
    },
    async saveState(state) {
      try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
      try {
        await fetch("/state", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(state),
        });
      } catch (e) {}
    },
    async ping(elementId, payload) {
      const body = Object.assign({ testId: elementId }, payload || {});
      try {
        await fetch("/ping", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        return true;
      } catch (e) { return false; }
    },
    /* Poll for new replies; calls cb(reply) for each. Tracks last-seen id. */
    onReplies(cb, intervalMs) {
      let last = 0;
      const tick = async () => {
        try {
          const r = await fetch("/replies/since/" + last, { cache: "no-store" });
          if (r.ok) {
            const items = await r.json();
            for (const reply of items) {
              if (Number(reply.id) > Number(last)) last = reply.id;
              cb(reply);
            }
          }
        } catch (e) {}
      };
      tick();
      return setInterval(tick, intervalMs || 2500);
    },
  };
  window.Dash = Dash;
})();
