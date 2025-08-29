"""
DICE™ AI Layer 2: Refine
Advanced AI refinement for final meeting minutes generation

Takes validated transcript and generates polished, professional meeting minutes
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re

# OpenAI
try:
    import openai
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from app.schemas.dice_schemas import (
    DraftTranscriptJSON, ValidationReportJSON, FinalMinutes,
    TranscriptSegment, FinalActionItem, FinalDecision
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AILayer2:
    """
    AI Layer 2: Refine
    
    Takes validated transcript and produces professional meeting minutes with:
    - Corrected and polished transcript
    - Structured action items with owners and deadlines
    - Clear decisions and rationale
    - Executive summary
    - Professional formatting
    """
    
    def __init__(self):
        """Initialize AI Layer 2 with OpenAI client"""
        self.openai_client = None
        if HAS_OPENAI and hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Professional meeting templates
        self.templates = {
            "formal": {
                "tone": "formal and professional",
                "structure": "traditional corporate meeting minutes",
                "language": "business-appropriate with complete sentences"
            },
            "informal": {
                "tone": "conversational but clear",
                "structure": "modern meeting summary format", 
                "language": "clear and accessible"
            },
            "technical": {
                "tone": "precise and detailed",
                "structure": "technical documentation style",
                "language": "specific terminology preserved"
            }
        }
    
    async def refine_transcript(
        self, 
        draft_transcript: DraftTranscriptJSON, 
        validation_report: ValidationReportJSON,
        template_style: str = "formal"
    ) -> FinalMinutes:
        """
        Refine draft transcript into professional meeting minutes
        
        Args:
            draft_transcript: Validated draft transcript
            validation_report: Validation issues and suggestions
            template_style: Style template to use
            
        Returns:
            FinalMinutes with polished content
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not available")
        
        # Apply validation corrections to transcript
        corrected_transcript = await self._apply_validation_corrections(
            draft_transcript, validation_report
        )
        
        # Generate meeting metadata
        meeting_metadata = await self._extract_meeting_metadata(corrected_transcript)
        
        # Generate executive summary
        executive_summary = await self._generate_executive_summary(corrected_transcript)
        
        # Extract and structure decisions
        decisions = await self._extract_decisions(corrected_transcript)
        
        # Extract and structure action items
        action_items = await self._extract_action_items(corrected_transcript)
        
        # Extract key topics
        key_topics = await self._extract_key_topics(corrected_transcript)
        
        # Polish the transcript segments
        polished_segments = await self._polish_transcript_segments(
            corrected_transcript.segments, template_style
        )
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            corrected_transcript, validation_report, len(decisions), len(action_items)
        )
        
        return FinalMinutes(
            title=meeting_metadata.get("title", "Meeting Minutes"),
            meeting_date=meeting_metadata.get("date", datetime.utcnow()),
            participants=meeting_metadata.get("participants", []),
            meeting_type=meeting_metadata.get("type"),
            location=meeting_metadata.get("location"),
            executive_summary=executive_summary,
            key_topics_discussed=key_topics,
            decisions=decisions,
            action_items=action_items,
            full_transcript=polished_segments,
            quality_score=quality_score,
            ai_model_used="gpt-4o"
        )
    
    async def _apply_validation_corrections(
        self, 
        draft_transcript: DraftTranscriptJSON, 
        validation_report: ValidationReportJSON
    ) -> DraftTranscriptJSON:
        """Apply validation corrections to the transcript"""
        
        corrected_segments = []
        
        for segment in draft_transcript.segments:
            corrected_text = segment.text
            
            # Apply high-confidence corrections
            segment_issues = [
                issue for issue in validation_report.issues 
                if issue.segment_id == segment.segment_id and issue.confidence > 0.8
            ]
            
            for issue in segment_issues:
                if issue.type in ["name_spell", "term_suggestion"] and issue.sa_context_applied:
                    # Apply SA-specific corrections with high confidence
                    corrected_text = corrected_text.replace(
                        issue.original_text, issue.suggested_text
                    )
                elif issue.type == "grammar" and issue.confidence > 0.9:
                    # Apply high-confidence grammar corrections
                    corrected_text = corrected_text.replace(
                        issue.original_text, issue.suggested_text
                    )
            
            # Create corrected segment
            corrected_segment = TranscriptSegment(
                segment_id=segment.segment_id,
                speaker=segment.speaker,
                start_time=segment.start_time,
                end_time=segment.end_time,
                text=corrected_text,
                confidence=min(1.0, segment.confidence + 0.1)  # Boost confidence slightly
            )
            corrected_segments.append(corrected_segment)
        
        # Update transcript with corrections
        corrected_transcript = DraftTranscriptJSON(
            language=draft_transcript.language,
            segments=corrected_segments,
            summary=draft_transcript.summary,
            action_items=draft_transcript.action_items,
            key_topics=draft_transcript.key_topics,
            model_used=draft_transcript.model_used,
            ai_provider=draft_transcript.ai_provider,
            confidence=draft_transcript.confidence
        )
        
        return corrected_transcript
    
    async def _extract_meeting_metadata(self, transcript: DraftTranscriptJSON) -> Dict[str, Any]:
        """Extract meeting metadata from transcript"""
        
        # Combine transcript text
        full_text = " ".join(segment.text for segment in transcript.segments[:10])  # First 10 segments
        
        try:
            prompt = f"""
Extract meeting metadata from this transcript excerpt. Return as JSON:

TRANSCRIPT EXCERPT:
{full_text[:1500]}...

Extract:
{{
    "title": "Meeting title or topic",
    "participants": ["Name 1", "Name 2", ...],
    "meeting_type": "type of meeting",
    "location": "location if mentioned",
    "estimated_date": "YYYY-MM-DD if determinable"
}}

Only include information explicitly mentioned or clearly inferable.
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting meeting metadata. Be conservative and only extract clearly stated information."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            metadata = json.loads(response.choices[0].message.content)
            
            # Parse date if provided
            if metadata.get("estimated_date"):
                try:
                    metadata["date"] = datetime.strptime(metadata["estimated_date"], "%Y-%m-%d")
                except ValueError:
                    metadata["date"] = datetime.utcnow()
            else:
                metadata["date"] = datetime.utcnow()
            
            # Extract unique speakers as participants if not found
            if not metadata.get("participants"):
                speakers = list(set(segment.speaker for segment in transcript.segments))
                metadata["participants"] = [s for s in speakers if s != "Unknown"]
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting meeting metadata: {e}")
            return {
                "title": "Meeting Minutes",
                "date": datetime.utcnow(),
                "participants": list(set(segment.speaker for segment in transcript.segments)),
                "meeting_type": None,
                "location": None
            }
    
    async def _generate_executive_summary(self, transcript: DraftTranscriptJSON) -> str:
        """Generate executive summary of the meeting"""
        
        # Combine transcript text
        full_text = " ".join(segment.text for segment in transcript.segments)
        
        try:
            prompt = f"""
Generate a professional executive summary for this meeting transcript.
The summary should be 2-3 paragraphs, highlighting key outcomes, decisions, and next steps.

TRANSCRIPT:
{full_text[:4000]}...

Write a concise, professional executive summary suitable for senior stakeholders.
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert executive assistant who writes clear, professional meeting summaries for senior leadership."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return "Meeting summary could not be generated."
    
    async def _extract_decisions(self, transcript: DraftTranscriptJSON) -> List[FinalDecision]:
        """Extract and structure decisions from transcript"""
        
        full_text = " ".join(segment.text for segment in transcript.segments)
        
        try:
            prompt = f"""
Extract all decisions made during this meeting. Return as JSON array:

TRANSCRIPT:
{full_text[:4000]}...

Format:
[
    {{
        "decision": "Clear statement of what was decided",
        "rationale": "Why this decision was made (if mentioned)",
        "stakeholders": ["Who was involved in the decision"],
        "implementation_date": "When to implement (if mentioned)"
    }}
]

Only include actual decisions, not just discussions.
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at identifying and structuring meeting decisions. Be precise and only extract clear decisions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            decisions_data = json.loads(response.choices[0].message.content)
            
            decisions = []
            for decision_data in decisions_data:
                decision = FinalDecision(
                    decision=decision_data.get("decision", ""),
                    rationale=decision_data.get("rationale"),
                    stakeholders=decision_data.get("stakeholders", []),
                    implementation_date=decision_data.get("implementation_date")
                )
                decisions.append(decision)
            
            return decisions
            
        except Exception as e:
            logger.error(f"Error extracting decisions: {e}")
            return []
    
    async def _extract_action_items(self, transcript: DraftTranscriptJSON) -> List[FinalActionItem]:
        """Extract and structure action items from transcript"""
        
        full_text = " ".join(segment.text for segment in transcript.segments)
        
        try:
            prompt = f"""
Extract all action items from this meeting transcript. Return as JSON array:

TRANSCRIPT:
{full_text[:4000]}...

Format:
[
    {{
        "item": "Specific action to be taken",
        "owner": "Person responsible",
        "due_date": "Deadline if mentioned",
        "priority": "high/medium/low",
        "category": "Category if applicable"
    }}
]

Only include clear action items with specific tasks.
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at identifying action items from meetings. Extract specific, actionable tasks with clear ownership."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            actions_data = json.loads(response.choices[0].message.content)
            
            action_items = []
            for action_data in actions_data:
                action_item = FinalActionItem(
                    item=action_data.get("item", ""),
                    owner=action_data.get("owner", "TBD"),
                    due_date=action_data.get("due_date"),
                    priority=action_data.get("priority", "medium"),
                    category=action_data.get("category")
                )
                action_items.append(action_item)
            
            return action_items
            
        except Exception as e:
            logger.error(f"Error extracting action items: {e}")
            return []
    
    async def _extract_key_topics(self, transcript: DraftTranscriptJSON) -> List[str]:
        """Extract key topics discussed in the meeting"""
        
        full_text = " ".join(segment.text for segment in transcript.segments)
        
        try:
            prompt = f"""
Identify the main topics discussed in this meeting. Return as JSON array of strings.

TRANSCRIPT:
{full_text[:3000]}...

Return the 5-10 most important topics as:
["Topic 1", "Topic 2", ...]

Focus on substantial discussion topics, not minor points.
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at identifying key discussion topics from meeting transcripts."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=300
            )
            
            topics = json.loads(response.choices[0].message.content)
            return topics if isinstance(topics, list) else []
            
        except Exception as e:
            logger.error(f"Error extracting key topics: {e}")
            return []
    
    async def _polish_transcript_segments(
        self, 
        segments: List[TranscriptSegment], 
        template_style: str
    ) -> List[TranscriptSegment]:
        """Polish transcript segments for final presentation"""
        
        template = self.templates.get(template_style, self.templates["formal"])
        polished_segments = []
        
        # Process segments in batches for efficiency
        batch_size = 5
        for i in range(0, len(segments), batch_size):
            batch = segments[i:i + batch_size]
            
            try:
                polished_batch = await self._polish_segment_batch(batch, template)
                polished_segments.extend(polished_batch)
            except Exception as e:
                logger.error(f"Error polishing segment batch: {e}")
                # Fall back to original segments
                polished_segments.extend(batch)
        
        return polished_segments
    
    async def _polish_segment_batch(
        self, 
        segments: List[TranscriptSegment], 
        template: Dict[str, str]
    ) -> List[TranscriptSegment]:
        """Polish a batch of segments"""
        
        # Combine segments for context
        batch_text = ""
        for i, seg in enumerate(segments):
            batch_text += f"[{seg.speaker}] {seg.text}\n"
        
        try:
            prompt = f"""
Polish this meeting transcript excerpt for professional presentation.
Use {template['tone']} tone and {template['language']} style.

ORIGINAL:
{batch_text}

Requirements:
- Maintain speaker labels and structure
- Remove filler words and false starts
- Correct grammar while preserving meaning
- Keep technical terms accurate
- Maintain natural flow

Return the polished version in the same format.
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert transcript editor. Polish text for {template['structure']} while maintaining accuracy and natural flow."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            polished_text = response.choices[0].message.content
            
            # Parse back to segments
            return self._parse_polished_segments(polished_text, segments)
            
        except Exception as e:
            logger.error(f"Error in segment polishing: {e}")
            return segments
    
    def _parse_polished_segments(
        self, 
        polished_text: str, 
        original_segments: List[TranscriptSegment]
    ) -> List[TranscriptSegment]:
        """Parse polished text back to segments"""
        
        lines = polished_text.strip().split('\n')
        polished_segments = []
        
        for i, line in enumerate(lines):
            if line.strip() and '[' in line and ']' in line:
                try:
                    # Extract speaker and text
                    speaker_end = line.find(']')
                    speaker = line[1:speaker_end]
                    text = line[speaker_end + 1:].strip()
                    
                    # Use original timing if available
                    if i < len(original_segments):
                        original = original_segments[i]
                        polished_segment = TranscriptSegment(
                            segment_id=original.segment_id,
                            speaker=speaker,
                            start_time=original.start_time,
                            end_time=original.end_time,
                            text=text,
                            confidence=min(1.0, original.confidence + 0.2)  # Boost confidence
                        )
                        polished_segments.append(polished_segment)
                        
                except Exception:
                    continue
        
        # Return original if parsing failed
        if len(polished_segments) < len(original_segments) * 0.8:
            return original_segments
        
        return polished_segments
    
    def _calculate_quality_score(
        self, 
        transcript: DraftTranscriptJSON, 
        validation_report: ValidationReportJSON,
        decisions_count: int,
        action_items_count: int
    ) -> float:
        """Calculate overall quality score for the final minutes"""
        
        # Base score from validation
        base_score = validation_report.scores.get("overall", 0.7)
        
        # Bonus for structured content
        content_bonus = 0.0
        if decisions_count > 0:
            content_bonus += 0.1
        if action_items_count > 0:
            content_bonus += 0.1
        
        # Bonus for transcript completeness
        if len(transcript.segments) > 5:
            content_bonus += 0.05
        
        # Penalty for remaining issues
        critical_issues = len([i for i in validation_report.issues if i.severity == "critical"])
        if critical_issues > 0:
            content_bonus -= 0.2
        
        final_score = min(1.0, base_score + content_bonus)
        return round(final_score, 3)




