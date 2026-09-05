# Claude Workflow adapter

Use only when the host exposes the compatible Workflow tool and JetBrains MCP.
The core SKILL.md defines scope and authorization. This adapter does not grant them.
Model names and workflow primitives below are Claude-specific; check availability
before selecting overrides. If this tool is absent, use the direct route in SKILL.md.

Launch the bundled, parameterized workflow once with the resolved inputs:

```
Workflow({
  scriptPath: "<absolute-skill-directory>/workflows/inspections.js",
  args: {
    projectPath: "<absolute project root>",
    files: [ ...resolved project-relative paths... ],
    policy: { default: "auto", rules: [ ...from policy.yaml... ] },
    mode: "apply",                     // "apply" | "dry-run" | "audit"
    severityFloor: ["ALL"],            // every severity (default); ["ERROR","WARNING"] or ["ERROR"] per --severity
    policyDoc: "<absolute-skill-directory>/references/resolution-policy.md",
    knownProblems: { },                // optional: reuse a prior scan (see references/scan-reuse.md)
    inspectModel: "sonnet"             // cheap model for the inspect passthrough (default; "haiku" = cheapest)
  }
})
```

Every run returns `snapshot` (file → problems for every in-scope file). Hold onto it — it is what
lets the next phase reuse still-valid observations (see references/scan-reuse.md).

#### Passing inputs robustly

`args` must reach the script as a **real JSON object**, not a JSON-encoded string. A large inline
`args` payload (a full `all` file list, or a big `knownProblems` cache) can get stringified or dropped
at the tool boundary; the symptom is the run logging "No files in scope" and falling back to mode
`apply`. The script now re-parses a stringified `args` defensively and logs loudly if inputs are
missing, but the bulletproof option for **large scopes** is to embed the inputs in the script text and
delegate to the bundled workflow via the inline `workflow()` hook — then only script text crosses the
boundary, never a structured payload:

```
Workflow({ script: `
export const meta = { name: 'idea-inspections-run', description: 'Run the inspection workflow with embedded inputs' }
const inputs = {
  projectPath: "<absolute project root>",
  files: [ /* resolved project-relative paths */ ],
  policy: { default: "auto", rules: [ /* from policy.yaml */ ] },
  mode: "audit",
  severityFloor: ["ALL"],
  policyDoc: "<absolute-skill-directory>/references/resolution-policy.md"
}
return await workflow({ scriptPath: "<absolute-skill-directory>/workflows/inspections.js" }, inputs)
` })
```

Use the direct `scriptPath` + `args` form for small scopes (`changed`, `file:`, a small module); use
the wrapper for `all` or any run with a large `files`/`knownProblems` payload.

Replace `<absolute-skill-directory>` with the loaded skill's actual absolute directory. In `apply`/`dry-run` mode the workflow
pipelines each file through **Inspect** (cheap `get_file_problems`) → **Resolve** (fix/suppress each
policy-actionable problem via `mcp__jetbrains__replace_text_in_file`, then re-inspect) → **Verify** (an
independent, adversarial re-inspection + soundness review that challenges every suppression).
Policy classification happens in plain JavaScript between Inspect and Resolve — no agent; each
actionable problem carries its `pinnedAction` (fix/suppress/auto) into Resolve, which honors it.

The **Inspect** agents run on a cheap model (`inspectModel`, default Sonnet) — they only load the MCP
tool and return its output, so paying for the session model on every file is pure waste. **Resolve**
and **Verify** inherit the session model (that is where the real reasoning lives); override per stage
with `resolveModel` / `verifyModel` / `triageModel` if needed.

Details of the orchestration live in `workflows/inspections.js`; the fix/suppress judgment and the
message→inspection-id cheat sheet the resolve agents rely on live in `references/resolution-policy.md`.
