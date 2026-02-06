-- migrate.sql
ALTER TABLE colaboradores ADD COLUMN IF NOT EXISTS complemento VARCHAR(100);