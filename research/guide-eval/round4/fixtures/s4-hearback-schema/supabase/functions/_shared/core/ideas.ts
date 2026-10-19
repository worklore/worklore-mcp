// Feedback → idea. Each feedback item joins an existing idea when it asks for
// the same thing (so "also asked by 2" counts people), else starts a new one.
// The match is a typed choice question to the decider (Jev): cheap, and no
// free text needed.

import type { Decider, Questions } from "../draft/mod.ts";
import { admin } from "../server/ctx.ts";
import { firstSentence } from "../server/text.ts";

export const IDEA_KINDS = ["feature", "bug", "pain", "would_pay", "other"] as const;

/** Pure: the question set for matching one ask against existing ideas. Exported for tests. */
export function ideaQuestions(ideas: { id: string; title: string }[]): { questions: Questions; optionToId: Record<string, string> } {
  const criteria: Record<string, string> = { new: "a different request from every idea listed here" };
  const optionToId: Record<string, string> = {};
  ideas.forEach((i, n) => {
    criteria[`idea_${n + 1}`] = `the same request as: "${i.title}"`;
    optionToId[`idea_${n + 1}`] = i.id;
  });
  return {
    optionToId,
    questions: {
      same_as: { type: "choice", instructions: "Is this ask the same as one of the founder's existing ideas (same change requested, even if worded differently)?", criteria },
      idea_kind: {
        type: "choice", instructions: "What kind of feedback is it?",
        criteria: {
          feature: "asks for a new feature or capability",
          bug: "reports something broken or wrong",
          pain: "describes a pain or friction without asking for a specific change",
          would_pay: "says they would pay for something, or asks about pricing",
          other: "anything else",
        },
      },
    },
  };
}

export async function fileFeedback(dec: Decider, item: {
  id: string; project_id: string; person_id: string; text: string; summary: string;
}): Promise<string> {
  const db = admin();
  const { data: existing } = await db.from("idea_items").select("idea_id").eq("item_id", item.id).limit(1);
  if (existing?.length) return existing[0].idea_id;

  const { data: ideas } = await db.from("ideas").select("id, title").eq("project_id", item.project_id)
    .neq("status", "done").order("updated_at", { ascending: false }).limit(15);
  const { questions, optionToId } = ideaQuestions(ideas ?? []);
  let ideaId: string | null = null;
  let kind = "feature";
  try {
    const d = await dec.decide(`New feedback: "${item.summary}"\nExact words: "${item.text.slice(0, 1200)}"`, questions);
    const same = d.answers.same_as;
    if (same && same.answer !== "new" && same.confidence >= 0.6) ideaId = optionToId[same.answer as string] ?? null;
    kind = (d.answers.idea_kind?.answer as string) ?? "feature";
  } catch (e) {
    console.error("idea match failed, new idea:", (e as Error).message.slice(0, 120));
  }
  const quote = firstSentence(item.text, 220);
  if (!ideaId) {
    const { data, error } = await db.from("ideas").insert({
      project_id: item.project_id, title: item.summary.slice(0, 200), summary: item.summary, quote,
      kind: (IDEA_KINDS as readonly string[]).includes(kind) ? kind : "other",
    }).select("id").single();
    if (error) throw error;
    ideaId = data.id;
  }
  await db.from("idea_items").upsert({ idea_id: ideaId, item_id: item.id, project_id: item.project_id, quote },
    { onConflict: "idea_id,item_id", ignoreDuplicates: true });
  return ideaId!;
}
