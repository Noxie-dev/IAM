"""
Unit tests for DICE™ Orchestrator
Tests the complete DICE pipeline coordination and workflow management
"""

import pytest
import asyncio
import uuid
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime

# Mock the problematic imports first
with patch.dict('sys.modules', {
    'app.core.database': MagicMock(get_async_session=AsyncMock()),
    'app.models.dice_job': MagicMock()
}):
    from app.services.dice_orchestrator import DICEOrchestrator
from app.models.dice_job import DiceJob, DiceJobLog
from app.schemas.dice_schemas import (
    FileInfo, PreScanJSON, DraftTranscriptJSON, 
    ValidationReportJSON, FinalMinutes, DiceJobStatus
)
from tests.fixtures.dice_test_data import DICETestFixtures, DICETestConstants


class TestDICEOrchestrator:
    """Test suite for DICE Orchestrator"""
    
    @pytest.fixture
    def job_id(self):
        """Create a test job ID"""
        return uuid.uuid4()
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session"""
        session = AsyncMock()
        return session
    
    @pytest.fixture
    def sample_dice_job(self, job_id):
        """Create a sample DICE job for testing"""
        return DiceJob(
            id=job_id,
            user_id=uuid.uuid4(),
            status=DiceJobStatus.PENDING,
            files_uploaded=[
                DICETestFixtures.create_sample_file_info(),
                DICETestFixtures.create_sample_audio_file_info()
            ],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.fixture
    async def dice_orchestrator(self, job_id, mock_db_session, sample_dice_job):
        """Create a DICE Orchestrator instance for testing"""
        with patch('app.services.dice_orchestrator.get_async_session') as mock_get_session:
            mock_get_session.return_value.__anext__.return_value = mock_db_session
            
            # Mock database query
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = sample_dice_job
            mock_db_session.execute.return_value = mock_result
            
            orchestrator = DICEOrchestrator(job_id, mock_db_session)
            await orchestrator._load_job()
            
            return orchestrator
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, job_id, mock_db_session):
        """Test DICE Orchestrator initialization"""
        with patch('app.services.dice_orchestrator.get_async_session') as mock_get_session:
            mock_get_session.return_value.__anext__.return_value = mock_db_session
            
            orchestrator = DICEOrchestrator(job_id, mock_db_session)
            
            # Verify initialization
            assert orchestrator.job_id == job_id
            assert orchestrator.db == mock_db_session
            assert orchestrator.prescan_algo is not None
            assert orchestrator.ai_layer_1 is not None
            assert orchestrator.validator is not None
            assert orchestrator.ai_layer_2 is not None
            assert orchestrator.tts_service is not None
    
    @pytest.mark.asyncio
    async def test_process_complete_pipeline(self, dice_orchestrator):
        """Test complete DICE pipeline processing"""
        # Mock all algorithm responses
        mock_prescan_result = DICETestFixtures.create_sample_prescan_result()
        mock_draft_transcript = DICETestFixtures.create_sample_draft_transcript()
        mock_validation_report = DICETestFixtures.create_sample_validation_report()
        mock_final_minutes = DICETestFixtures.create_sample_final_minutes()
        
        with patch.object(dice_orchestrator.prescan_algo, 'process_files', new_callable=AsyncMock, return_value=mock_prescan_result) as mock_prescan, \
             patch.object(dice_orchestrator.ai_layer_1, 'generate_transcript', new_callable=AsyncMock, return_value=mock_draft_transcript) as mock_ai1, \
             patch.object(dice_orchestrator.validator, 'validate_transcript', new_callable=AsyncMock, return_value=mock_validation_report) as mock_validate, \
             patch.object(dice_orchestrator.ai_layer_2, 'generate_final_minutes', new_callable=AsyncMock, return_value=mock_final_minutes) as mock_ai2, \
             patch.object(dice_orchestrator, '_update_job_status', new_callable=AsyncMock) as mock_update_status, \
             patch.object(dice_orchestrator, '_log_event', new_callable=AsyncMock) as mock_log:
            
            result = await dice_orchestrator.process_complete_pipeline()
            
            # Verify all stages were executed
            mock_prescan.assert_called_once()
            mock_ai1.assert_called_once()
            mock_validate.assert_called_once()
            mock_ai2.assert_called_once()
            
            # Verify status updates
            assert mock_update_status.call_count >= 4  # Start + each stage completion
            
            # Verify logging
            assert mock_log.call_count >= 4
            
            # Verify result
            assert isinstance(result, FinalMinutes)
            assert result.title is not None
            assert result.confidence_score > 0.0
    
    @pytest.mark.asyncio
    async def test_error_handling_in_pipeline(self, dice_orchestrator):
        """Test error handling during pipeline execution"""
        # Mock an error in AI Layer 1
        with patch.object(dice_orchestrator.prescan_algo, 'process_files', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_prescan_result()), \
             patch.object(dice_orchestrator.ai_layer_1, 'generate_transcript', side_effect=Exception("AI processing failed")) as mock_ai1, \
             patch.object(dice_orchestrator, '_update_job_status', new_callable=AsyncMock) as mock_update_status, \
             patch.object(dice_orchestrator, '_log_event', new_callable=AsyncMock) as mock_log:
            
            with pytest.raises(Exception):
                await dice_orchestrator.process_complete_pipeline()
            
            # Verify error was logged
            error_logs = [call for call in mock_log.call_args_list if call[0][0] == "error"]
            assert len(error_logs) > 0
            
            # Verify status was updated to failed
            failed_status_calls = [call for call in mock_update_status.call_args_list 
                                 if call[0][0] == DiceJobStatus.FAILED]
            assert len(failed_status_calls) > 0
    
    @pytest.mark.asyncio
    async def test_prescan_stage_execution(self, dice_orchestrator):
        """Test PreScan stage execution"""
        mock_result = DICETestFixtures.create_sample_prescan_result()
        
        with patch.object(dice_orchestrator.prescan_algo, 'process_files', new_callable=AsyncMock, return_value=mock_result) as mock_prescan, \
             patch.object(dice_orchestrator, '_log_event', new_callable=AsyncMock) as mock_log:
            
            result = await dice_orchestrator._execute_prescan_stage()
            
            # Verify execution
            mock_prescan.assert_called_once_with(dice_orchestrator.job.files_uploaded)
            assert result == mock_result
            
            # Verify logging
            start_log = next((call for call in mock_log.call_args_list if "Starting PreScan" in call[0][2]), None)
            assert start_log is not None
    
    @pytest.mark.asyncio
    async def test_ai_layer_1_stage_execution(self, dice_orchestrator):
        """Test AI Layer 1 stage execution"""
        prescan_result = DICETestFixtures.create_sample_prescan_result()
        mock_transcript = DICETestFixtures.create_sample_draft_transcript()
        
        with patch.object(dice_orchestrator.ai_layer_1, 'generate_transcript', new_callable=AsyncMock, return_value=mock_transcript) as mock_ai1, \
             patch.object(dice_orchestrator, '_log_event', new_callable=AsyncMock) as mock_log:
            
            result = await dice_orchestrator._execute_ai_layer_1_stage(prescan_result)
            
            # Verify execution
            mock_ai1.assert_called_once_with(dice_orchestrator.job.files_uploaded, prescan_result)
            assert result == mock_transcript
            
            # Verify performance logging
            perf_logs = [call for call in mock_log.call_args_list if "execution_time" in call[1]]
            assert len(perf_logs) > 0
    
    @pytest.mark.asyncio
    async def test_validation_stage_execution(self, dice_orchestrator):
        """Test Validation stage execution"""
        prescan_result = DICETestFixtures.create_sample_prescan_result()
        draft_transcript = DICETestFixtures.create_sample_draft_transcript()
        mock_validation = DICETestFixtures.create_sample_validation_report()
        
        with patch.object(dice_orchestrator.validator, 'validate_transcript', new_callable=AsyncMock, return_value=mock_validation) as mock_validate, \
             patch.object(dice_orchestrator, '_log_event', new_callable=AsyncMock) as mock_log:
            
            result = await dice_orchestrator._execute_validation_stage(prescan_result, draft_transcript)
            
            # Verify execution
            mock_validate.assert_called_once_with(prescan_result, draft_transcript)
            assert result == mock_validation
            
            # Check for validation issue logging
            if mock_validation.issues_found:
                issue_logs = [call for call in mock_log.call_args_list 
                            if "validation issues" in call[0][2].lower()]
                assert len(issue_logs) > 0
    
    @pytest.mark.asyncio
    async def test_ai_layer_2_stage_execution(self, dice_orchestrator):
        """Test AI Layer 2 stage execution"""
        prescan_result = DICETestFixtures.create_sample_prescan_result()
        draft_transcript = DICETestFixtures.create_sample_draft_transcript()
        validation_report = DICETestFixtures.create_sample_validation_report()
        mock_final_minutes = DICETestFixtures.create_sample_final_minutes()
        
        with patch.object(dice_orchestrator.ai_layer_2, 'generate_final_minutes', new_callable=AsyncMock, return_value=mock_final_minutes) as mock_ai2, \
             patch.object(dice_orchestrator, '_log_event', new_callable=AsyncMock):
            
            result = await dice_orchestrator._execute_ai_layer_2_stage(
                prescan_result, draft_transcript, validation_report
            )
            
            # Verify execution
            mock_ai2.assert_called_once_with(prescan_result, draft_transcript, validation_report)
            assert result == mock_final_minutes
    
    @pytest.mark.asyncio
    async def test_progress_tracking(self, dice_orchestrator):
        """Test progress tracking throughout pipeline"""
        with patch.object(dice_orchestrator.prescan_algo, 'process_files', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_prescan_result()), \
             patch.object(dice_orchestrator.ai_layer_1, 'generate_transcript', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_draft_transcript()), \
             patch.object(dice_orchestrator.validator, 'validate_transcript', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_validation_report()), \
             patch.object(dice_orchestrator.ai_layer_2, 'generate_final_minutes', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_final_minutes()), \
             patch.object(dice_orchestrator, '_update_job_progress', new_callable=AsyncMock) as mock_progress:
            
            await dice_orchestrator.process_complete_pipeline()
            
            # Verify progress updates
            assert mock_progress.call_count >= 4  # One for each stage
            
            # Verify progress values are increasing
            progress_values = [call[0][0] for call in mock_progress.call_args_list]
            assert all(progress_values[i] <= progress_values[i+1] for i in range(len(progress_values)-1))
            assert progress_values[-1] == 100  # Should reach 100% at completion
    
    @pytest.mark.asyncio
    async def test_job_status_updates(self, dice_orchestrator):
        """Test job status updates during processing"""
        with patch.object(dice_orchestrator.prescan_algo, 'process_files', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_prescan_result()), \
             patch.object(dice_orchestrator.ai_layer_1, 'generate_transcript', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_draft_transcript()), \
             patch.object(dice_orchestrator.validator, 'validate_transcript', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_validation_report()), \
             patch.object(dice_orchestrator.ai_layer_2, 'generate_final_minutes', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_final_minutes()), \
             patch.object(dice_orchestrator, '_update_job_status', new_callable=AsyncMock) as mock_status:
            
            await dice_orchestrator.process_complete_pipeline()
            
            # Verify status progression
            status_calls = [call[0][0] for call in mock_status.call_args_list]
            
            # Should start with PROCESSING and end with COMPLETED
            assert DiceJobStatus.PROCESSING in status_calls
            assert DiceJobStatus.COMPLETED in status_calls[-1:]
    
    @pytest.mark.asyncio
    async def test_logging_and_metrics(self, dice_orchestrator):
        """Test comprehensive logging and metrics collection"""
        with patch.object(dice_orchestrator.prescan_algo, 'process_files', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_prescan_result()), \
             patch.object(dice_orchestrator.ai_layer_1, 'generate_transcript', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_draft_transcript()), \
             patch.object(dice_orchestrator.validator, 'validate_transcript', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_validation_report()), \
             patch.object(dice_orchestrator.ai_layer_2, 'generate_final_minutes', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_final_minutes()), \
             patch.object(dice_orchestrator, '_log_event', new_callable=AsyncMock) as mock_log:
            
            await dice_orchestrator.process_complete_pipeline()
            
            # Verify different types of logs were created
            log_levels = {call[0][0] for call in mock_log.call_args_list}
            log_steps = {call[0][1] for call in mock_log.call_args_list}
            
            assert "info" in log_levels
            assert "prescan" in log_steps
            assert "ai_layer_1" in log_steps
            assert "validation" in log_steps
            assert "ai_layer_2" in log_steps
            
            # Verify performance metrics are logged
            perf_logs = [call for call in mock_log.call_args_list if call[1].get("execution_time")]
            assert len(perf_logs) >= 4  # One for each stage
    
    @pytest.mark.asyncio
    async def test_concurrent_job_processing(self, mock_db_session):
        """Test handling of multiple concurrent DICE jobs"""
        job_ids = [uuid.uuid4() for _ in range(3)]
        orchestrators = []
        
        # Create multiple orchestrators
        for job_id in job_ids:
            sample_job = DiceJob(
                id=job_id,
                user_id=uuid.uuid4(),
                status=DiceJobStatus.PENDING,
                files_uploaded=[DICETestFixtures.create_sample_file_info()],
                created_at=datetime.utcnow()
            )
            
            with patch('app.services.dice_orchestrator.get_async_session') as mock_get_session:
                mock_get_session.return_value.__anext__.return_value = mock_db_session
                
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = sample_job
                mock_db_session.execute.return_value = mock_result
                
                orchestrator = DICEOrchestrator(job_id, mock_db_session)
                await orchestrator._load_job()
                orchestrators.append(orchestrator)
        
        # Mock algorithm responses for all orchestrators
        for orchestrator in orchestrators:
            with patch.object(orchestrator.prescan_algo, 'process_files', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_prescan_result()), \
                 patch.object(orchestrator.ai_layer_1, 'generate_transcript', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_draft_transcript()), \
                 patch.object(orchestrator.validator, 'validate_transcript', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_validation_report()), \
                 patch.object(orchestrator.ai_layer_2, 'generate_final_minutes', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_final_minutes()), \
                 patch.object(orchestrator, '_update_job_status', new_callable=AsyncMock), \
                 patch.object(orchestrator, '_log_event', new_callable=AsyncMock):
                pass
        
        # Process jobs concurrently
        tasks = [orchestrator.process_complete_pipeline() for orchestrator in orchestrators]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all jobs completed successfully
        assert len(results) == 3
        assert all(isinstance(result, FinalMinutes) for result in results)
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, dice_orchestrator):
        """Test that complete pipeline meets performance benchmarks"""
        import time
        
        with patch.object(dice_orchestrator.prescan_algo, 'process_files', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_prescan_result()), \
             patch.object(dice_orchestrator.ai_layer_1, 'generate_transcript', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_draft_transcript()), \
             patch.object(dice_orchestrator.validator, 'validate_transcript', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_validation_report()), \
             patch.object(dice_orchestrator.ai_layer_2, 'generate_final_minutes', new_callable=AsyncMock, return_value=DICETestFixtures.create_sample_final_minutes()), \
             patch.object(dice_orchestrator, '_update_job_status', new_callable=AsyncMock), \
             patch.object(dice_orchestrator, '_log_event', new_callable=AsyncMock):
            
            start_time = time.time()
            result = await dice_orchestrator.process_complete_pipeline()
            end_time = time.time()
            
            total_time = end_time - start_time
            
            # Complete pipeline should finish within reasonable time
            max_total_time = sum([
                DICETestConstants.MAX_PRESCAN_TIME,
                DICETestConstants.MAX_AI_LAYER1_TIME,
                DICETestConstants.MAX_VALIDATION_TIME,
                DICETestConstants.MAX_AI_LAYER2_TIME
            ])
            
            assert total_time < max_total_time
            assert isinstance(result, FinalMinutes)
    
    @pytest.mark.asyncio
    async def test_context_manager_usage(self, job_id, mock_db_session, sample_dice_job):
        """Test using orchestrator as async context manager"""
        with patch('app.services.dice_orchestrator.get_async_session') as mock_get_session:
            mock_get_session.return_value.__anext__.return_value = mock_db_session
            
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = sample_dice_job
            mock_db_session.execute.return_value = mock_result
            
            async with DICEOrchestrator(job_id) as orchestrator:
                assert orchestrator.job is not None
                assert orchestrator.job.id == job_id
            
            # Context manager should handle cleanup
            mock_db_session.close.assert_called_once()


@pytest.mark.integration
class TestDICEOrchestratorIntegration:
    """Integration tests for DICE Orchestrator with real components"""
    
    @pytest.mark.skipif(not os.environ.get('RUN_INTEGRATION_TESTS'),
                       reason="Integration tests require full environment setup")
    @pytest.mark.asyncio
    async def test_end_to_end_pipeline(self):
        """Test complete end-to-end pipeline with real components"""
        # This would test the full pipeline with real:
        # - Database connections
        # - OpenAI API calls
        # - S3 file operations
        # - Redis caching
        pass
    
    @pytest.mark.asyncio
    async def test_real_performance_benchmarks(self):
        """Test performance with real components and data"""
        # This would test actual performance with real files
        # and API calls to ensure SLA compliance
        pass
