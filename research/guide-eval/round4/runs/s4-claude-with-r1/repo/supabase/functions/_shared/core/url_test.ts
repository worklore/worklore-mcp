import { assertEquals } from "jsr:@std/assert@1";
import { urlKey } from "./url.ts";

Deno.test("urlKey: scheme/host case, www., trailing slash, fragment", () => {
  assertEquals(urlKey("https://worklore.dev/"), "https://worklore.dev");
  assertEquals(urlKey("HTTPS://WWW.Worklore.dev"), "https://worklore.dev");
  assertEquals(urlKey("https://worklore.dev/Docs/?a=1#x"), "https://worklore.dev/Docs/?a=1");
  assertEquals(urlKey("https://worklore.dev/docs//"), "https://worklore.dev/docs");
  assertEquals(urlKey("www.worklore.dev/"), "https://worklore.dev");
  assertEquals(urlKey("  "), null);
  assertEquals(urlKey(null), null);
});
