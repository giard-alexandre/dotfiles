// Reports Pi as blocked on you while an rpiv-ask-user-question questionnaire is open.
//
// Pi reports its state to the terminal with OSC 7501 (the Program Status Protocol), which
// Herdr uses for its working/blocked dot and its "needs you" sound and toast. Pi only reports
// `blocked` for its own dialogs and inline `ctx.ui.custom` components; rpiv-ask-user-question
// opens an overlay, which Pi doesn't count, so Herdr kept showing Pi as working.
//
// rpiv emits `rpiv:ask-user:blocked` around every wait ({ active, toolCallId }) and
// `rpiv:ask-user:prompt` just before it (with the questions). This turns those into an OSC 7501
// `blocked` report, and back to Pi's own `working` report once the last questionnaire closes.
// It also raises `herdr:blocked`, the event Herdr's socket integration (herdr-agent-state.ts)
// listens for when Pi runs with HERDR_ENV=1.

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const PROMPT = "rpiv:ask-user:prompt";
const BLOCKED = "rpiv:ask-user:blocked";

// Same encoding as pi-tui's formatProgramStatus.
function osc7501(state: "blocked" | "working", message?: string): string {
  const pairs = [`state=${state}`, "app=pi"];
  if (state === "blocked") pairs.push("kind=question");
  const text = (message ?? "").replace(/[\u0000-\u001f\u007f-\u009f]/g, " ").trim().slice(0, 500);
  if (text) pairs.push(`msg=${Buffer.from(text, "utf8").toString("base64")}`);
  return `\x1b]7501;${pairs.join(":")}\x1b\\`;
}

export default function (pi: ExtensionAPI) {
  // Only an interactive TUI on a real terminal reports program status, as Pi itself does.
  let tui = false;
  const canReport = () =>
    tui && process.stdout.isTTY && process.env.TERM !== "dumb" && process.env.PI_PROGRAM_STATUS !== "0";

  const titles = new Map<string, string>(); // toolCallId -> what the questionnaire asks
  const open: string[] = []; // open questionnaires, oldest first

  const report = () => {
    if (!canReport()) return;
    const top = open.at(-1);
    // Pi's own report while a tool runs is `working` with the session name; it won't resend it
    // (its last report hasn't changed), so restore it here.
    process.stdout.write(top ? osc7501("blocked", titles.get(top) ?? "Question") : osc7501("working", pi.getSessionName()));
  };

  pi.on("session_start", (_event, ctx) => {
    tui = ctx?.mode === "tui";
  });

  pi.events.on(PROMPT, (data: any) => {
    const q = data?.questions?.[0];
    if (data?.toolCallId && q) titles.set(data.toolCallId, String(q.question || q.header || "Question"));
  });

  pi.events.on(BLOCKED, (data: any) => {
    const id = String(data?.toolCallId ?? "questionnaire");
    const at = open.indexOf(id);
    if (data?.active) {
      if (at === -1) open.push(id);
    } else {
      if (at === -1) return;
      open.splice(at, 1);
      titles.delete(id);
    }
    report();
    pi.events.emit("herdr:blocked", { active: Boolean(data?.active), label: titles.get(id) ?? "Question" });
  });
}
