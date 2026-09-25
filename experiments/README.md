# Experiments (personal scratch space)

- `experiments/<member>/` belongs to that member only. Nobody else edits it, so it never conflicts.
- Put notebooks, quick scripts and exploratory analysis here.
- **Clear notebook outputs before committing.** No data files, no files over 5 MB (hooks block them).
- When code becomes useful to others, **promote** it into `code/business_entity_resolution/src/ber/<area>/` through a PR, owned by the area owner.
- Anything the final pipeline needs must live in `src/ber/`. The final zip contains only `code/business_entity_resolution/`.
