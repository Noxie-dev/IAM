"""
DICE™ Algorithm 2: Validator
Advanced validation engine with South African context awareness

Performs grammar checking, name validation, coherence analysis, and SA-specific corrections
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional, Set
import json
from pathlib import Path

# Grammar and language processing
try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False

try:
    import language_tool_python
    HAS_LANGUAGE_TOOL = True
except ImportError:
    HAS_LANGUAGE_TOOL = False

# Text processing
import difflib
from collections import Counter

from app.schemas.dice_schemas import (
    DraftTranscriptJSON, ValidationReportJSON, ValidationIssue, TranscriptSegment
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SANameMatcher:
    """South African name and term matcher with fuzzy matching capabilities"""
    
    def __init__(self):
        """Initialize with South African names and terms database"""
        # Common South African names (this would be expanded from a proper database)
        self.sa_names = {
            # Afrikaans names
            "Johannes", "Jacobus", "Andries", "Pieter", "Francois", "Gideon", "Hennie",
            "Marié", "Annemarie", "Elmarie", "Hannetjie", "Marietjie", "Sannie",
            "Kobus", "Fanie", "Boet", "Bennie", "Christo", "Danie", "Deon", "Dirk",
            
            # African names
            "Thabo", "Mandla", "Sipho", "Nomsa", "Thandiwe", "Kagiso", "Lebohang",
            "Ntombi", "Sizani", "Zodwa", "Bongani", "Tebogo", "Mpho", "Kgaogelo",
            "Lindiwe", "Nokuthula", "Precious", "Beauty", "Given", "Prince",
            
            # English South African names
            "Charlize", "Candice", "Ryk", "Schalk", "Jannie", "Hansie", "Eben",
            
            # Surnames
            "Van der Merwe", "Botha", "Pretorius", "Van Wyk", "Joubert", "Nel",
            "Smith", "Williams", "Brown", "Jones", "Miller", "Davis",
            "Mthembu", "Nkomo", "Dlamini", "Khumalo", "Mabaso", "Ndlovu",
            "Zulu", "Xhosa", "Tshabalala", "Mahlangu", "Mokoena", "Molefe"
        }
        
        # SA-specific terms and organizations
        self.sa_terms = {
            # Government and organizations
            "SARS", "SARB", "SADC", "AU", "GNU", "ANC", "DA", "EFF", "IFP",
            "Department of Trade and Industry", "DTI", "DTIC", "CIPC",
            "National Treasury", "GEPF", "UIF", "CCMA", "SETA",
            
            # Business terms
            "BEE", "BBBEE", "JSE", "Johannesburg Stock Exchange",
            "Pty Ltd", "CC", "Close Corporation", "NPO", "NPC",
            "VAT", "PAYE", "SDL", "UIF", "WCA", "Workmen's Compensation",
            
            # Geographic terms
            "Gauteng", "KwaZulu-Natal", "Western Cape", "Eastern Cape",
            "Free State", "Limpopo", "Mpumalanga", "North West", "Northern Cape",
            "Johannesburg", "Cape Town", "Durban", "Pretoria", "Tshwane",
            "Bloemfontein", "Port Elizabeth", "Gqeberha", "Kimberley",
            
            # Cultural and linguistic
            "Ubuntu", "Braai", "Biltong", "Rooibos", "Boerewors", "Potjiekos",
            "Afrikaans", "isiZulu", "isiXhosa", "Sepedi", "Setswana", "Sesotho",
            "Xitsonga", "siSwati", "Tshivenda", "isiNdebele",
            
            # Currency and measurements
            "Rand", "ZAR", "cents", "rand value"
        }
        
        # Convert to lowercase for matching
        self.sa_names_lower = {name.lower(): name for name in self.sa_names}
        self.sa_terms_lower = {term.lower(): term for term in self.sa_terms}
        
        # Common misspellings and corrections
        self.common_corrections = {
            "johannesberg": "Johannesburg",
            "capetown": "Cape Town",
            "kwa-zulu natal": "KwaZulu-Natal",
            "kwazulu natal": "KwaZulu-Natal",
            "bee": "BEE",
            "vat": "VAT",
            "sars": "SARS"
        }
    
    def find_best_match(self, text: str) -> Optional[Dict[str, Any]]:
        """Find best matching SA term with confidence score"""
        text_lower = text.lower().strip()
        
        # Exact match
        if text_lower in self.sa_names_lower:
            return {
                "original": text,
                "correction": self.sa_names_lower[text_lower],
                "confidence": 1.0,
                "type": "name"
            }
        
        if text_lower in self.sa_terms_lower:
            return {
                "original": text,
                "correction": self.sa_terms_lower[text_lower],
                "confidence": 1.0,
                "type": "term"
            }
        
        # Check common corrections
        if text_lower in self.common_corrections:
            return {
                "original": text,
                "correction": self.common_corrections[text_lower],
                "confidence": 0.95,
                "type": "correction"
            }
        
        # Fuzzy matching
        best_match = None
        best_score = 0.0
        
        # Check names
        for name_lower, name_correct in self.sa_names_lower.items():
            ratio = difflib.SequenceMatcher(None, text_lower, name_lower).ratio()
            if ratio > 0.85 and ratio > best_score:
                best_score = ratio
                best_match = {
                    "original": text,
                    "correction": name_correct,
                    "confidence": ratio,
                    "type": "name_fuzzy"
                }
        
        # Check terms
        for term_lower, term_correct in self.sa_terms_lower.items():
            ratio = difflib.SequenceMatcher(None, text_lower, term_lower).ratio()
            if ratio > 0.85 and ratio > best_score:
                best_score = ratio
                best_match = {
                    "original": text,
                    "correction": term_correct,
                    "confidence": ratio,
                    "type": "term_fuzzy"
                }
        
        return best_match


class ValidationAlgorithm:
    """
    Algorithm 2: Validator
    
    Advanced validation engine that checks:
    - Grammar and coherence
    - South African names and terms
    - Meeting-specific context
    - Consistency across segments
    """
    
    def __init__(self):
        """Initialize the validation algorithm"""
        # Initialize language tools
        self.nlp = None
        if HAS_SPACY:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("SpaCy English model not found")
        
        self.grammar_tool = None
        if HAS_LANGUAGE_TOOL:
            try:
                self.grammar_tool = language_tool_python.LanguageTool('en-US')
            except Exception as e:
                logger.warning(f"Could not initialize LanguageTool: {e}")
        
        # Initialize SA matcher
        self.sa_matcher = SANameMatcher()
        
        # Meeting-specific patterns
        self.meeting_patterns = {
            "action_items": [
                r"\b(action|task|todo|follow[- ]?up|assign|responsible)\b",
                r"\b(due|deadline|by|before|next week|next month)\b"
            ],
            "decisions": [
                r"\b(decide|decision|agreed|consensus|vote|approve)\b",
                r"\b(will|shall|must|should|going to)\b"
            ],
            "speakers": [
                r"\b(speaker|chair|chairperson|presenter|facilitator)\b",
                r"\b(said|mentioned|stated|asked|replied|responded)\b"
            ]
        }
    
    async def validate_transcript(self, draft_transcript: DraftTranscriptJSON) -> ValidationReportJSON:
        """
        Validate draft transcript and generate comprehensive report
        
        Args:
            draft_transcript: Draft transcript to validate
            
        Returns:
            ValidationReportJSON with issues and scores
        """
        if not draft_transcript.segments:
            return ValidationReportJSON(
                issues=[],
                scores={"grammar": 0.0, "sa_names": 0.0, "coherence": 0.0, "overall": 0.0},
                total_segments_analyzed=0
            )
        
        issues = []
        
        # Validate each segment
        for i, segment in enumerate(draft_transcript.segments):
            segment_issues = await self._validate_segment(segment, i, draft_transcript.segments)
            issues.extend(segment_issues)
        
        # Calculate quality scores
        scores = self._calculate_quality_scores(issues, draft_transcript.segments)
        
        # Determine if human review is required
        requires_hitl = self._requires_human_review(scores, issues)
        
        # Generate statistics
        issues_by_severity = Counter(issue.severity for issue in issues)
        
        return ValidationReportJSON(
            issues=issues,
            scores=scores,
            total_segments_analyzed=len(draft_transcript.segments),
            total_words_analyzed=draft_transcript.word_count,
            issues_by_severity=dict(issues_by_severity),
            requires_human_review=requires_hitl,
            auto_approval_eligible=not requires_hitl and scores["overall"] >= 0.9
        )
    
    async def _validate_segment(
        self, 
        segment: TranscriptSegment, 
        index: int, 
        all_segments: List[TranscriptSegment]
    ) -> List[ValidationIssue]:
        """Validate individual transcript segment"""
        issues = []
        
        # Grammar and language validation
        issues.extend(await self._check_grammar(segment, index))
        
        # South African names and terms
        issues.extend(await self._check_sa_context(segment, index))
        
        # Coherence with surrounding segments
        issues.extend(await self._check_coherence(segment, index, all_segments))
        
        # Meeting-specific validation
        issues.extend(await self._check_meeting_context(segment, index))
        
        return issues
    
    async def _check_grammar(self, segment: TranscriptSegment, index: int) -> List[ValidationIssue]:
        """Check grammar and language issues"""
        issues = []
        
        if not segment.text.strip():
            return issues
        
        try:
            # Use LanguageTool for grammar checking
            if self.grammar_tool:
                matches = self.grammar_tool.check(segment.text)
                
                for match in matches:
                    # Filter out minor issues for transcripts
                    if self._is_significant_grammar_issue(match):
                        severity = self._determine_grammar_severity(match)
                        
                        issue = ValidationIssue(
                            type="grammar",
                            severity=severity,
                            segment_id=segment.segment_id,
                            segment_index=index,
                            original_text=segment.text[match.offset:match.offset + match.errorLength],
                            suggested_text=match.replacements[0] if match.replacements else "",
                            confidence=0.8,
                            notes=match.message
                        )
                        issues.append(issue)
            
            # Additional custom grammar checks for transcripts
            issues.extend(self._check_transcript_specific_grammar(segment, index))
            
        except Exception as e:
            logger.error(f"Error in grammar checking: {e}")
        
        return issues
    
    def _is_significant_grammar_issue(self, match) -> bool:
        """Filter grammar issues for transcript context"""
        # Skip minor punctuation issues common in transcripts
        minor_rules = [
            "WHITESPACE_RULE",
            "COMMA_PARENTHESIS_WHITESPACE",
            "SENTENCE_WHITESPACE"
        ]
        
        return match.ruleId not in minor_rules
    
    def _determine_grammar_severity(self, match) -> str:
        """Determine severity of grammar issue"""
        high_severity_rules = [
            "MORFOLOGIK_RULE_EN_US",  # Spelling
            "AGREEMENT_ERRORS",
            "VERB_FORM_ERRORS"
        ]
        
        if any(rule in match.ruleId for rule in high_severity_rules):
            return "high"
        elif match.ruleIssueType == "misspelling":
            return "medium"
        else:
            return "low"
    
    def _check_transcript_specific_grammar(
        self, 
        segment: TranscriptSegment, 
        index: int
    ) -> List[ValidationIssue]:
        """Check transcript-specific grammar patterns"""
        issues = []
        text = segment.text
        
        # Check for incomplete sentences (common in transcripts)
        if len(text.split()) > 3 and not text.strip().endswith(('.', '!', '?')):
            # Only flag if it doesn't look like an interruption
            if not re.search(r'\b(um|uh|er|ah|well|so)\b', text.lower()):
                issue = ValidationIssue(
                    type="grammar",
                    severity="low",
                    segment_id=segment.segment_id,
                    segment_index=index,
                    original_text=text,
                    suggested_text=text + ".",
                    confidence=0.6,
                    notes="Incomplete sentence - consider adding punctuation"
                )
                issues.append(issue)
        
        # Check for excessive filler words
        filler_count = len(re.findall(r'\b(um|uh|er|ah|like|you know)\b', text.lower()))
        word_count = len(text.split())
        
        if word_count > 5 and filler_count / word_count > 0.3:
            issue = ValidationIssue(
                type="coherence",
                severity="medium",
                segment_id=segment.segment_id,
                segment_index=index,
                original_text=text,
                suggested_text="[Consider reducing filler words]",
                confidence=0.8,
                notes="High concentration of filler words"
            )
            issues.append(issue)
        
        return issues
    
    async def _check_sa_context(self, segment: TranscriptSegment, index: int) -> List[ValidationIssue]:
        """Check South African names, terms, and context"""
        issues = []
        
        if not self.nlp:
            return issues
        
        try:
            doc = self.nlp(segment.text)
            
            # Check proper nouns for SA names/terms
            for token in doc:
                if token.pos_ == "PROPN" and len(token.text) > 1:
                    match = self.sa_matcher.find_best_match(token.text)
                    
                    if match and match["confidence"] < 0.98:
                        # Found a potential SA correction
                        severity = "high" if match["confidence"] < 0.9 else "medium"
                        
                        issue = ValidationIssue(
                            type="name_spell",
                            severity=severity,
                            segment_id=segment.segment_id,
                            segment_index=index,
                            original_text=token.text,
                            suggested_text=match["correction"],
                            confidence=match["confidence"],
                            sa_context_applied=True,
                            sa_term_match=match["correction"],
                            notes=f"SA {match['type']} correction suggested"
                        )
                        issues.append(issue)
            
            # Check for SA-specific term patterns
            issues.extend(self._check_sa_term_patterns(segment, index))
            
        except Exception as e:
            logger.error(f"Error in SA context checking: {e}")
        
        return issues
    
    def _check_sa_term_patterns(self, segment: TranscriptSegment, index: int) -> List[ValidationIssue]:
        """Check for SA-specific term patterns and common mistakes"""
        issues = []
        text = segment.text.lower()
        
        # Common SA term corrections
        sa_corrections = {
            r'\bvat\b': "VAT",
            r'\bsars\b': "SARS",
            r'\bbee\b': "BEE",
            r'\bjse\b': "JSE",
            r'\bcape town\b': "Cape Town",
            r'\bjohannes?burg\b': "Johannesburg",
            r'\bkwa-?zulu-?natal\b': "KwaZulu-Natal"
        }
        
        for pattern, correction in sa_corrections.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                if match.group() != correction.lower():
                    issue = ValidationIssue(
                        type="term_suggestion",
                        severity="medium",
                        segment_id=segment.segment_id,
                        segment_index=index,
                        original_text=match.group(),
                        suggested_text=correction,
                        confidence=0.9,
                        sa_context_applied=True,
                        notes="SA term standardization"
                    )
                    issues.append(issue)
        
        return issues
    
    async def _check_coherence(
        self, 
        segment: TranscriptSegment, 
        index: int, 
        all_segments: List[TranscriptSegment]
    ) -> List[ValidationIssue]:
        """Check coherence with surrounding segments"""
        issues = []
        
        # Check speaker consistency
        if index > 0:
            prev_segment = all_segments[index - 1]
            
            # Check for sudden speaker changes without context
            if (segment.speaker != prev_segment.speaker and 
                not self._has_speaker_transition_context(prev_segment.text, segment.text)):
                
                # Only flag if segments are very close in time
                time_gap = segment.start_time - prev_segment.end_time
                if time_gap < 1.0:  # Less than 1 second gap
                    issue = ValidationIssue(
                        type="coherence",
                        severity="low",
                        segment_id=segment.segment_id,
                        segment_index=index,
                        original_text=segment.text,
                        suggested_text="[Verify speaker change]",
                        confidence=0.6,
                        notes="Abrupt speaker change detected"
                    )
                    issues.append(issue)
        
        # Check for topic continuity
        if index > 0 and index < len(all_segments) - 1:
            issues.extend(self._check_topic_continuity(segment, index, all_segments))
        
        return issues
    
    def _has_speaker_transition_context(self, prev_text: str, current_text: str) -> bool:
        """Check if there's natural speaker transition context"""
        transition_words = [
            "thank you", "thanks", "okay", "right", "yes", "no", 
            "question", "answer", "comment", "next", "moving on"
        ]
        
        combined_text = (prev_text + " " + current_text).lower()
        return any(word in combined_text for word in transition_words)
    
    def _check_topic_continuity(
        self, 
        segment: TranscriptSegment, 
        index: int, 
        all_segments: List[TranscriptSegment]
    ) -> List[ValidationIssue]:
        """Check topic continuity between segments"""
        issues = []
        
        # Simple topic continuity check based on keyword overlap
        prev_segment = all_segments[index - 1]
        next_segment = all_segments[index + 1]
        
        # Extract keywords
        current_keywords = set(re.findall(r'\b\w{4,}\b', segment.text.lower()))
        prev_keywords = set(re.findall(r'\b\w{4,}\b', prev_segment.text.lower()))
        next_keywords = set(re.findall(r'\b\w{4,}\b', next_segment.text.lower()))
        
        # Check overlap
        prev_overlap = len(current_keywords & prev_keywords) / max(len(current_keywords), 1)
        next_overlap = len(current_keywords & next_keywords) / max(len(current_keywords), 1)
        
        # Flag if very low overlap (possible topic jump)
        if prev_overlap < 0.1 and next_overlap < 0.1 and len(current_keywords) > 3:
            issue = ValidationIssue(
                type="coherence",
                severity="low",
                segment_id=segment.segment_id,
                segment_index=index,
                original_text=segment.text,
                suggested_text="[Review topic continuity]",
                confidence=0.5,
                notes="Possible topic discontinuity"
            )
            issues.append(issue)
        
        return issues
    
    async def _check_meeting_context(self, segment: TranscriptSegment, index: int) -> List[ValidationIssue]:
        """Check meeting-specific context and terminology"""
        issues = []
        
        text = segment.text.lower()
        
        # Check for incomplete action items
        if re.search(r'\b(action|task|todo|follow[- ]?up)\b', text):
            # Should have owner or deadline mentioned
            if not re.search(r'\b(who|by|before|due|assign|responsible|will|shall)\b', text):
                issue = ValidationIssue(
                    type="context_error",
                    severity="medium",
                    segment_id=segment.segment_id,
                    segment_index=index,
                    original_text=segment.text,
                    suggested_text="[Specify action owner or deadline]",
                    confidence=0.7,
                    notes="Action item missing owner or deadline"
                )
                issues.append(issue)
        
        # Check for unclear references
        pronouns = re.findall(r'\b(this|that|it|they|them|he|she)\b', text)
        if len(pronouns) > 2 and len(segment.text.split()) < 15:
            issue = ValidationIssue(
                type="coherence",
                severity="low",
                segment_id=segment.segment_id,
                segment_index=index,
                original_text=segment.text,
                suggested_text="[Clarify references]",
                confidence=0.6,
                notes="Multiple unclear references in short segment"
            )
            issues.append(issue)
        
        return issues
    
    def _calculate_quality_scores(
        self, 
        issues: List[ValidationIssue], 
        segments: List[TranscriptSegment]
    ) -> Dict[str, float]:
        """Calculate quality scores based on issues found"""
        
        if not segments:
            return {"grammar": 0.0, "sa_names": 0.0, "coherence": 0.0, "overall": 0.0}
        
        # Count issues by type and severity
        grammar_issues = [i for i in issues if i.type == "grammar"]
        sa_issues = [i for i in issues if i.type in ["name_spell", "term_suggestion"]]
        coherence_issues = [i for i in issues if i.type in ["coherence", "context_error"]]
        
        # Calculate scores (1.0 = perfect, 0.0 = many issues)
        total_segments = len(segments)
        
        # Grammar score
        grammar_penalty = sum(
            {"low": 0.05, "medium": 0.15, "high": 0.3, "critical": 0.5}.get(issue.severity, 0.1)
            for issue in grammar_issues
        )
        grammar_score = max(0.0, 1.0 - (grammar_penalty / total_segments))
        
        # SA names score
        sa_penalty = sum(
            {"low": 0.1, "medium": 0.2, "high": 0.4, "critical": 0.6}.get(issue.severity, 0.15)
            for issue in sa_issues
        )
        sa_score = max(0.0, 1.0 - (sa_penalty / total_segments))
        
        # Coherence score
        coherence_penalty = sum(
            {"low": 0.05, "medium": 0.1, "high": 0.2, "critical": 0.4}.get(issue.severity, 0.1)
            for issue in coherence_issues
        )
        coherence_score = max(0.0, 1.0 - (coherence_penalty / total_segments))
        
        # Overall score (weighted average)
        overall_score = (grammar_score * 0.3 + sa_score * 0.4 + coherence_score * 0.3)
        
        return {
            "grammar": round(grammar_score, 3),
            "sa_names": round(sa_score, 3),
            "coherence": round(coherence_score, 3),
            "overall": round(overall_score, 3)
        }
    
    def _requires_human_review(self, scores: Dict[str, float], issues: List[ValidationIssue]) -> bool:
        """Determine if human review is required"""
        
        # Always require review if overall score is low
        if scores["overall"] < 0.75:
            return True
        
        # Require review for critical issues
        critical_issues = [i for i in issues if i.severity == "critical"]
        if critical_issues:
            return True
        
        # Require review for many high severity issues
        high_issues = [i for i in issues if i.severity == "high"]
        if len(high_issues) > 3:
            return True
        
        # Require review for SA-specific issues with low confidence
        sa_issues = [i for i in issues if i.sa_context_applied and i.confidence < 0.9]
        if len(sa_issues) > 2:
            return True
        
        return False

