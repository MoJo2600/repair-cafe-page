-- Fix dates set to today (2026-07-18) during data migration.
-- Sets repair_logs.created_at and repairs.closed_at to repairs.datum
-- for all records whose date currently equals the migration date.

-- Adjust this constant if the migration was run on a different date.
SET @migration_date = '2026-07-18';

-- 1. Fix repair_logs.created_at
UPDATE repair_logs rl
JOIN repairs r ON r.id = rl.repair_id
SET rl.created_at = CAST(r.datum AS DATETIME)
WHERE DATE(rl.created_at) = @migration_date;

-- 2. Fix repairs.closed_at (only for closed repairs that have a closed_at set)
UPDATE repairs
SET closed_at = CAST(datum AS DATETIME)
WHERE closed_at IS NOT NULL
  AND DATE(closed_at) = @migration_date;
