export const meta = {
  name: 'idea-inspections',
  description: 'Inspect Java/Kotlin files via the JetBrains MCP, then resolve every actionable problem per the project policy and verify',
  phases: [
    { title: 'Inspect', detail: 'get_file_problems per file (cheap model — Sonnet by default)' },
    { title: 'Triage', detail: 'audit mode: classify each inspection type into a policy rule (ignore/fix/suppress)' },
    { title: 'Resolve', detail: 'fix or suppress each actionable problem per policy, re-inspect to confirm' },
    { title: 'Verify', detail: 'independent adversarial re-inspection + soundness review' },
  ],
}

// ---------------------------------------------------------------------------
// Inputs (via `args`):
//   projectPath    absolute path to the IntelliJ project root
//   files          array of project-relative .java/.kt paths (the resolved scope)
//   policy         { default: 'auto'|'fix'|'suppress'|'ignore', rules: [ rule, ... ] } — the
//                  inspection policy from .idea-inspections/policy.yaml. A `rule` is
//                  { description?: regex, severity?, paths?: glob[], action: ignore|fix|suppress|auto,
//                    suppressId?, reason? }. Rules are first-match-wins; unmatched problems take
//                  `default` (default 'auto' => the resolve agent decides fix vs suppress).
//   whitelist      legacy: array of ignore entries; converted to policy rules with action 'ignore'.
//   mode           'apply' (resolve + verify) | 'dry-run' (inspect + plan only) |
//                  'audit' (aggregate by type + triage into proposed policy rules; no edits)
//   apply          legacy: false is treated as mode 'dry-run' when mode is unset
//   severityFloor  severities in scope; default ['ALL'] = every severity (WEAK_WARNING, INFO, …),
//                  not just ERROR/WARNING. Pass an explicit list (e.g. ['ERROR'] or
//                  ['ERROR','WARNING']) to restrict.
//   policyDoc      absolute path to references/resolution-policy.md (suppression-id hints)
//   knownProblems  optional cache: { "<file>": [ ...problems... ] }. A file present here is NOT
//                  re-inspected (reuse from a prior audit/scan). Edited files must be invalidated
//                  by the caller (drop them from the cache) so the next run re-inspects them.
//   inspectModel   model for the cheap inspect passthrough (default 'sonnet'; 'haiku' for max savings)
//   triageModel    optional model override for triage  (default: inherit the session model)
//   resolveModel   optional model override for resolve (default: inherit the session model)
//   verifyModel    optional model override for verify  (default: inherit the session model)
//
// Every run returns `snapshot` (file -> problems for every in-scope file, cache hits included) so
// the caller can persist a baseline or feed it straight into a follow-up run without rescanning.
// ---------------------------------------------------------------------------

// Be robust to `args` arriving as a JSON string. A large inline args payload can be passed (or
// serialized) as a JSON-encoded string across the tool boundary; then `args.files`/`args.mode` are
// undefined and the run silently degrades to "No files in scope" + mode "apply". Re-parse so the
// inputs survive. (Prefer passing args as a real object; for big scopes see references/claude-workflow.md.)
let input = args
if (typeof input === 'string') {
  try {
    input = JSON.parse(input)
  } catch (e) {
    log('idea-inspections: args came across as a non-JSON string and could not be parsed: ' + e.message)
    input = {}
  }
}
if (!input || typeof input !== 'object') input = {}

const projectPath = input.projectPath
const files = Array.isArray(input.files) ? input.files : []
const mode = input.mode || (input.apply === false ? 'dry-run' : 'apply')
const apply = mode === 'apply'
const severityFloor = (Array.isArray(input.severityFloor) ? input.severityFloor : ['ALL'])
  .map((s) => String(s).toUpperCase())
// Default 'ALL' keeps every severity in scope — WEAK_WARNING, INFO, etc., not just ERROR/WARNING.
// Pass an explicit severityFloor (e.g. ['ERROR'] or ['ERROR','WARNING']) to restrict.
const allSeverities = severityFloor.includes('ALL')
const policyDoc = input.policyDoc || ''
const knownProblems = input.knownProblems && typeof input.knownProblems === 'object' ? input.knownProblems : {}

// Inspection policy: { default, rules }. Accept the legacy `whitelist` array (ignore-only) too.
const ACTIONS = ['ignore', 'fix', 'suppress', 'auto']
const rawPolicy =
  input.policy && typeof input.policy === 'object'
    ? input.policy
    : Array.isArray(input.whitelist)
      ? { default: 'auto', rules: input.whitelist.map((w) => ({ ...w, action: 'ignore' })) }
      : { default: 'auto', rules: [] }
const rules = Array.isArray(rawPolicy.rules) ? rawPolicy.rules : []
const defaultAction = ACTIONS.includes(rawPolicy.default) ? rawPolicy.default : 'auto'

// Per-stage model overrides. Inspect is a pure MCP-tool-call passthrough (ToolSearch -> one
// get_file_problems call -> structured return), so it defaults to a CHEAP model — otherwise every
// file (~hundreds on an `all` scan) runs on the expensive session model for no benefit. The
// reasoning-heavy stages inherit the session model unless explicitly overridden.
const inspectModel = input.inspectModel || 'sonnet'
const triageModel = input.triageModel || null
const resolveModel = input.resolveModel || null
const verifyModel = input.verifyModel || null

// Inspection snapshot collected this run (file -> problems[]), cache hits included. Declared early
// so inspectOne() can populate it from any mode. Returned for the caller to persist or pass on.
const snapshot = {}

// ---- helpers --------------------------------------------------------------

function short(file) {
  const parts = String(file).split('/')
  return parts.slice(-2).join('/')
}

// Attach a model override only when one is set (null/undefined => inherit the session model).
function withModel(opts, model) {
  return model ? { ...opts, model } : opts
}

function globToRegExp(glob) {
  let re = ''
  for (let i = 0; i < glob.length; i++) {
    const c = glob[i]
    if (c === '*') {
      if (glob[i + 1] === '*') {
        re += '.*'
        i++
        if (glob[i + 1] === '/') i++
      } else {
        re += '[^/]*'
      }
    } else if ('\\^$+?.()|[]{}'.includes(c)) {
      re += '\\' + c
    } else {
      re += c
    }
  }
  return new RegExp('^' + re + '$')
}

function matchesPaths(file, globs) {
  return globs.some((g) => {
    try {
      return globToRegExp(g).test(file) || globToRegExp('**/' + g).test(file)
    } catch (_) {
      return false
    }
  })
}

// First policy rule (in file order) that matches this problem, or null.
function matchRule(p, file, sev) {
  for (const e of rules) {
    if (e.description) {
      try {
        if (!new RegExp(e.description).test(p.description)) continue
      } catch (_) {
        continue
      }
    }
    if (e.severity && String(e.severity).toUpperCase() !== sev) continue
    if (e.paths && e.paths.length && !matchesPaths(file, e.paths)) continue
    return e
  }
  return null
}

// Assign each in-scope problem a policy action and bucket it:
//   ignored     -> action 'ignore' (no code change)
//   actionable  -> action fix|suppress|auto, carried on each item as `pinnedAction`
//                  (a rule action other than ignore/fix/suppress, or 'auto', means "agent decides")
//   outOfScope  -> excluded by an explicit severityFloor (empty when the default 'ALL' is in effect)
function classify(problems, file) {
  const actionable = []
  const ignored = []
  const outOfScope = []
  for (const p of problems) {
    const sev = String(p.severity || '').toUpperCase()
    if (!allSeverities && !severityFloor.includes(sev)) {
      outOfScope.push(p)
      continue
    }
    const rule = matchRule(p, file, sev)
    const action = rule ? rule.action : defaultAction
    if (action === 'ignore') {
      ignored.push({ ...p, policyReason: rule ? rule.reason || '' : 'default: ignore' })
      continue
    }
    actionable.push({
      ...p,
      pinnedAction: action === 'fix' || action === 'suppress' ? action : 'auto',
      suppressId: rule ? rule.suppressId : undefined,
      policyReason: rule ? rule.reason || '' : '',
    })
  }
  return { actionable, ignored, outOfScope }
}

function normalize(desc) {
  return String(desc).replace(/'[^']*'/g, "'…'").replace(/\b\d+\b/g, '#')
}

function toRegex(norm) {
  return (
    '^' +
    norm
      .split("'…'")
      .map((seg) =>
        seg
          .split('#')
          .map((s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
          .join('\\d+'),
      )
      .join("'[^']*'") +
    '$'
  )
}

// ---- schemas --------------------------------------------------------------

const PROBLEM = {
  type: 'object',
  required: ['severity', 'description', 'line'],
  properties: {
    severity: { type: 'string' },
    description: { type: 'string' },
    line: { type: 'integer' },
    column: { type: 'integer' },
    lineContent: { type: 'string' },
  },
}

const PROBLEMS_SCHEMA = {
  type: 'object',
  required: ['file', 'problems'],
  properties: {
    file: { type: 'string' },
    problems: { type: 'array', items: PROBLEM },
  },
}

const RESOLUTION_SCHEMA = {
  type: 'object',
  required: ['file', 'changed', 'resolutions', 'remaining'],
  properties: {
    file: { type: 'string' },
    changed: { type: 'boolean' },
    resolutions: {
      type: 'array',
      items: {
        type: 'object',
        required: ['description', 'line', 'action', 'detail'],
        properties: {
          description: { type: 'string' },
          line: { type: 'integer' },
          action: { type: 'string', enum: ['fix', 'suppress', 'blocked'] },
          detail: { type: 'string' },
          suppressId: { type: 'string' },
        },
      },
    },
    remaining: { type: 'array', items: PROBLEM },
    notes: { type: 'string' },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['file', 'clean', 'approved'],
  properties: {
    file: { type: 'string' },
    clean: { type: 'boolean' },
    approved: { type: 'boolean' },
    issues: { type: 'array', items: { type: 'string' } },
    remaining: { type: 'array', items: PROBLEM },
  },
}

const TRIAGE_SCHEMA = {
  type: 'object',
  required: ['action', 'rationale'],
  properties: {
    // the recommended policy action for this inspection type
    action: { type: 'string', enum: ['ignore', 'fix', 'suppress', 'mixed'] },
    rationale: { type: 'string' },
    // true when this is low-signal noise rather than a real problem (an ignore candidate)
    questionableValue: { type: 'boolean' },
    // the policy rule to add to .idea-inspections/policy.yaml
    rule: {
      type: 'object',
      properties: {
        description: { type: 'string' },
        action: { type: 'string', enum: ['ignore', 'fix', 'suppress'] },
        severity: { type: 'string' },
        paths: { type: 'array', items: { type: 'string' } },
        suppressId: { type: 'string' },
        reason: { type: 'string' },
      },
    },
  },
}

// ---- prompts --------------------------------------------------------------

function inspectPrompt(file) {
  return [
    'Report every problem IntelliJ finds in ONE file. Do not edit anything.',
    '',
    '1. Load the tool: ToolSearch query "select:mcp__jetbrains__get_file_problems".',
    '2. Call mcp__jetbrains__get_file_problems with:',
    `   - filePath: "${file}"`,
    `   - projectPath: "${projectPath}"`,
    '   - errorsOnly: false',
    '3. Return EVERY reported problem verbatim: severity, description, line, column, lineContent.',
    '   If the tool returns an empty list, return an empty problems array.',
    '',
    `Set file to "${file}". Return only the structured object.`,
  ].join('\n')
}

function resolvePrompt(file, actionable, ignored) {
  return [
    'Resolve IntelliJ inspection problems in ONE file under a ZERO-TOLERANCE policy:',
    'every problem below must end as a fix or a suppression. Mark "blocked" ONLY when',
    'neither a safe fix nor a verifiable suppression is possible.',
    '',
    `Project root: ${projectPath}`,
    `File: ${file}`,
    '',
    'Each problem carries a "pinnedAction" set by the project policy — honor it:',
    '- "fix": you MUST fix it (do not suppress).',
    '- "suppress": you MUST suppress it at the narrowest scope. If "suppressId" is given, use it as',
    '  the inspection id; add a short reason comment (use "policyReason" if present).',
    '- "auto": YOU decide fix vs suppress using the judgment rules below.',
    '',
    'Problems to resolve (already filtered through the project policy):',
    JSON.stringify(actionable, null, 2),
    '',
    'Tolerated here by policy (do NOT touch these): ' + JSON.stringify(ignored.map((w) => w.description)),
    '',
    'Load tools first: ToolSearch query',
    '"select:mcp__jetbrains__get_file_problems,mcp__jetbrains__get_file_text_by_path,mcp__jetbrains__replace_text_in_file".',
    'Edit ONLY through mcp__jetbrains__replace_text_in_file so the IDE stays in sync; do not',
    'use the filesystem Edit/Write tools on project files. Pass projectPath on every MCP call.',
    '',
    'Judgment rules (for pinnedAction "auto", and for HOW to fix/suppress):',
    '- A fix either preserves behavior (mechanical cleanups, simplifications, redundant code) or',
    '  correctly repairs a real defect the inspection exposes (e.g. "always null/false", passing',
    '  null to @NotNull). Keep diffs minimal; do not reformat unrelated lines.',
    '- To suppress: @SuppressWarnings("<id>") / @Suppress("<id>") on the smallest element, or a',
    '  //noinspection <id> line directly above, plus a short reason comment. The MCP does NOT return',
    '  inspection ids — infer the id, then VERIFY: re-run get_file_problems and confirm the problem is',
    '  gone. If it persists, try an alternate id; if still unresolved after two tries, fix instead or',
    '  mark blocked.',
    '- A defect that needs a human decision (changing a real nullness/throws contract, deleting code',
    '  that may be load-bearing): mark blocked with an explanation rather than silencing it. This',
    '  applies even when pinnedAction is "fix" — never invent a risky change to satisfy the policy.',
    '',
    'Respect project conventions: read AGENTS.md / CLAUDE.md at the project root and follow',
    'them (this is a JSpecify @NullMarked codebase; @Nullable never goes on local variables).',
    policyDoc ? `For message→inspection-id hints, read: ${policyDoc}` : '',
    '',
    'After all edits, re-run get_file_problems on the file and report any policy-actionable',
    'problem of any severity still present in "remaining". Set changed=true if you modified the file.',
    'Return one resolution entry per problem you handled.',
  ]
    .filter(Boolean)
    .join('\n')
}

function verifyPrompt(file, resolved) {
  const tolerated = (resolved.ignored || []).map((w) => w.description)
  return [
    'Independently and adversarially verify the inspection resolutions for ONE file.',
    'Assume the resolver may have hidden a bug or over-suppressed; try to disprove its work.',
    '',
    `Project root: ${projectPath}`,
    `File: ${file}`,
    '',
    'Load tools: ToolSearch query',
    '"select:mcp__jetbrains__get_file_problems,mcp__jetbrains__get_file_text_by_path".',
    '',
    '1. Re-inspect from scratch: get_file_problems(filePath, projectPath, errorsOnly:false).',
    '2. Read the file to review what changed.',
    '3. clean = no policy-actionable problems of any severity remain. List any that do in "remaining".',
    '   Treat these as tolerated by policy: ' + JSON.stringify(tolerated),
    '4. approved = every fix preserves behavior or correctly fixes a real bug, AND every',
    '   suppression is a justified false-positive / intentional case — not a masked defect.',
    '   Challenge each suppression specifically. Flag deleted logic, masked bugs, over-broad',
    '   suppressions, or newly introduced problems in "issues".',
    '',
    'Resolutions under review:',
    JSON.stringify(resolved.resolutions || [], null, 2),
    '',
    `Set file to "${file}". Return the verdict object.`,
  ].join('\n')
}

function triagePrompt(t) {
  return [
    'Triage ONE IntelliJ inspection type for an existing codebase that is building up its',
    'inspection policy (.idea-inspections/policy.yaml). Recommend the policy action for this type.',
    '',
    'Choose one action:',
    '- "ignore": tolerated project-wide — no code change (low-signal/subjective/noise or accepted',
    '  by policy).',
    '- "fix": a genuine issue that should be fixed under zero-tolerance.',
    '- "suppress": correct report but intentional code — suppress at each occurrence.',
    '- "mixed": legitimate in some places, noise in others — return a path-narrowed rule (usually',
    '  ignore or suppress for the noisy paths) and note the rest should be fixed.',
    '',
    `Inspection (normalized): ${t.pattern}`,
    `Severity: ${t.severity}. Occurrences: ${t.count} across ${t.files.length} file(s).`,
    'Examples (file, line, lineContent):',
    JSON.stringify(t.examples, null, 2),
    '',
    `Project root: ${projectPath}. You MAY read 1–2 example files for context`,
    '(ToolSearch "select:mcp__jetbrains__get_file_text_by_path", or the Read tool).',
    '',
    'Judgment guidance:',
    '- Correctness / bug smells are NEVER ignore: "always true/false", null passed to @NotNull,',
    '  resource leaks, etc. → fix.',
    '- Subjective / stylistic or structural-by-design → ignore candidates: duplicated code,',
    "  \"may be 'final'\", Optional-as-parameter-type, symmetric generated/codec code.",
    '- Unused public-API declarations → ignore or suppress, narrowed by paths to the API surface so',
    '  genuinely dead private code is still caught.',
    '- Mechanical simplifications (enhanced switch, assertInstanceOf, !isEmpty) default to fix, but',
    '  may be ignored if the team prefers to avoid churn — then set questionableValue=true.',
    '',
    'Return `rule`: a policy rule with description (a regex over the message; default',
    `${JSON.stringify(t.suggestedRegex)}), action (ignore|fix|suppress), optional severity, optional`,
    'paths globs to narrow it, optional suppressId (for suppress), and a short reason. Set',
    'questionableValue=true when this is low-signal noise rather than a real problem.',
  ].join('\n')
}

// ---- inspection (cache-aware) ---------------------------------------------

// Inspect one file, reusing knownProblems on a cache hit (no agent call). Records into snapshot.
async function inspectOne(file) {
  let problems
  if (Array.isArray(knownProblems[file])) {
    problems = knownProblems[file]
  } else {
    const r = await agent(inspectPrompt(file), {
      label: `inspect ${short(file)}`,
      phase: 'Inspect',
      schema: PROBLEMS_SCHEMA,
      effort: 'low',
      model: inspectModel,
    })
    problems = (r && r.problems) || []
  }
  snapshot[file] = problems
  return { file, problems }
}

// ---- pipeline -------------------------------------------------------------

if (files.length === 0) {
  if (!projectPath) {
    log(
      'idea-inspections: received no files AND no projectPath — inputs did not arrive. The args were ' +
        'likely passed as a JSON string or dropped at the tool boundary. See SKILL.md "Passing inputs ' +
        'robustly"; pass args as a real object or use the wrapper form.',
    )
  } else {
    log('No files in scope — nothing to inspect.')
  }
  return { scopeCount: 0, mode, files: [], summary: {}, policySuggestions: [], snapshot }
}

// ---- audit (bootstrap) mode ----------------------------------------------
// Inspect everything, aggregate actionable problems by inspection type, and triage each type into a
// proposed policy rule (ignore/fix/suppress) to build up .idea-inspections/policy.yaml. No edits.
if (mode === 'audit') {
  log(`Audit mode over ${files.length} file(s); aggregating inspections to build the policy.`)
  const inspected = await parallel(files.map((f) => () => inspectOne(f)))

  const byType = {}
  let totalActionable = 0
  for (const r of inspected) {
    if (!r) continue
    const { actionable } = classify(r.problems || [], r.file)
    for (const p of actionable) {
      totalActionable++
      const k = normalize(p.description)
      if (!byType[k]) {
        byType[k] = { pattern: k, suggestedRegex: toRegex(k), severity: p.severity, count: 0, files: [], examples: [] }
      }
      const t = byType[k]
      t.count++
      if (!t.files.includes(r.file)) t.files.push(r.file)
      if (t.examples.length < 5) t.examples.push({ file: r.file, line: p.line, lineContent: p.lineContent, description: p.description })
    }
  }

  const types = Object.values(byType).sort((a, b) => b.count - a.count)
  if (types.length === 0) {
    log('No actionable problems found — nothing to triage.')
    return { mode: 'audit', scopeCount: files.length, typeCount: 0, totalActionable: 0, proposedRules: [], byAction: {}, types: [], snapshot }
  }

  log(`${types.length} distinct inspection type(s), ${totalActionable} occurrence(s). Triaging.`)
  const triaged = await parallel(
    types.map((t) => () =>
      agent(
        triagePrompt(t),
        withModel({ label: `triage ${t.pattern.slice(0, 40)}`, phase: 'Triage', schema: TRIAGE_SCHEMA, effort: 'high' }, triageModel),
      ).then((v) => ({
        pattern: t.pattern,
        suggestedRegex: t.suggestedRegex,
        severity: t.severity,
        count: t.count,
        fileCount: t.files.length,
        files: t.files.slice(0, 10),
        examples: t.examples,
        triage: v || { action: 'fix', rationale: 'triage agent died; defaulting to fix', questionableValue: false },
      })),
    ),
  )

  // Turn each triaged type into a concrete policy rule ready to merge into policy.yaml.
  const proposedRules = triaged.map((t) => {
    const r = (t.triage && t.triage.rule) || {}
    const action = ['ignore', 'fix', 'suppress'].includes(r.action)
      ? r.action
      : t.triage.action === 'mixed'
        ? 'suppress'
        : ['ignore', 'fix', 'suppress'].includes(t.triage.action)
          ? t.triage.action
          : 'fix'
    return {
      description: r.description || t.suggestedRegex,
      action,
      severity: r.severity,
      paths: r.paths,
      suppressId: r.suppressId,
      reason: r.reason || t.triage.rationale,
      questionableValue: !!t.triage.questionableValue,
      count: t.count,
      fileCount: t.fileCount,
      examples: t.examples,
    }
  })
  const byAction = proposedRules.reduce((a, r) => ((a[r.action] = (a[r.action] || 0) + 1), a), {})

  log(
    `Audit done. proposed rules: ${proposedRules.length} ` +
      `(ignore ${byAction.ignore || 0}, suppress ${byAction.suppress || 0}, fix ${byAction.fix || 0}).`,
  )
  return { mode: 'audit', scopeCount: files.length, typeCount: types.length, totalActionable, proposedRules, byAction, types: triaged, snapshot }
}

log(`${apply ? 'Apply' : 'Dry-run'} mode over ${files.length} file(s); severity floor ${severityFloor.join('+')}.`)

const results = await pipeline(
  files,

  // Stage 1 — inspect (cheap; reuses knownProblems on a cache hit)
  (file) => inspectOne(file),

  // Stage 2 — classify against policy (pure JS) then resolve (or plan, in dry-run)
  async (inspected, file) => {
    if (!inspected) return { file, error: 'inspect-failed' }
    const { actionable, ignored, outOfScope } = classify(inspected.problems || [], file)
    if (actionable.length === 0) {
      return { file, clean: true, actionable: [], ignored, outOfScope, resolutions: [], remaining: [] }
    }
    if (!apply) {
      return { file, clean: false, dryRun: true, actionable, ignored, outOfScope }
    }
    const res = await agent(
      resolvePrompt(file, actionable, ignored),
      withModel({ label: `resolve ${short(file)}`, phase: 'Resolve', schema: RESOLUTION_SCHEMA }, resolveModel),
    )
    return { ...(res || { file, error: 'resolve-failed' }), actionable, ignored, outOfScope }
  },

  // Stage 3 — adversarial verify (only when changes were applied)
  async (resolved, file) => {
    if (!resolved || resolved.clean || resolved.dryRun || resolved.error) return resolved
    const v = await agent(
      verifyPrompt(file, resolved),
      withModel({ label: `verify ${short(file)}`, phase: 'Verify', schema: VERDICT_SCHEMA, effort: 'high' }, verifyModel),
    )
    return { ...resolved, verdict: v || { file, clean: false, approved: false, issues: ['verify agent died'] } }
  },
)

// ---- summarize ------------------------------------------------------------

const clean = []
const resolvedOk = []
const needsAttention = [] // blocked, remaining, or failed verify
const dryRunPlans = []
const errored = []

for (const r of results) {
  if (!r) {
    errored.push({ file: 'unknown', error: 'dropped' })
    continue
  }
  if (r.error) {
    errored.push(r)
    continue
  }
  if (r.dryRun) {
    dryRunPlans.push(r)
    continue
  }
  if (r.clean) {
    clean.push(r.file)
    continue
  }
  const remaining = (r.remaining && r.remaining.length) || (r.verdict && r.verdict.remaining && r.verdict.remaining.length)
  const blocked = (r.resolutions || []).filter((x) => x.action === 'blocked')
  const unapproved = r.verdict && r.verdict.approved === false
  if (remaining || blocked.length || unapproved) {
    needsAttention.push({
      file: r.file,
      blocked,
      remaining: r.remaining || (r.verdict && r.verdict.remaining) || [],
      verdictIssues: (r.verdict && r.verdict.issues) || [],
      approved: r.verdict ? r.verdict.approved : null,
    })
  } else {
    resolvedOk.push({
      file: r.file,
      resolutions: r.resolutions || [],
      approved: r.verdict ? r.verdict.approved : null,
    })
  }
}

// Policy suggestions: actionable messages recurring across >= 3 files — candidates for an explicit
// policy rule (pin fix/suppress, or ignore) so they aren't re-decided by `auto` every run.
const tally = {}
for (const r of results) {
  if (r && r.actionable && r.actionable.length) {
    const seen = new Set()
    for (const p of r.actionable) {
      const k = normalize(p.description)
      if (!tally[k]) tally[k] = { count: 0, files: [], example: p.description }
      tally[k].count++
      if (!seen.has(k)) {
        tally[k].files.push(r.file)
        seen.add(k)
      }
    }
  }
}
const policySuggestions = Object.entries(tally)
  .filter(([, v]) => v.files.length >= 3)
  .map(([norm, v]) => ({
    suggestedRegex: toRegex(norm),
    example: v.example,
    occurrences: v.count,
    fileCount: v.files.length,
    files: v.files.slice(0, 10),
  }))
  .sort((a, b) => b.fileCount - a.fileCount)

log(
  `Done. clean ${clean.length}, resolved ${resolvedOk.length}, needs-attention ${needsAttention.length}` +
    (apply ? '' : `, planned ${dryRunPlans.length}`) +
    (errored.length ? `, errors ${errored.length}` : ''),
)

return {
  scopeCount: files.length,
  mode,
  apply,
  severityFloor,
  summary: {
    clean: clean.length,
    resolved: resolvedOk.length,
    needsAttention: needsAttention.length,
    dryRunPlans: dryRunPlans.length,
    errors: errored.length,
  },
  clean,
  resolvedOk,
  needsAttention,
  dryRunPlans,
  errored,
  policySuggestions,
  snapshot,
}
