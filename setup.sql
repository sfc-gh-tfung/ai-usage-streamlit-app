/*
 * AI on Snowflake — One-time Setup
 *
 * Instructions:
 *   1. Open a Snowflake worksheet (ACCOUNTADMIN role recommended).
 *   2. Replace the placeholder values below with your own.
 *   3. Run this entire script.
 *   4. Deploy the app using:  ./deploy.sh <your_connection>
 */

-- ============================================================
-- STEP 1: Set your configuration (edit these values)
-- ============================================================
SET db_name      = 'AI_MONITOR_DB';
SET schema_name  = 'STREAMLIT_APP';
SET warehouse    = 'COMPUTE_WH';

-- ============================================================
-- STEP 2: Create database and schema
-- ============================================================
CREATE DATABASE IF NOT EXISTS IDENTIFIER($db_name);
USE DATABASE IDENTIFIER($db_name);

CREATE SCHEMA IF NOT EXISTS IDENTIFIER($schema_name);
USE SCHEMA IDENTIFIER($schema_name);

-- ============================================================
-- STEP 3: Create compute pool for container runtime
-- ============================================================
CREATE COMPUTE POOL IF NOT EXISTS STREAMLIT_COMPUTE_POOL
  MIN_NODES = 1
  MAX_NODES = 2
  INSTANCE_FAMILY = CPU_X64_XS
  AUTO_SUSPEND_SECS = 3600
  AUTO_RESUME = TRUE;

-- ============================================================
-- STEP 4: Create external access integration for PyPI
-- ============================================================
-- If you already have a PYPI_ACCESS_INTEGRATION, skip this step.
-- CREATE OR REPLACE NETWORK RULE pypi_network_rule
--   MODE = EGRESS
--   TYPE = HOST_PORT
--   VALUE_LIST = ('pypi.org', 'files.pythonhosted.org');

-- CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION PYPI_ACCESS_INTEGRATION
--   ALLOWED_NETWORK_RULES = (pypi_network_rule)
--   ENABLED = TRUE;

-- ============================================================
-- STEP 5: Grant access to ACCOUNT_USAGE views
-- ============================================================
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE IDENTIFIER(CURRENT_ROLE());

-- ============================================================
-- STEP 6: Deploy the app
-- ============================================================
-- After running this setup, deploy the app using the deploy.sh script:
--   chmod +x deploy.sh
--   ./deploy.sh <your_connection>
--
-- Or manually via snow CLI:
--   snow streamlit deploy --replace --connection <your_connection>
