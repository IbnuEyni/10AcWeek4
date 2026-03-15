# CODEBASE.md

**Generated**: 2026-03-15 03:30:26  
**Total Modules**: 19  
**Total Datasets**: 6  
**Analysis Tool**: Brownfield Cartographer

---

## Architecture Overview

This codebase contains **19 modules** and **6 datasets**. The architecture has been analyzed using static analysis, data lineage extraction, and semantic analysis.

### Statistics

- **Modules**: 19
- **Datasets**: 6
- **Critical Modules** (top 5 by PageRank): 5
- **Entry Datasets** (data sources): 0
- **Exit Datasets** (data sinks): 6
- **High Velocity Modules**: 0
- **Dead Code Candidates**: 19
- **Documentation Drift**: 12

---

## Critical Path

The following modules are architectural hubs (highest PageRank scores):

### 1. test_select_exclude_snapshot.py

- **PageRank**: 0.0526
- **Domain**: Snapshot Testing
- **Complexity**: 26.0
- **Change Velocity**: 0 commits (30d)
- **Purpose**: This module tests dbt's snapshot selection and exclusion functionality, ensuring that users can selectively run specific snapshots using --select and --exclude flags. It validates that snapshot filter...

### 2. test_basic_snapshot.py

- **PageRank**: 0.0526
- **Domain**: Snapshot Testing
- **Complexity**: 71.0
- **Change Velocity**: 0 commits (30d)
- **Purpose**: This module contains integration tests for dbt's snapshot functionality, which enables tracking historical changes to data over time. It validates that snapshots correctly capture data changes using d...

### 3. test_snapshot_empty.py

- **PageRank**: 0.0526
- **Domain**: Snapshot Testing
- **Complexity**: 3.0
- **Change Velocity**: 0 commits (30d)
- **Purpose**: This module tests dbt's snapshot functionality with the --empty flag, which creates snapshot tables without populating them with data. It verifies that when using the --empty flag, snapshot tables rem...

### 4. fixtures.py

- **PageRank**: 0.0526
- **Domain**: Snapshot Testing
- **Complexity**: 0.0
- **Change Velocity**: 0 commits (30d)
- **Purpose**: This module provides test fixtures for dbt snapshot functionality, containing sample snapshot configurations, custom snapshot strategies, and associated test data. It exists to support testing dbt's s...

### 5. test_check_cols_updated_at_snapshot.py

- **PageRank**: 0.0526
- **Domain**: Snapshot Testing
- **Complexity**: 4.0
- **Change Velocity**: 0 commits (30d)
- **Purpose**: This module tests that dbt's snapshot functionality correctly captures timestamp-based changes when using the 'check' strategy with an 'updated_at' column. It validates that the dbt_updated_at column ...

---

## Data Sources & Sinks

### Entry Datasets (Data Sources)

These datasets have no producers (external data sources):

*No entry datasets identified*

### Exit Datasets (Data Sinks)

These datasets have no consumers (final outputs):

- **invalidate_postgres** (`N/A`)
- **seed_dbt_valid_to** (`N/A`)
- **seed_pg** (`N/A`)
- **seed_cn** (`N/A`)
- **shared_macros** (`N/A`)
- **update** (`N/A`)

---

## Known Debt

### Dead Code Candidates

Modules with zero change velocity and low PageRank:

- **test_select_exclude_snapshot.py** (Velocity: 0, PageRank: 0.0526)
- **test_basic_snapshot.py** (Velocity: 0, PageRank: 0.0526)
- **test_snapshot_empty.py** (Velocity: 0, PageRank: 0.0526)
- **fixtures.py** (Velocity: 0, PageRank: 0.0526)
- **test_check_cols_updated_at_snapshot.py** (Velocity: 0, PageRank: 0.0526)
- **test_hard_delete_snapshot.py** (Velocity: 0, PageRank: 0.0526)
- **test_missing_strategy_snapshot.py** (Velocity: 0, PageRank: 0.0526)
- **test_invalid_namespace_snapshot.py** (Velocity: 0, PageRank: 0.0526)
- **test_check_cols_snapshot.py** (Velocity: 0, PageRank: 0.0526)
- **test_snapshot_config.py** (Velocity: 0, PageRank: 0.0526)

### Documentation Drift

Modules where docstrings don't match implementation:

- **test_basic_snapshot.py** - This module contains integration tests for dbt's snapshot functionality, which enables tracking hist...
- **test_snapshot_empty.py** - This module tests dbt's snapshot functionality with the --empty flag, which creates snapshot tables ...
- **fixtures.py** - This module provides test fixtures for dbt snapshot functionality, containing sample snapshot config...
- **test_check_cols_updated_at_snapshot.py** - This module tests that dbt's snapshot functionality correctly captures timestamp-based changes when ...
- **test_check_cols_snapshot.py** - This module tests dbt's snapshot functionality with check strategy column tracking. It validates tha...
- **test_snapshot_config.py** - This module tests dbt snapshot configuration functionality to ensure data change tracking works corr...
- **test_long_text_snapshot.py** - This module tests dbt's snapshot functionality with long text fields to ensure data integrity when h...
- **test_changing_strategy_snapshot.py** - This module tests dbt's snapshot functionality when switching between snapshot strategies (check vs ...
- **test_snapshot_column_names.py** - This module tests dbt's snapshot functionality with custom column name configurations. It validates ...
- **test_snapshot_timestamps.py** - This module tests dbt snapshot functionality with timestamp-based change detection. It validates tha...

---

## Recent Change Velocity

Modules with highest change frequency (last 30 days):

*No change velocity data available*

---

## Module Purpose Index

Complete index of all modules with purpose statements:


### Snapshot Testing (19 modules)

#### fixtures.py

- **Language**: python
- **PageRank**: 0.0526
- **Complexity**: 0.0
- **Velocity**: 0 commits (30d)
- **Purpose**: This module provides test fixtures for dbt snapshot functionality, containing sample snapshot configurations, custom snapshot strategies, and associated test data. It exists to support testing dbt's snapshotting capabilities across different database configurations and edge cases, including custom snapshot strategies, schema variations, and data validation tests.

#### test_basic_snapshot.py

- **Language**: python
- **PageRank**: 0.0526
- **Complexity**: 71.0
- **Velocity**: 0 commits (30d)
- **Purpose**: This module contains integration tests for dbt's snapshot functionality, which enables tracking historical changes to data over time. It validates that snapshots correctly capture data changes using different strategies (check, timestamp), custom configurations, and schema variations. These tests ensure data lineage and historical accuracy for business intelligence and compliance reporting.

#### test_changing_check_cols_snapshot.py

- **Language**: python
- **PageRank**: 0.0526
- **Complexity**: 6.0
- **Velocity**: 0 commits (30d)
- **Purpose**: This module tests dbt's snapshot functionality with the 'check' strategy when columns are added to source data. It verifies that snapshots can handle schema evolution by properly detecting changes when new columns are included in check_cols configuration, ensuring data integrity is maintained during incremental schema changes.

#### test_changing_strategy_snapshot.py

- **Language**: python
- **PageRank**: 0.0526
- **Complexity**: 4.0
- **Velocity**: 0 commits (30d)
- **Purpose**: This module tests dbt's snapshot functionality when switching between snapshot strategies (check vs timestamp). It validates that changing strategies mid-process correctly captures data changes by simulating a three-step workflow: initial check strategy, adding timestamp columns, then switching to timestamp strategy. This ensures data integrity is maintained during strategy transitions in data pipeline operations.

#### test_check_cols_snapshot.py

- **Language**: python
- **PageRank**: 0.0526
- **Complexity**: 3.0
- **Velocity**: 0 commits (30d)
- **Purpose**: This module tests dbt's snapshot functionality with check strategy column tracking. It validates that when source data changes over multiple versions, the snapshot correctly tracks historical values, invalidates old records, and maintains proper current state. The test ensures data lineage and change tracking work correctly for business-critical historical data analysis.

#### test_check_cols_updated_at_snapshot.py

- **Language**: python
- **PageRank**: 0.0526
- **Complexity**: 4.0
- **Velocity**: 0 commits (30d)
- **Purpose**: This module tests that dbt's snapshot functionality correctly captures timestamp-based changes when using the 'check' strategy with an 'updated_at' column. It validates that the dbt_updated_at column properly reflects the timestamp expression provided in the snapshot configuration by comparing actual snapshot results against expected data across multiple snapshot runs. This ensures data lineage and change tracking work correctly for time-sensitive data pipelines.

#### test_comment_ending_snapshot.py

- **Language**: python
- **PageRank**: 0.0526
- **Complexity**: 3.0
- **Velocity**: 0 commits (30d)
- **Purpose**: This module tests that dbt snapshots work correctly when SQL comments appear at the end of snapshot blocks. It specifically prevents a regression of GitHub issue #6781 where trailing comments caused parsing errors. The test creates a snapshot with a trailing comment, runs it twice to ensure proper table creation and column checking, and verifies the snapshot executes successfully.

#### test_cross_schema_snapshot.py

- **Language**: python
- **PageRank**: 0.0526
- **Complexity**: 4.0
- **Velocity**: 0 commits (30d)
- **Purpose**: This module tests dbt's ability to create snapshots in one schema and reference them from another schema. It validates cross-schema snapshot functionality by creating a snapshot in a separate target schema and then running models that reference that snapshot. This ensures data consistency and referential integrity when snapshots are stored in different schemas than the models that use them.

#### test_hard_delete_snapshot.py

- **Language**: python
- **PageRank**: 0.0526
- **Complexity**: 8.0
- **Velocity**: 0 commits (30d)
- **Purpose**: This module tests dbt's snapshot functionality for handling hard deletes in data pipelines. It verifies that when records are physically deleted from source tables, the snapshot mechanism correctly marks them as invalidated with proper timestamps, and can properly revive records when they're re-added. This ensures data lineage and historical tracking remain accurate even when source data undergoes hard deletions.

#### test_invalid_namespace_snapshot.py

- **Language**: python
- **PageRank**: 0.0526
- **Complexity**: 5.0
- **Velocity**: 0 commits (30d)
- **Purpose**: This module tests dbt's snapshot functionality when a custom snapshot strategy references an invalid namespace. It verifies that dbt properly handles and fails when attempting to use a non-existent custom snapshot strategy ('dbt.custom'), ensuring the system correctly validates strategy references and prevents execution with invalid configurations.

#### test_long_text_snapshot.py

- **Language**: python
- **PageRank**: 0.0526
- **Complexity**: 4.0
- **Velocity**: 0 commits (30d)
- **Purpose**: This module tests dbt's snapshot functionality with long text fields to ensure data integrity when handling large string values. It validates that snapshot tables correctly capture and store text data exceeding typical column lengths, preventing data truncation or corruption in change data capture scenarios. This ensures reliable historical tracking of text-heavy data in data warehousing pipelines.

#### test_missing_strategy_snapshot.py

- **Language**: python
- **PageRank**: 0.0526
- **Complexity**: 4.0
- **Velocity**: 0 commits (30d)
- **Purpose**: This module is a test that validates dbt's snapshot configuration validation logic. It specifically tests that dbt properly raises an error when a snapshot configuration is missing the mandatory 'strategy' parameter, ensuring data integrity by preventing incomplete snapshot configurations from being deployed. This helps maintain data reliability in data transformation pipelines by enforcing required configuration parameters.

#### test_renamed_source_snapshot.py

- **Language**: python
- **PageRank**: 0.0526
- **Complexity**: 4.0
- **Velocity**: 0 commits (30d)
- **Purpose**: This module tests dbt's snapshot functionality when the underlying data source changes structure (specifically when a new column is added). It verifies that snapshots correctly handle schema evolution by ensuring data integrity is maintained when switching between different seed files with varying column structures. The test validates that snapshot tables properly accommodate new columns while preserving existing data.

#### test_select_exclude_snapshot.py

- **Language**: python
- **PageRank**: 0.0526
- **Complexity**: 26.0
- **Velocity**: 0 commits (30d)
- **Purpose**: This module tests dbt's snapshot selection and exclusion functionality, ensuring that users can selectively run specific snapshots using --select and --exclude flags. It validates that snapshot filtering works correctly with both basic and configured snapshot definitions, verifying that only intended snapshots are created or updated during dbt runs.

#### test_slow_query_snapshot.py

- **Language**: python
- **PageRank**: 0.0526
- **Complexity**: 4.0
- **Velocity**: 0 commits (30d)
- **Purpose**: This module tests dbt's timestamp-based snapshot functionality to ensure data versioning works correctly over time. It validates that when records are updated, the new version's valid_from timestamp matches the previous version's valid_to timestamp, maintaining proper temporal continuity for historical data tracking. This ensures data integrity in slowly changing dimension scenarios where audit trails are critical.

#### test_snapshot_column_names.py

- **Language**: python
- **PageRank**: 0.0526
- **Complexity**: 14.0
- **Velocity**: 0 commits (30d)
- **Purpose**: This module tests dbt's snapshot functionality with custom column name configurations. It validates that snapshot metadata columns (like valid_from, valid_to, scd_id) can be renamed through configuration, ensuring data teams can maintain consistent naming conventions across their data warehouse. The tests verify both model-level and project-level configuration approaches work correctly and detect configuration errors.

#### test_snapshot_config.py

- **Language**: python
- **PageRank**: 0.0526
- **Complexity**: 4.0
- **Velocity**: 0 commits (30d)
- **Purpose**: This module tests dbt snapshot configuration functionality to ensure data change tracking works correctly. It validates that snapshots can be configured both inline within SQL files and externally via YAML schema files, ensuring data teams can reliably track historical changes to critical business data like order statuses.

#### test_snapshot_empty.py

- **Language**: python
- **PageRank**: 0.0526
- **Complexity**: 3.0
- **Velocity**: 0 commits (30d)
- **Purpose**: This module tests dbt's snapshot functionality with the --empty flag, which creates snapshot tables without populating them with data. It verifies that when using the --empty flag, snapshot tables remain empty even after multiple runs, ensuring the flag works correctly for scenarios where empty snapshot structures are needed for data modeling or testing purposes.

#### test_snapshot_timestamps.py

- **Language**: python
- **PageRank**: 0.0526
- **Complexity**: 4.0
- **Velocity**: 0 commits (30d)
- **Purpose**: This module tests dbt snapshot functionality with timestamp-based change detection. It validates that snapshots correctly capture data changes over time by creating source data, running models, and checking snapshot behavior. The test ensures the timestamp strategy works properly and provides appropriate configuration feedback.


---

## How to Use This Document

1. **New Engineers**: Start with Architecture Overview and Critical Path
2. **Bug Fixes**: Check Module Purpose Index for relevant modules
3. **Refactoring**: Review Known Debt section for improvement opportunities
4. **Data Flow**: Trace from Data Sources through Critical Path to Data Sinks

**Generated by**: Brownfield Cartographer Archivist Agent  
**Last Updated**: 2026-03-15 03:30:26
