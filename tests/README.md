# Test Suite - Data Pipeline

## Philosophy

This test suite validates **pipeline behavior and orchestration**, not table structures or data transformations.

Tests focus on:
- ✅ **Pipeline orchestration** (DAG structure, task dependencies, execution order)
- ✅ **Component integration** (Bronze → Silver → Gold flow)
- ✅ **Operational patterns** (idempotency, retries, error handling)
- ✅ **Data quality framework** (Great Expectations integration)

Tests **do NOT** focus on:
- ❌ Table schemas or column structures
- ❌ Specific data transformations
- ❌ Field-level validation rules
- ❌ Domain-specific business logic

## Structure

```
tests/
├── unit/                                    # Component behavior tests
│   ├── test_bronze_layer_pattern.py        # Bronze layer behavior
│   ├── test_data_quality_framework.py      # Great Expectations integration
│   ├── test_brewery_client.py              # API client (can be removed)
│   ├── test_bronze_processor.py            # Bronze processor (can be removed)
│   └── test_silver_processor.py            # Silver processor (can be removed)
│
├── integration/                             # Pipeline integration tests
│   ├── test_pipeline_orchestration.py      # ✨ DAG structure and orchestration
│   ├── test_medallion_pipeline_flow.py     # Layer-to-layer flow
│   └── test_pipeline_e2e.py                # Full pipeline (can be removed)
│
└── functional/                              # System behavior tests
    └── test_idempotency.py                  # Idempotency guarantees
```

## Key Test Categories

### 1. Pipeline Orchestration (test_pipeline_orchestration.py)

Tests Airflow DAG behavior:

- **DAG Structure**: Schedule, retries, catchup configuration
- **Task Dependencies**: Execution order, upstream/downstream relationships
- **Task Types**: PythonOperator, BashOperator usage
- **Error Handling**: Retry configuration, exponential backoff
- **Pipeline Integrity**: No circular dependencies, single source/sink
- **Medallion Pattern**: Bronze → Silver → Gold flow

```python
def test_extract_is_first_task():
    """Extract task should have no upstream dependencies."""

def test_linear_pipeline_structure():
    """Pipeline should be linear (no branching)."""
```

### 2. Bronze Layer Behavior (test_bronze_layer_pattern.py)

Tests Bronze layer operational patterns:

- **Schema-on-read**: Accepts any data structure
- **Raw persistence**: No transformation
- **Metadata enrichment**: Adds timestamps
- **Dual persistence**: Storage + database
- **Empty data handling**: Graceful handling

### 3. Data Quality Framework (test_data_quality_framework.py)

Tests Great Expectations integration:

- **Framework integration**: Context initialization
- **Checkpoint execution**: Running validations
- **Result handling**: Statistics extraction
- **Airflow integration**: Task callables

### 4. Pipeline Flow (test_medallion_pipeline_flow.py)

Tests complete Bronze → Silver → Gold flow:

- **Data flow**: Movement through layers
- **Quality improvement**: Increasing quality per layer
- **Metadata preservation**: Lineage tracking
- **Idempotency**: Same input → same output

### 5. Idempotency (test_idempotency.py)

Tests pipeline idempotency guarantees:

- **Deterministic results**: Same input → same output
- **No duplication**: Re-runs don't duplicate data
- **Safe retries**: Failed runs can be retried
- **State management**: Predictable state

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run pipeline orchestration tests
```bash
pytest tests/integration/test_pipeline_orchestration.py -v
```

### Run specific test class
```bash
pytest tests/integration/test_pipeline_orchestration.py::TestDAGStructure -v
```

### Run with coverage
```bash
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

### Run inside Docker container
```bash
# Enter Airflow container
docker exec -it data_engineer_bees-airflow-webserver-1 bash

# Run tests (pytest.ini automatically suppresses PySpark warnings)
pytest tests/ -v
```

**Note:** Deprecation warnings from PySpark (third-party library) are automatically suppressed via `pytest.ini` configuration.

## Test Examples

### ✅ Good: Testing Pipeline Behavior

```python
def test_dag_has_retry_configuration():
    """DAG should have retry logic configured."""
    assert dag.default_args['retries'] >= 1
```

```python
def test_linear_pipeline_structure():
    """Pipeline should be linear (no branching)."""
    for task in dag.tasks:
        if task != first and task != last:
            assert len(task.upstream_list) == 1
```

### ❌ Bad: Testing Table Structure

```python
# Don't test specific columns
def test_silver_has_brewery_type_column():
    assert "brewery_type" in silver_table.columns
```

```python
# Don't test field transformations
def test_coordinates_are_decimal_type():
    assert isinstance(longitude, Decimal)
```

## Design Principles

### 1. Test the Pipeline, Not the Data
❌ **Bad**: `assert df["brewery_type"] == "micro"`
✅ **Good**: `assert extract_task.upstream_list == []`

### 2. Test Orchestration, Not Transformation
❌ **Bad**: `assert whitespace_is_trimmed()`
✅ **Good**: `assert validate_task depends on transform_task`

### 3. Test Integration, Not Implementation
❌ **Bad**: `assert uses_pandas_dataframe()`
✅ **Good**: `assert bronze_writes_to_storage_and_database()`

### 4. Test Behavior, Not Structure
❌ **Bad**: `assert has_column("city")`
✅ **Good**: `assert rerunning_produces_same_output()`

## Coverage Goals

- **Pipeline Orchestration**: 100% of DAG structure and dependencies
- **Integration Flow**: 100% of layer-to-layer interactions
- **Operational Patterns**: 100% of idempotency, retries, error handling
- **Overall Code Coverage**: Target >70% (focused on pipeline logic, not data logic)

## Maintenance

### When to Update Tests

Update tests when:
- ✅ Adding/removing pipeline tasks
- ✅ Changing task dependencies
- ✅ Modifying retry/error handling logic
- ✅ Changing orchestration patterns

Don't update tests when:
- ❌ Adding/removing table columns
- ❌ Changing data transformation logic
- ❌ Modifying validation rules
- ❌ Updating business logic

### Adding New Tests

When adding tests:
1. **Focus on pipeline behavior**
2. **Avoid coupling to data structures**
3. **Test integration, not implementation**
4. **Use clear, behavior-focused naming**

## Quick Test Commands

```bash
# Pipeline orchestration
pytest tests/integration/test_pipeline_orchestration.py -v

# DAG structure only
pytest tests/integration/test_pipeline_orchestration.py::TestDAGStructure -v

# Task dependencies only
pytest tests/integration/test_pipeline_orchestration.py::TestTaskDependencies -v

# Idempotency
pytest tests/functional/test_idempotency.py -v

# All integration tests
pytest tests/integration/ -v

# Run fast (skip slow Spark tests)
pytest tests/ -v -m "not slow"
```

## Philosophy Summary

> **"Test that the pipeline orchestrates data flow correctly,
> not that it transforms brewery data correctly."**

Key principles:
- ✅ Validate DAG structure and dependencies
- ✅ Verify task execution order
- ✅ Ensure retry and error handling work
- ✅ Confirm pipeline is idempotent
- ✅ Check component integration
- ❌ Don't validate table schemas
- ❌ Don't test data transformations
- ❌ Don't verify field-level rules
- ❌ Don't couple to domain logic
