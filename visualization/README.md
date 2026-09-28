# Local skill relationship explorer

From the repository root, using your Python environment:

```sh
python -m pip install -r visualization/requirements.txt
python -m uvicorn visualization.app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Generate reports with the existing family-analysis
workflow into `work/`, then select a JSON report. The app does not run analysis
or change source data. To use another report folder, set `GITSKILLS_REPORT_DIR`
before starting the server. File paths are resolved independently of the shell's
working directory. Stop the server with Ctrl+C.

The viewer supports cluster selection, artifact-ID lookup across clusters,
parent/child navigation, ancestor/descendant views, pan, zoom, and comparison
details. All interface assets are local; no CDN or frontend build is required.

## Report handling and interpretation

- Expected format: `analyze_family_diffs` output with `artifact_count`,
  `cluster_count`, `comparisons`, and `ambiguous_relationships`.
- Reports are parsed on first access. A compact index of one report is cached;
  changing a file's size or modification time invalidates its cache. Switching
  reports rebuilds the index. Initial parsing temporarily holds the full JSON
  and can use substantially more memory than the file's size. Use one worker
  for local use to avoid duplicate caches.
- Only a selected cluster's compact graph is sent to the browser. Ambiguous
  pairs are counted, not rendered or assigned a direction. Individual ambiguous
  pair inspection is not implemented.
- Arrows are inferred source-to-target relationships, not proof of copying.
  Multiple parents and cycles can occur; the graph is not necessarily a tree.
  A cycle warning means the layered layout must not be read as generation order.
- Artifacts whose IDs do not occur in relationships cannot be drawn from the
  current report format. They are reported as an unlisted count.
- The viewer uses artifact IDs and does not expose raw report files, source
  bodies, or repository metadata. IDs remain linkable to local dataset records.
- This is a local application without authentication. Keep the default loopback
  address; do not expose it publicly without a separate deployment review.

API documentation is available locally at `/docs`.

## Tests

Install `httpx` in the test environment, then run from the repository root:

```sh
python -m unittest visualization.test_app
```
