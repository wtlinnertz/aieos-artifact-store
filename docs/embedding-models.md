# Embedding Model Selection

## Model Comparison

| Model | Dimensions | Speed | Quality | Cost | Provider Neutral |
|-------|-----------|-------|---------|------|-----------------|
| `all-MiniLM-L6-v2` | 384 | Fast | Good | Free (local) | Yes |
| `all-mpnet-base-v2` | 768 | Medium | Better | Free (local) | Yes |
| `nomic-embed-text` | 768 | Fast | Very good | Free (local) | Yes |
| `text-embedding-3-small` | 1536 | Fast | Best | $0.02/1M tokens | No |

## Default: all-MiniLM-L6-v2

The default model is `all-MiniLM-L6-v2` from the sentence-transformers library. Rationale:

- **Local execution.** No API key, no network call, no cost. Runs on CPU in under a second for typical AIEOS artifacts.
- **Provider neutral.** AIEOS governance policy prohibits vendor-specific dependencies in core tooling. A local model satisfies this constraint.
- **Good enough for the domain.** AIEOS artifacts are structured Markdown with consistent terminology. The vocabulary is narrow (governance, architecture, deployment, testing). A smaller model with good general-purpose embeddings performs well in this domain.
- **Fast reindexing.** The full AIEOS artifact corpus for a typical organization (10-50 initiatives, 500-2000 frozen artifacts) indexes in under 60 seconds on a laptop CPU.
- **384 dimensions.** Smaller vectors mean faster search, smaller store, and lower memory usage. For the corpus sizes expected in AIEOS usage, this is more than sufficient.

## Upgrade Path: all-mpnet-base-v2

If search quality is insufficient (e.g., relevant chunks are not surfacing in the top 5 results), the first upgrade is `all-mpnet-base-v2`:

- Same library, same local execution, same cost (free).
- 768 dimensions provide better semantic discrimination.
- Roughly 2x slower embedding and 2x larger store.
- No code changes required beyond updating the config.

## Future Option: nomic-embed-text

The `nomic-embed-text` model offers very good quality at 768 dimensions with fast inference. It requires the `nomic` package. This is a strong candidate if the project moves beyond sentence-transformers.

## Non-Recommended: text-embedding-3-small

OpenAI's `text-embedding-3-small` produces the highest quality embeddings in benchmarks, but it requires an API key and network access. This breaks the AIEOS provider-neutrality principle and introduces a runtime dependency on an external service. It is listed here for completeness but is not recommended for the default configuration.

If an organization chooses to use it, they accept the provider coupling and should document the decision as a deviation from provider-neutral policy.

## How to Switch Models

1. Update the `AIEOS_EMBED_MODEL` environment variable or edit `src/config.py`.
2. Run `bash scripts/reindex.sh` to drop the existing store and rebuild with the new model.

The store must be fully rebuilt when switching models because embeddings from different models are not comparable. There is no migration path — reindex is the only option.
