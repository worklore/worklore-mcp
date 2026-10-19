// POST /functions/v1/post-bluesky  {draft_id, final_text, move_stage?}
// The core reply action for the Bluesky connector (reply mode "server"):
// posts on her explicit tap, then records the outcome. docs/API.md › post-bluesky

import "../_shared/connectors/mod.ts";
import { replyOnServer } from "../_shared/core/actions.ts";
import { requireUser } from "../_shared/server/ctx.ts";
import { serve, str, uuid } from "../_shared/server/http.ts";

serve(async (req, body) => {
  const c = await requireUser(req);
  return await replyOnServer(c, {
    platform: "bluesky",
    draftId: uuid(body.draft_id, "draft_id")!,
    text: str(body.final_text, "final_text", { required: true, max: 5000 }) ?? "",
    moveStage: str(body.move_stage, "move_stage"),
  });
});
