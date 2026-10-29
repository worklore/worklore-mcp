const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const calls = [];
let destination;
const connect = { disabled: false };
const root = {
  className: "",
  innerHTML: "",
  insertAdjacentHTML() { throw new Error("unexpected connection error"); },
};
const responses = {
  "/api/me": { name: "C. Okafor" },
  "/api/intervals/status": { connected: false, status: "disconnected" },
  "/api/intervals/auth/init": { authorize_url: "https://intervals.icu/oauth/authorize?state=sample" },
};
const context = {
  localStorage: { getItem: () => "tok-okafor" },
  document: {
    getElementById: id => ({ app: root, connect })[id] || null,
  },
  fetch: async (path, options) => {
    calls.push({ path, options });
    return { ok: true, json: async () => responses[path] };
  },
  window: { location: { assign: url => { destination = url; } } },
};

(async () => {
  vm.runInNewContext(fs.readFileSync("static/app.js", "utf8"), context);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(typeof connect.onclick, "function");
  await connect.onclick();
  assert.equal(calls.at(-1).path, "/api/intervals/auth/init");
  assert.equal(calls.at(-1).options.headers.Authorization, "Bearer tok-okafor");
  assert.equal(destination, responses["/api/intervals/auth/init"].authorize_url);
  console.log("Connect button sends bearer token and navigates to OAuth URL");
})().catch(error => { console.error(error); process.exitCode = 1; });
