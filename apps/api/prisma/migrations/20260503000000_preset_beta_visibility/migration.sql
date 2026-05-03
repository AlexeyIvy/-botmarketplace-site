-- 55-T6: extend PresetVisibility with BETA between PRIVATE and PUBLIC.
--
-- Additive only — existing rows keep their PRIVATE / PUBLIC values; the
-- column default ('PRIVATE') is unchanged. No backfill required.
--
-- Note: PostgreSQL <12 cannot run "ALTER TYPE ... ADD VALUE" inside a
-- transaction block. Prisma 4+ wraps each migration in an implicit
-- transaction, but ships PostgreSQL ≥13 in the supported matrix
-- (`docs/14-deployment.md`), so the wrapping is safe in this project.
ALTER TYPE "PresetVisibility" ADD VALUE 'BETA' BEFORE 'PUBLIC';
