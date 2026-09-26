-- Rebuild all project-derived GitSkills tables.
--
-- Run this file from the repository root with:
--
--   duckdb -bail /c/data/duckdb/agent_skills_release.db \
--       < sql/rebuild_project_tables.sql
--
-- The scripts are executed in dependency order:
--
--   1. create_analysis_tables.sql
--      Recreates artifact_groupings.
--
--   2. update_artifact_groupings.sql
--      Populates derived sibling metadata for artifact_groupings.
--
--   3. create_sprint1_sample.sql
--      Recreates the frozen Sprint 1 sample tables from
--      data/sample_population.csv.
--
-- Source GitSkills tables such as artifacts, artifact_siblings, repos,
-- and mining_runs are not rebuilt by this script.
--
-- FROZEN_* validation tables are not touched.

.print '=== Rebuilding analysis tables ==='
.read sql/create_analysis_tables.sql

.print '=== Updating artifact groupings ==='
.read sql/update_artifact_groupings.sql

.print '=== Rebuilding Sprint 1 sample tables ==='
.read sql/create_sprint1_sample.sql

.print '=== Project table rebuild complete ==='