# Follow-up research

Update an existing document when the new work answers the same research question and the
combined artifact remains coherent. Create a companion document when the follow-up changes
the central question, crosses a major version or evidence boundary, needs a different
audience, or would make the original document misleading.

## Update workflow

1. Locate the existing document in the user-specified path or the repository's research
   directory. If needed, search for its `topic`, title, or frontmatter fields.
2. Re-read the document's scope, findings, evidence baseline, and open questions.
3. Decide whether to integrate findings into existing sections or add a dated follow-up
   section. Prefer integration when it keeps the document accurate and navigable. Use a
   dated section when preserving the investigation timeline matters.
4. Preserve the original `date`. Refresh update metadata and, for repository research,
   the repository snapshot.
5. Re-check conclusions and the opening summary; do not leave newly contradicted claims in
   place without qualification.
6. Run the document validator again.

Generate update fields with:

```bash
bash <skill-dir>/scripts/research-metadata.sh \
  --update \
  --repo /path/to/researched/repo \
  --note "Brief description of the follow-up"
```

Omit `--repo` for non-repository research. Merge the emitted keys into the existing YAML
frontmatter, replacing keys with the same name. `--update` intentionally does not emit a
new `date`, `topic`, `tags`, or `status`; update `status` separately when the document's
state changes.

When creating a companion document, link both documents and explain the scope boundary so
future readers know which one answers which question.
