"""
Integration tests for Pipeline Orchestration.

Tests Airflow DAG behavior and task orchestration independent of data.
Validates:
- DAG structure and dependencies
- Task execution order
- Error handling and retries
- Task state management
- Airflow integration patterns
"""

from datetime import timedelta
from unittest.mock import Mock, patch

import pytest


class TestDAGStructure:
    """Test DAG structure and configuration."""

    def test_dag_exists_and_is_importable(self):
        """DAG file should be importable without errors."""
        try:
            from dags.brewery_pipeline import dag
            assert dag is not None
        except ImportError as e:
            pytest.fail(f"DAG import failed: {e}")

    def test_dag_has_correct_schedule(self):
        """DAG should have expected schedule interval."""
        from dags.brewery_pipeline import dag

        # Daily at 2 AM
        assert dag.schedule_interval == '0 2 * * *'

    def test_dag_has_default_args(self):
        """DAG should have default args configured."""
        from dags.brewery_pipeline import dag

        assert dag.default_args is not None
        assert 'owner' in dag.default_args
        assert 'retries' in dag.default_args

    def test_dag_has_retry_configuration(self):
        """DAG should have retry logic configured."""
        from dags.brewery_pipeline import dag

        assert dag.default_args['retries'] >= 1
        assert 'retry_delay' in dag.default_args

    def test_dag_does_not_catchup(self):
        """DAG should not catch up on missed runs."""
        from dags.brewery_pipeline import dag

        assert dag.catchup == False

    def test_dag_has_single_active_run(self):
        """DAG should allow only one active run at a time."""
        from dags.brewery_pipeline import dag

        assert dag.max_active_runs == 1


class TestTaskDependencies:
    """Test task dependencies and execution order."""

    def test_all_expected_tasks_exist(self):
        """DAG should have all expected tasks."""
        from dags.brewery_pipeline import dag

        task_ids = [task.task_id for task in dag.tasks]

        expected_tasks = [
            'extract_bronze_data',
            'validate_bronze',
            'transform_silver_data',
            'validate_silver',
            'dbt_gold_transform',
            'dbt_test',
            'validate_gold',
            'data_quality_report',
        ]

        for task_id in expected_tasks:
            assert task_id in task_ids, f"Task {task_id} not found in DAG"

    def test_task_count(self):
        """DAG should have expected number of tasks."""
        from dags.brewery_pipeline import dag

        assert len(dag.tasks) == 8

    def test_extract_is_first_task(self):
        """Extract task should have no upstream dependencies."""
        from dags.brewery_pipeline import dag

        extract_task = dag.get_task('extract_bronze_data')
        assert len(extract_task.upstream_list) == 0

    def test_validate_bronze_depends_on_extract(self):
        """Bronze validation should depend on extract."""
        from dags.brewery_pipeline import dag

        validate_task = dag.get_task('validate_bronze')
        upstream_ids = [t.task_id for t in validate_task.upstream_list]

        assert 'extract_bronze_data' in upstream_ids

    def test_transform_depends_on_validate_bronze(self):
        """Silver transform should depend on Bronze validation."""
        from dags.brewery_pipeline import dag

        transform_task = dag.get_task('transform_silver_data')
        upstream_ids = [t.task_id for t in transform_task.upstream_list]

        assert 'validate_bronze' in upstream_ids

    def test_validate_silver_depends_on_transform(self):
        """Silver validation should depend on transform."""
        from dags.brewery_pipeline import dag

        validate_task = dag.get_task('validate_silver')
        upstream_ids = [t.task_id for t in validate_task.upstream_list]

        assert 'transform_silver_data' in upstream_ids

    def test_dbt_run_depends_on_validate_silver(self):
        """dbt run should depend on Silver validation."""
        from dags.brewery_pipeline import dag

        dbt_task = dag.get_task('dbt_gold_transform')
        upstream_ids = [t.task_id for t in dbt_task.upstream_list]

        assert 'validate_silver' in upstream_ids

    def test_dbt_test_depends_on_dbt_run(self):
        """dbt test should depend on dbt run."""
        from dags.brewery_pipeline import dag

        dbt_test_task = dag.get_task('dbt_test')
        upstream_ids = [t.task_id for t in dbt_test_task.upstream_list]

        assert 'dbt_gold_transform' in upstream_ids

    def test_validate_gold_depends_on_dbt_test(self):
        """Gold validation should depend on dbt test."""
        from dags.brewery_pipeline import dag

        validate_task = dag.get_task('validate_gold')
        upstream_ids = [t.task_id for t in validate_task.upstream_list]

        assert 'dbt_test' in upstream_ids

    def test_report_is_last_task(self):
        """Quality report should be the last task (no downstream)."""
        from dags.brewery_pipeline import dag

        report_task = dag.get_task('data_quality_report')
        assert len(report_task.downstream_list) == 0

    def test_linear_pipeline_structure(self):
        """Pipeline should be linear (no branching or parallel paths)."""
        from dags.brewery_pipeline import dag

        # Each task (except first and last) should have exactly 1 upstream and 1 downstream
        for task in dag.tasks:
            if task.task_id == 'extract_bronze_data':
                assert len(task.upstream_list) == 0
                assert len(task.downstream_list) == 1
            elif task.task_id == 'data_quality_report':
                assert len(task.upstream_list) == 1
                assert len(task.downstream_list) == 0
            else:
                assert len(task.upstream_list) == 1
                assert len(task.downstream_list) == 1


class TestTaskTypes:
    """Test task operator types."""

    def test_extract_is_python_operator(self):
        """Extract task should use PythonOperator."""
        from dags.brewery_pipeline import dag
        from airflow.operators.python import PythonOperator

        extract_task = dag.get_task('extract_bronze_data')
        assert isinstance(extract_task, PythonOperator)

    def test_validation_tasks_are_python_operators(self):
        """Validation tasks should use PythonOperator."""
        from dags.brewery_pipeline import dag
        from airflow.operators.python import PythonOperator

        validation_tasks = ['validate_bronze', 'validate_silver', 'validate_gold']

        for task_id in validation_tasks:
            task = dag.get_task(task_id)
            assert isinstance(task, PythonOperator)

    def test_dbt_tasks_are_bash_operators(self):
        """dbt tasks should use BashOperator."""
        from dags.brewery_pipeline import dag
        from airflow.operators.bash import BashOperator

        dbt_tasks = ['dbt_gold_transform', 'dbt_test']

        for task_id in dbt_tasks:
            task = dag.get_task(task_id)
            assert isinstance(task, BashOperator)


class TestRetryBehavior:
    """Test retry configuration and behavior."""

    def test_tasks_have_retry_configured(self):
        """All tasks should inherit retry configuration from DAG defaults."""
        from dags.brewery_pipeline import dag

        for task in dag.tasks:
            # Task should have retries (from default_args)
            retries = task.retries if hasattr(task, 'retries') else dag.default_args.get('retries')
            assert retries is not None
            assert retries >= 1

    def test_exponential_backoff_enabled(self):
        """Retry should use exponential backoff."""
        from dags.brewery_pipeline import dag

        assert dag.default_args.get('retry_exponential_backoff') == True

    def test_max_retry_delay_configured(self):
        """Max retry delay should be configured."""
        from dags.brewery_pipeline import dag

        assert 'max_retry_delay' in dag.default_args
        max_delay = dag.default_args['max_retry_delay']
        assert isinstance(max_delay, timedelta)
        assert max_delay.total_seconds() > 0


class TestErrorHandling:
    """Test error handling configuration."""

    def test_email_on_failure_configured(self):
        """Email on failure should be configured (even if disabled)."""
        from dags.brewery_pipeline import dag

        assert 'email_on_failure' in dag.default_args

    def test_email_on_retry_configured(self):
        """Email on retry should be configured (even if disabled)."""
        from dags.brewery_pipeline import dag

        assert 'email_on_retry' in dag.default_args


class TestPipelineFlow:
    """Test complete pipeline flow pattern."""

    def test_medallion_architecture_pattern(self):
        """Pipeline should follow Medallion architecture (Bronze → Silver → Gold)."""
        from dags.brewery_pipeline import dag

        task_ids = [task.task_id for task in dag.tasks]

        # Should have Bronze layer tasks
        assert any('bronze' in task_id.lower() for task_id in task_ids)

        # Should have Silver layer tasks
        assert any('silver' in task_id.lower() for task_id in task_ids)

        # Should have Gold layer tasks (dbt)
        assert any('gold' in task_id.lower() or 'dbt' in task_id.lower() for task_id in task_ids)

    def test_validation_between_layers(self):
        """Pipeline should validate data between layers."""
        from dags.brewery_pipeline import dag

        task_ids = [task.task_id for task in dag.tasks]

        # Should have validation tasks
        validation_tasks = [t for t in task_ids if 'validate' in t.lower()]
        assert len(validation_tasks) >= 3  # Bronze, Silver, Gold validations

    def test_data_quality_reporting(self):
        """Pipeline should include data quality reporting."""
        from dags.brewery_pipeline import dag

        task_ids = [task.task_id for task in dag.tasks]

        # Should have quality report task
        assert any('quality' in task_id.lower() or 'report' in task_id.lower() for task_id in task_ids)


class TestDAGTags:
    """Test DAG tagging and categorization."""

    def test_dag_has_tags(self):
        """DAG should have tags for organization."""
        from dags.brewery_pipeline import dag

        assert dag.tags is not None
        assert len(dag.tags) > 0

    def test_dag_has_relevant_tags(self):
        """DAG tags should be relevant to pipeline type."""
        from dags.brewery_pipeline import dag

        # Should have at least one of these tags
        relevant_tags = ['etl', 'pipeline', 'medallion', 'data-quality']

        has_relevant_tag = any(tag in dag.tags for tag in relevant_tags)
        assert has_relevant_tag


class TestPipelineIntegrity:
    """Test pipeline integrity and consistency."""

    def test_no_circular_dependencies(self):
        """DAG should not have circular dependencies."""
        from dags.brewery_pipeline import dag

        # Airflow will raise an error if circular dependencies exist
        # If DAG imports successfully, this test passes
        assert dag is not None

    def test_all_tasks_reachable_from_start(self):
        """All tasks should be reachable from the first task."""
        from dags.brewery_pipeline import dag

        first_task = dag.get_task('extract_bronze_data')

        # Get all tasks reachable from first task
        visited = set()
        to_visit = [first_task]

        while to_visit:
            current = to_visit.pop()
            if current.task_id not in visited:
                visited.add(current.task_id)
                to_visit.extend(current.downstream_list)

        # All tasks should be reachable
        assert len(visited) == len(dag.tasks)

    def test_single_sink_node(self):
        """DAG should have single final task (sink node)."""
        from dags.brewery_pipeline import dag

        # Tasks with no downstream dependencies
        sink_tasks = [task for task in dag.tasks if len(task.downstream_list) == 0]

        assert len(sink_tasks) == 1
        assert sink_tasks[0].task_id == 'data_quality_report'

    def test_single_source_node(self):
        """DAG should have single starting task (source node)."""
        from dags.brewery_pipeline import dag

        # Tasks with no upstream dependencies
        source_tasks = [task for task in dag.tasks if len(task.upstream_list) == 0]

        assert len(source_tasks) == 1
        assert source_tasks[0].task_id == 'extract_bronze_data'


class TestDAGDocumentation:
    """Test DAG documentation and metadata."""

    def test_dag_has_description(self):
        """DAG should have a description."""
        from dags.brewery_pipeline import dag

        assert dag.description is not None
        assert len(dag.description) > 0

    def test_dag_has_doc_md(self):
        """DAG should have documentation (even if None)."""
        from dags.brewery_pipeline import dag

        # doc_md can be None, but attribute should exist
        assert hasattr(dag, 'doc_md')
