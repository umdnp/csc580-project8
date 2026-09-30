-- Sprint 1 sample view for the GitSkills project database.
--
-- Creates or replaces sample_artifacts using the 43 artifact IDs listed
-- below. These IDs are deterministic for the project's dataset and
-- define the selected sample without reading an external CSV file.
--
-- The view exposes all columns from matching rows in artifacts. It stores
-- the selection query rather than a separate copy of the artifact data.
-- Sample membership is defined by the embedded ID list; returned values
-- reflect the underlying artifacts table when the view is queried.
--
-- The final query reports the number of matching artifacts. The expected
-- count is 43, provided every selected ID exists in artifacts.

create or replace view sample_artifacts as
with sample_groupings as (
  select * from artifact_groupings where artifact_id in (
    1970318, 2244377, 2386167, 2386173,
    2498630, 2696303, 2723114, 3076631,
    1244165, 2690162,
    3273850, 3291033, 3315007, 3329361, 3378260,
    2627824, 2630854, 2630982,
    3485370, 3498417, 3498458, 3572584, 3602273,
    3323843, 3324967, 3347921, 3509100, 3517041,
    2449887, 2450269, 2457192, 2609593, 2616525,
    1549970, 1550041, 1580781, 1956585, 3687704,
    2044216, 2090132, 2093346, 3306314, 3335142
  )
)
select g.*, a.file_sha, a.path, a.filename, a.location_class, a.content, a.content_fetched, a.history_fetched,
  a.composition_fetched, a.dedup_primary, a.sibling_count, a.has_scripts, a.content_sha_ok,
  r.full_name repo_name, r.owner as repo_owner, r.created_at as repo_created_at
from sample_groupings g
join artifacts a on a.id=g.artifact_id
join repos r on r.id=g.repo_id
order by name;

-- Expected: 43, provided every selected ID exists.
SELECT COUNT(*) AS sample_artifact_count
FROM sample_artifacts;