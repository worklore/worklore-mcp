const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const calls = [];
const connect = { disabled: false };
let destination;
const root = { className: "", innerHTML: "", insertAdjacentHTML() {} };
const responses = {
  "/api/me": { id: "u_rivera", name: "T. Rivera" },
  "/api/intervals/status": { connected: false, status: "disconnected" },
  "/api/intervals/auth/init": { authorize_url: "https://intervals.icu/oauth/authorize?test=1" },
};
const context = {
  localStorage: { getItem: () => "tok-rivera" },
  document: { getElementById: id => id === "app" ? root : id === "connect" ? connect : null },
  fetch: async (path, opts) => {
    calls.push({ path, opts });
    return { ok: true, json: async () => responses[path] };
  },
  window: { location: { assign: url => { destination = url; } } },
};

vm.runInNewContext(fs.readFileSync("static/app.js", "utf8"), context);

(async () => {
  await new Promise(setImmediate);
  assert.match(root.innerHTML, /Connect Intervals\.icu/);
  await connect.onclick();
  const init = calls.find(call => call.path === "/api/intervals/auth/init");
  assert.equal(init.opts.headers.Authorization, "Bearer tok-rivera");
  assert.equal(destination, responses["/api/intervals/auth/init"].authorize_url);
})().catch(error => { console.error(error); process.exitCode = 1; });
