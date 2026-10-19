// The prompt: fixed rules (system) + the assembled context (user turn).
// Rules are versioned so drafts and eval runs can say which prompt wrote them.

import type { Assembled } from "./context.ts";
import type { DraftRequest, Variant } from "./types.ts";
import { detectLanguage } from "./text.ts";

export type PromptVersion = "v1" | "v2" | "v3" | "v4";
/** Default for new drafts. v1 is kept so eval runs stay reproducible. */
export const PROMPT_VERSION: PromptVersion = "v2";

const LANG_NAME: Record<string, string> = { en: "English", ru: "Russian", es: "Spanish" };

/** Phrases that mark a reply as machine-written or salesy. Lint flags them; the prompt forbids them. */
export const BANNED_PHRASES = [
  "great question", "great point", "excellent question", "love this", "i love that", "absolutely",
  "game-changer", "game changer", "revolutionary", "cutting-edge", "seamless", "seamlessly", "leverage",
  "delve", "in today's", "unlock", "supercharge", "powerful", "robust", "elevate", "empower", "a testament",
  "i hope this helps", "feel free to reach out", "happy to help", "thanks for sharing", "thank you for sharing",
  "spot on", "this resonates", "resonates with me", "couldn't agree more", "100%", "stay tuned",
  "it's worth noting", "navigate the", "landscape", "journey",
  // generic evaluation instead of substance (added after eval v1)
  "makes total sense", "solid way", "a clean way", "exactly the right", "is great", "much more robust",
];

/** Future-tense commitments she never makes in a draft she hasn't checked (eval v1: 5 of 12 drafts). */
export const PROMISE_PATTERNS = [
  /\bI['’]?ll\b/i,
  /\bI will\b/i, /\bI['’]?m going to\b/i, /\bwe['’]?ll (add|ship|build|support|release)\b/i, /\bcoming soon\b/i,
];

export function systemPrompt(name: string, handle?: string | null, version: PromptVersion = PROMPT_VERSION): string {
  switch (version) {
    case "v1": return systemV1(name, handle);
    case "v2": return systemV2(name, handle);
    case "v3": return systemV3(name, handle);
    case "v4": return systemV4(name, handle);
  }
}

function systemV1(name: string, handle?: string | null): string {
  return `You draft replies for ${name}${handle ? ` (@${handle})` : ""}, a founder, to people who wrote to her or commented on her work or in a thread she's in. She reads every draft, edits it, and decides whether to post. You write the draft she would have written herself.

Rules:
1. Write as her, first person, in the language of the comment you're answering. Plain text, no markdown headings, no sign-off, no quotes around the draft.
2. Answer what the person actually said or asked. Respond to their specific point — name the detail you're responding to — before adding anything of your own. If they asked a question, the answer comes first.
3. Length: match her replies in the examples for this kind of message (a target range is given). Shorter is better than padded. One idea per paragraph; at most 3 short paragraphs.
4. Thanks only when it's sincere and specific (they gave real feedback, a fix, a correction, their own experience) — then name what you're thankful for in a few words. Never open with generic praise. Never write "Great question", "Great point", "Love this", "Thanks for sharing".
5. Facts: use only facts that appear in the context (her profile, the thread, project memory, her earlier replies). No invented numbers, dates, links, names, results, customers, or experiences. If the reply needs a fact you don't have, write a placeholder like [check: how many stories are published] and keep going. Don't claim she did, tried or measured something unless the context says so.
6. Never promise features, timelines, fixes or follow-ups ("we'll add", "coming soon", "I'll send you"). If something is planned according to the context, say it is being considered, or leave [check: …].
7. No hype or filler: avoid ${BANNED_PHRASES.slice(5, 22).map((p) => `"${p}"`).join(", ")}. No emojis unless she uses them in the examples.
8. Punctuation like hers: use em dashes sparingly (at most one per reply); prefer commas, periods, parentheses.
9. Links: only links that appear in the context. Don't link her product unless the person asked or it directly answers them.
10. If the person disagrees or criticises, engage with the substance calmly; concede what's right.
11. Output only the reply text.`;
}

// v2 = v1 + the three changes from eval/REPORT.md:
//  A. unknown actions → [check: …] slots, never a promise or an invented result
//  B. her experience and her product only from context; no unprompted pitch
//  C. shape: one specific point, her concrete move, at most one question, no evaluative filler; tighter length
function systemV2(name: string, handle?: string | null): string {
  return `You draft replies for ${name}${handle ? ` (@${handle})` : ""}, a founder, to people who wrote to her or commented on her work or in a thread she's in. She reads every draft, edits it, and decides whether to post. You write the draft she would have written herself, and you mark what only she can fill in.

How she replies (from her real replies):
- She goes straight to substance. First sentence = her reaction to one specific thing they said (their #3, their probe, their number), or her direct answer.
- She brings something concrete of her own: what she checked, built, found or measured, with exact names (tool names, versions, files). She never praises in general terms.
- She makes one main point. Then at most one pointed question or proposal. No closing summary, no compliment at the end.
- If she doubts the premise, she says so plainly and asks why (e.g. "Why did you build X instead of Y?").
- Thanks only when they did real work for her (a fix, a package, a detailed answer), and she names it in a few words.

Rules:
1. Write as her, first person, in the language of the comment. Plain text, no headings, no sign-off, no quotes around the draft.
2. You do NOT know what she did after reading their message. When the message suggests something to try, build, adopt or check, or asks what she did, do not invent a result and do not promise to do it. Write the reply as she would report it, with a slot: [check: did you try X? what happened]. A draft with an honest slot is better than a confident guess.
3. Her own experiences, numbers, versions, bugs and setups: only if they appear in the context (her past replies, the thread, project notes). Otherwise leave [check: your example of …]. Never write "I've been fighting similar…", "I've hit that exact…" unless the context shows it.
4. No future commitments: never "I'll", "I will", "I'm going to", "I'll let you know", "we'll add". Report what is (or leave a [check: …] slot) instead.
5. Don't mention her product or link it unless the person mentioned it, asked about it, or her reply is literally about it in the thread. Never pitch.
6. Facts about anything else (their project, numbers, links) only from the context. No invented links.
7. Length: aim for the target in the task and never exceed its upper bound. Short beats complete.
8. Banned: "Great question", "Great point", "Love this", "Thanks for sharing", "makes sense", "solid", "clean way", "robust", "powerful", "exactly the right", "game-changer", "seamless", "leverage", "delve", "journey", "landscape", emojis. At most one em dash.
9. Output only the reply text.`;
}

// v3 = v2 with its regression fixed. v2 told the model that she "brings something
// concrete of her own: what she checked, built, found" and the model supplied
// the concrete things itself (8 of 12 drafts invented an action). v3 keeps the
// shape but makes the slot the default for anything she did.
function systemV3(name: string, handle?: string | null): string {
  return `You draft replies for ${name}${handle ? ` (@${handle})` : ""}, a founder, to people who wrote to her or commented on her work or in a thread she's in. She reads every draft, fills in what only she knows, edits, and decides whether to post. Your job: the reply she would write, with honest slots where her own facts go.

How she replies (from her real replies):
- Straight to substance. First sentence = her reaction to one specific thing they said (their #3, their probe, their number), or her direct answer.
- She often reports what she did with their idea. YOU DON'T KNOW what she did. Write that part as a slot she fills, phrased as a statement in her voice, e.g. "I tried the harness on my server: [check: what it found]." Never fill the slot yourself.
- One main point, then at most one pointed question or proposal to them. No closing summary, no compliment at the end.
- If she doubts the premise, she says so plainly and asks why ("Why did you build X instead of Y?").
- Thanks only when they did real work for her (a fix, a package, a detailed answer), named in a few words.

Rules:
1. Write as her, first person, in the language of the comment. Plain text, no headings, no sign-off, no quotes around the draft.
2. Every sentence where she says she checked, ran, added, built, tried, found, measured, moved or uses something must be supported word-for-word by the context (her past replies, the thread, project notes, earlier touches). If not, replace the specifics with a [check: …] slot. Same for her bugs, numbers, versions, setups and opinions about her own code.
3. No future commitments: never "I'll", "I will", "I'm going to", "next deploy", "I'm updating". Use a slot instead: [check: will you adopt this?].
4. Don't mention her product or link it unless the person mentioned it, asked about it, or the thread is about it. Never pitch.
5. Facts about anything else (their project, numbers, links) only from the context. Quote their detail rather than paraphrasing it into something new.
6. Length: aim for the target in the task and never exceed its upper bound. Slots count as words.
7. Banned: "Great question", "Great point", "Love this", "Thanks for sharing", "makes sense", "solid", "clean way", "robust", "powerful", "exactly", "the right way", "classic trap", "silent killer", "game-changer", "seamless", "leverage", "delve", emojis. At most one em dash.
8. Output only the reply text.`;
}

// v4 = v2 + her published work (eval/REPORT-v2.md). Triage now keeps
// "please change your product" items out of drafting, so v4 drafts only
// engagement, questions and reactions. The new part: retrieved chunks of her
// articles, stories, research and release notes, which she may draw on as her
// own experience, and cite when someone asked a question they answer.
function systemV4(name: string, handle?: string | null): string {
  return `You draft replies for ${name}${handle ? ` (@${handle})` : ""}, a founder, to people who wrote to her, commented on her work, or posted in a thread she's in. She reads every draft, edits it, and decides whether to post. You write the reply she would write, using what she has actually published, and you mark what only she can fill in.

How she replies (from her real replies):
- Straight to substance. First sentence = her reaction to one specific thing they said (their #3, their probe, their number), or her direct answer.
- Her concrete material is her own published work: what she built, measured, found and wrote up. She brings ONE such piece when it fits their point, with its exact names and numbers. She never praises in general terms.
- One main point. Then at most one pointed question or proposal. No closing summary, no compliment at the end.
- If she doubts the premise, she says so plainly and asks why.
- Thanks only when they did real work for her, named in a few words.

Rules:
1. Write as her, first person, in the language of the message you answer. Plain text, no headings, no sign-off, no quotes around the draft.
2. "Her published work" in the context (marked [K1], [K2]…) is true and hers: you may state its facts as hers ("when I measured 5 to 100 tools…"). Keep its numbers, names and versions exactly; never round, extend or combine them into new claims. Use at most two pieces, and only ones that bear directly on their point. Don't write the [K…] marks in the reply.
3. Anything else she did, checked or thinks about her own code: only if the thread or her past replies show it. You do NOT know what she did after reading this message. If the reply needs that, write a slot in her voice: [check: did you try X? what happened]. Never invent an experience ("I hit the same thing…").
4. No future commitments: never "I'll", "I will", "I'm going to", "we'll add". Report what is, or leave a [check: …] slot.
5. Links: only URLs that appear in the context, copied exactly. Link a piece of her work only when they asked something it answers, or when the reply's point is that piece; at most one link. Never link a source marked "(no public link)".
6. Don't pitch her product. Mention it only if they mentioned it, asked about it, or the thread is about it, or the piece of her work you use is about it.
7. Facts about anything else (their project, numbers, links) only from the context. Quote their detail rather than paraphrasing it into something new.
8. Length: aim for the target in the task and never exceed its upper bound. Short beats complete.
9. Banned: "Great question", "Great point", "Love this", "Thanks for sharing", "makes sense", "solid", "clean way", "robust", "powerful", "exactly the right", "game-changer", "seamless", "leverage", "delve", "journey", "landscape", emojis. At most one em dash.
10. Output only the reply text.`;
}

const KIND_TASK: Record<string, string> = {
  engagement: "This is a discussion: take one point of theirs and add one concrete thing from her published work if one fits; otherwise ask the one question she'd ask.",
  question: "They asked something about her product or work. Answer it first, in one or two sentences, from her published work, and give the one source link that answers it. If her published work doesn't answer it, write [check: answer] instead of guessing.",
  reaction: "This is thanks or a short reaction. Reply in 1–3 short sentences; if they asked a small question, answer it. No new topic.",
};

function block(title: string, body: string) { return `## ${title}\n${body.trim()}\n`; }

export function userPrompt(req: DraftRequest, a: Assembled, variant: Variant, version: PromptVersion = PROMPT_VERSION): string {
  const p = userPromptParts(req, a, variant, version);
  return `${p.stable}\n${p.item}`;
}

/**
 * The user turn in two parts. `stable` (who she is, the product) is the same
 * for every draft of a project, so a provider with prompt caching can cache it
 * together with the system rules; `item` is everything about this message.
 * stable + "\n" + item is exactly userPrompt(), so providers without caching
 * see the same text.
 */
export function userPromptParts(req: DraftRequest, a: Assembled, variant: Variant, version: PromptVersion = PROMPT_VERSION): { stable: string; item: string } {
  const lang = detectLanguage(a.item.text);
  const stable = block("Who you are and the product", a.profile);
  const parts: string[] = [];
  if (a.voice.length) {
    parts.push(block("Her real past replies (match this voice, length and directness; don't copy their content)",
      a.voice.map((v, i) => `Example ${i + 1}${v.in_reply_to ? `\n(in reply to: "${v.in_reply_to.replace(/\s+/g, " ")}")` : ""}\nShe wrote:\n${v.text}`).join("\n\n")));
  }
  if (a.memory.length) {
    parts.push(block("Project notes you may rely on", a.memory.map((m) => `- (${m.kind}) ${m.text}${m.source_url ? ` [${m.source_url}]` : ""}`).join("\n")));
  }
  if (a.knowledge.length) {
    parts.push(block("Her published work (retrieved for this message; true and hers, use only what bears on their point)",
      a.knowledge.map((k, i) => `[K${i + 1}] ${k.kind}, ${k.published_at.slice(0, 10)}: "${k.title}" ${k.source_url ? `<${k.source_url}>` : "(no public link)"}\n${k.text.trim()}`).join("\n\n")));
  }
  if (a.person) parts.push(block("The person you're answering", a.person));

  const thread: string[] = [];
  if (a.post) thread.push(`POST ${a.post}`);
  if (a.omittedChain) thread.push(`[${a.omittedChain} earlier message(s) omitted]`);
  for (const m of a.chain) thread.push(`@${m.author}${m.is_owner ? " (you)" : ""}:\n${m.text}`);
  parts.push(block(`Thread on ${req.context.platform}`, thread.join("\n\n---\n\n")));
  parts.push(block(`The ${req.context.kind} to answer, by @${a.item.author}`, a.item.text));

  const [lo0, hi0] = a.targetWords;
  // v2: tighter band around her typical length (v1 drafts ran ~1.3x long).
  const mid = Math.round((lo0 + hi0) / 2);
  let [lo, hi] = version === "v1" ? [lo0, hi0] as const : [Math.round(mid * 0.55), Math.round(mid * 0.95)];
  // A reaction gets a reaction: her short replies run 30–70 words. Not when
  // she gave a point: then she has something to say.
  if (version === "v4" && req.item_kind === "reaction" && !req.gist?.trim()) [lo, hi] = [Math.min(lo, 25), Math.min(hi, 60)];
  const task: string[] = [];
  if (variant === "shorter" && req.previous_draft) {
    // Eval: "about half" alone gave 119 → 107 words; an explicit number works better.
    const cap = Math.max(12, Math.round(req.previous_draft.trim().split(/\s+/).length * 0.55));
    task.push(`Rewrite this draft in at most ${cap} words. Keep the main answer, any [check: …] slots and her voice; cut whole sentences rather than squeezing every sentence. Don't add anything new.\n\nDraft:\n${req.previous_draft}`);
  } else if (variant === "redraft" && req.previous_draft && req.expand) {
    // Longer: the one-liner's point, developed. Not a fresh draft (that lost her point).
    task.push(`Make this one-line draft a full reply. Keep its point${req.gist?.trim() ? " and her point (in her note)" : ""} as the opening, then develop it against what @${a.item.author} actually said: name or quote their specific words and answer them. Support it only with what the thread and her published work show; don't add an idea, claim or angle of your own. Same rules: nothing she did unless the context shows it, slots for the rest.\n\nDraft:\n${req.previous_draft}\n\nLength: about ${Math.round((lo + hi) / 2)} words, never more than ${hi}.`);
  } else if (variant === "redraft" && req.previous_draft && req.gist?.trim()) {
    // Her own point is the base. Before this, a redraft asked for "a different
    // angle", and the model invented one and put it in her mouth.
    // Her point is a seed, usually a few words: grow it into the reply and
    // tie it to what they said, rather than paraphrasing it shorter.
    task.push(`She didn't like this draft and told you her point, in short. Write the whole reply around her point: open with it, keeping her wording where you can, then develop it against what @${a.item.author} actually said: name or quote their specific words and say how her point answers, extends or disagrees with them. Support it only with what the thread and her published work show. Don't add another idea, angle or opinion of your own. Same rules: nothing she did unless the context shows it, slots for the rest.\n\nHer point:\n${req.gist.trim()}\n\nPrevious draft (what she didn't like):\n${req.previous_draft}\n\nLength: about ${Math.round((lo + hi) / 2)} words, never more than ${hi}; longer than her point, which is only the seed.`);
  } else if (variant === "redraft" && req.previous_draft) {
    // No point from her: reword only. A new angle would have to be invented.
    task.push(`Reword this draft: a different opening and different sentences, the same points. Don't add any idea, claim, example or angle that isn't already in the draft or the thread; drop a sentence rather than invent one. Same rules: nothing she did unless the context shows it, slots for the rest.\n\nDraft:\n${req.previous_draft}\n\nLength: at most ${hi} words.`);
  } else {
    task.push(version === "v1"
      ? `Write her reply to @${a.item.author}. Length: ${lo}–${hi} words. Language: ${LANG_NAME[lang] ?? lang}.`
      : `Write her reply to @${a.item.author}. Length: about ${Math.round((lo + hi) / 2)} words, never more than ${hi}. Language: ${LANG_NAME[lang] ?? lang}.`);
  }
  if (version === "v4" && variant === "first" && req.item_kind && KIND_TASK[req.item_kind]) task.push(KIND_TASK[req.item_kind]);
  if (req.note) task.push(`Her note for this draft: ${req.note}`);
  if (variant === "first" && req.gist?.trim()) task.push("Build the reply on what she wants to say (in her note): it is the main point; don't add a different idea of your own.");
  parts.push(block("Task", task.join("\n\n")));
  return { stable, item: parts.join("\n") };
}
