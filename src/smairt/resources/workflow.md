# SMAIRT v2 Workflow

```text
references -> background -> three proposals -> human-selected hypothesis
-> experiment -> iteration -> immutable run -> human decision
-> evidence card -> approved claim -> reviewed manuscript -> versioned build
```

- Full PDFs, raw data, old logs, stale summaries, and unrelated iterations stay out of default
  context.
- Promoted fresh summaries may enter shared context; contributor versions remain immutable.
- `cheap` tier handles metadata and mechanical checks, `balanced` handles routine code, and
  `strong` handles scientific reasoning and synthesis.
- Retractions invalidate accepted pointers and dependent evidence. Supersession links an old run
  to a verified replacement.
- Harness adapters translate instructions only. They never create parallel scientific state.
