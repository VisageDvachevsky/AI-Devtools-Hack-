"""
Feedback Loop System
Collects feedback on candidate evaluations and continuously improves scoring models
"""
import json
import statistics
import time
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class FeedbackType(str, Enum):
    SCORING_ACCURACY = "scoring_accuracy"
    HIRE_OUTCOME = "hire_outcome"
    INTERVIEW_PERFORMANCE = "interview_performance"
    MODEL_SUGGESTION = "model_suggestion"


class HireOutcome(str, Enum):
    HIRED = "hired"
    OFFER_REJECTED = "offer_rejected"
    REJECTED_BY_COMPANY = "rejected_by_company"
    WITHDREW = "withdrew"
    IN_PROCESS = "in_process"


class FeedbackEntry(BaseModel):
    feedback_id: str
    candidate_id: str
    feedback_type: FeedbackType
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    # Candidate data at time of evaluation
    original_score: int
    original_decision: str  # "go", "hold", "no"

    # Actual outcome
    actual_outcome: Optional[HireOutcome] = None
    interview_score: Optional[float] = None  # 1-5 scale
    hire_decision_date: Optional[str] = None

    # Feedback details
    was_score_accurate: Optional[bool] = None
    suggested_score: Optional[int] = None
    notes: str = ""

    # Submitter info
    submitted_by: str = "system"
    role: str = ""


class ModelAdjustment(BaseModel):
    adjustment_id: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    reason: str
    parameter_changes: Dict[str, any]
    expected_impact: str
    applied: bool = False


class FeedbackAnalytics(BaseModel):
    total_feedback_entries: int
    feedback_by_type: Dict[str, int]

    # Accuracy metrics
    scoring_accuracy_rate: float = Field(ge=0.0, le=1.0)
    false_positive_rate: float = Field(ge=0.0, le=1.0)
    false_negative_rate: float = Field(ge=0.0, le=1.0)

    # Prediction metrics
    hire_prediction_accuracy: float = Field(ge=0.0, le=1.0)
    avg_score_deviation: float

    # Recommendations
    recommended_adjustments: List[str]


class FeedbackLoopSystem:
    """
    Feedback loop system for continuous improvement
    """

    def __init__(self):
        self.feedback_entries: List[FeedbackEntry] = []
        self.model_adjustments: List[ModelAdjustment] = []

        # Thresholds for scoring
        self.score_thresholds = {
            "go": 70,
            "hold": 50,
            "no": 0
        }

    def submit_feedback(
        self,
        candidate_id: str,
        original_score: int,
        original_decision: str,
        feedback_type: FeedbackType,
        actual_outcome: Optional[HireOutcome] = None,
        interview_score: Optional[float] = None,
        suggested_score: Optional[int] = None,
        notes: str = "",
        submitted_by: str = "system",
        role: str = ""
    ) -> str:
        """
        Submit feedback on a candidate evaluation

        Args:
            candidate_id: Candidate identifier
            original_score: Score given by system
            original_decision: Original decision ("go"/"hold"/"no")
            feedback_type: Type of feedback
            actual_outcome: Actual hiring outcome
            interview_score: Interview performance (1-5)
            suggested_score: What score should have been given
            notes: Additional notes
            submitted_by: Who submitted feedback
            role: Role candidate was evaluated for

        Returns:
            Feedback ID
        """

        # Generate feedback ID
        feedback_id = f"fb_{int(time.time())}_{candidate_id}"

        # Determine if score was accurate
        was_accurate = None
        if actual_outcome and suggested_score:
            # If hired and score was "go", or rejected and score was "no"
            if (actual_outcome == HireOutcome.HIRED and original_decision == "go") or \
               (actual_outcome == HireOutcome.REJECTED_BY_COMPANY and original_decision == "no"):
                was_accurate = True
            else:
                was_accurate = False

        feedback = FeedbackEntry(
            feedback_id=feedback_id,
            candidate_id=candidate_id,
            feedback_type=feedback_type,
            original_score=original_score,
            original_decision=original_decision,
            actual_outcome=actual_outcome,
            interview_score=interview_score,
            was_score_accurate=was_accurate,
            suggested_score=suggested_score,
            notes=notes,
            submitted_by=submitted_by,
            role=role
        )

        self.feedback_entries.append(feedback)

        # Auto-trigger analysis if enough data
        if len(self.feedback_entries) % 50 == 0:
            self.analyze_feedback()

        return feedback_id

    def analyze_feedback(self) -> FeedbackAnalytics:
        """
        Analyze collected feedback and identify improvement opportunities
        """

        if not self.feedback_entries:
            return FeedbackAnalytics(
                total_feedback_entries=0,
                feedback_by_type={},
                scoring_accuracy_rate=0.0,
                false_positive_rate=0.0,
                false_negative_rate=0.0,
                hire_prediction_accuracy=0.0,
                avg_score_deviation=0.0,
                recommended_adjustments=[]
            )

        # Count feedback by type
        feedback_by_type = defaultdict(int)
        for entry in self.feedback_entries:
            feedback_by_type[entry.feedback_type] += 1

        # Calculate accuracy metrics
        accuracy_entries = [
            e for e in self.feedback_entries
            if e.was_score_accurate is not None
        ]

        scoring_accuracy = 0.0
        if accuracy_entries:
            accurate_count = sum(1 for e in accuracy_entries if e.was_score_accurate)
            scoring_accuracy = accurate_count / len(accuracy_entries)

        # Calculate false positives and false negatives
        hire_outcomes = [
            e for e in self.feedback_entries
            if e.actual_outcome in [HireOutcome.HIRED, HireOutcome.REJECTED_BY_COMPANY]
        ]

        false_positives = 0
        false_negatives = 0
        true_positives = 0
        true_negatives = 0

        for entry in hire_outcomes:
            predicted_hire = entry.original_decision == "go"
            actually_hired = entry.actual_outcome == HireOutcome.HIRED

            if predicted_hire and actually_hired:
                true_positives += 1
            elif predicted_hire and not actually_hired:
                false_positives += 1
            elif not predicted_hire and actually_hired:
                false_negatives += 1
            else:
                true_negatives += 1

        total_predictions = len(hire_outcomes)
        fp_rate = false_positives / total_predictions if total_predictions > 0 else 0.0
        fn_rate = false_negatives / total_predictions if total_predictions > 0 else 0.0

        # Hire prediction accuracy
        hire_accuracy = 0.0
        if total_predictions > 0:
            correct = true_positives + true_negatives
            hire_accuracy = correct / total_predictions

        # Average score deviation
        deviations = []
        for entry in self.feedback_entries:
            if entry.suggested_score:
                deviation = abs(entry.original_score - entry.suggested_score)
                deviations.append(deviation)

        avg_deviation = statistics.mean(deviations) if deviations else 0.0

        # Generate recommendations
        recommendations = self._generate_recommendations(
            scoring_accuracy,
            fp_rate,
            fn_rate,
            avg_deviation
        )

        return FeedbackAnalytics(
            total_feedback_entries=len(self.feedback_entries),
            feedback_by_type=dict(feedback_by_type),
            scoring_accuracy_rate=round(scoring_accuracy, 3),
            false_positive_rate=round(fp_rate, 3),
            false_negative_rate=round(fn_rate, 3),
            hire_prediction_accuracy=round(hire_accuracy, 3),
            avg_score_deviation=round(avg_deviation, 2),
            recommended_adjustments=recommendations
        )

    def _generate_recommendations(
        self,
        accuracy: float,
        fp_rate: float,
        fn_rate: float,
        avg_deviation: float
    ) -> List[str]:
        """Generate improvement recommendations based on metrics"""

        recommendations = []

        # Accuracy recommendations
        if accuracy < 0.7:
            recommendations.append(
                "Low scoring accuracy (<70%). Consider retraining or adjusting scoring weights."
            )

        # False positive recommendations
        if fp_rate > 0.3:
            recommendations.append(
                f"High false positive rate ({fp_rate:.1%}). Increase scoring threshold for 'go' decisions."
            )
            self._create_adjustment(
                "reduce_false_positives",
                {"go_threshold": self.score_thresholds["go"] + 5},
                "Increase 'go' threshold to reduce false positives"
            )

        # False negative recommendations
        if fn_rate > 0.3:
            recommendations.append(
                f"High false negative rate ({fn_rate:.1%}). Decrease scoring threshold or improve skill detection."
            )
            self._create_adjustment(
                "reduce_false_negatives",
                {"go_threshold": self.score_thresholds["go"] - 5},
                "Decrease 'go' threshold to reduce false negatives"
            )

        # Score deviation recommendations
        if avg_deviation > 15:
            recommendations.append(
                f"High average score deviation ({avg_deviation:.1f} points). Review scoring algorithm."
            )

        # No issues found
        if not recommendations:
            recommendations.append("Scoring system performing well. Continue monitoring.")

        return recommendations

    def _create_adjustment(
        self,
        reason: str,
        parameter_changes: Dict,
        expected_impact: str
    ):
        """Create a model adjustment recommendation"""

        adjustment_id = f"adj_{int(time.time())}_{reason}"

        adjustment = ModelAdjustment(
            adjustment_id=adjustment_id,
            reason=reason,
            parameter_changes=parameter_changes,
            expected_impact=expected_impact
        )

        self.model_adjustments.append(adjustment)

    def get_feedback_for_candidate(self, candidate_id: str) -> List[FeedbackEntry]:
        """Get all feedback for a specific candidate"""
        return [
            entry for entry in self.feedback_entries
            if entry.candidate_id == candidate_id
        ]

    def get_recent_feedback(self, days: int = 30) -> List[FeedbackEntry]:
        """Get feedback from last N days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()

        return [
            entry for entry in self.feedback_entries
            if entry.timestamp >= cutoff_str
        ]

    def apply_adjustment(self, adjustment_id: str) -> bool:
        """
        Apply a model adjustment

        Args:
            adjustment_id: Adjustment ID

        Returns:
            True if applied successfully
        """

        for adjustment in self.model_adjustments:
            if adjustment.adjustment_id == adjustment_id:
                if not adjustment.applied:
                    # Apply parameter changes
                    for param, value in adjustment.parameter_changes.items():
                        if param in self.score_thresholds:
                            self.score_thresholds[param] = value

                    adjustment.applied = True
                    return True

        return False

    def get_pending_adjustments(self) -> List[ModelAdjustment]:
        """Get adjustments that haven't been applied yet"""
        return [adj for adj in self.model_adjustments if not adj.applied]

    def export_feedback_data(self) -> Dict:
        """Export all feedback data for analysis"""
        return {
            "feedback_entries": [entry.model_dump() for entry in self.feedback_entries],
            "model_adjustments": [adj.model_dump() for adj in self.model_adjustments],
            "current_thresholds": self.score_thresholds,
            "analytics": self.analyze_feedback().model_dump()
        }


# Global feedback loop instance
feedback_loop = FeedbackLoopSystem()


def submit_hire_outcome_feedback(
    candidate_id: str,
    original_score: int,
    original_decision: str,
    hired: bool,
    role: str,
    notes: str = ""
) -> str:
    """
    Convenience function to submit hire outcome feedback

    Args:
        candidate_id: Candidate ID
        original_score: Original score
        original_decision: Original decision
        hired: Whether candidate was hired
        role: Role
        notes: Additional notes

    Returns:
        Feedback ID
    """

    outcome = HireOutcome.HIRED if hired else HireOutcome.REJECTED_BY_COMPANY

    return feedback_loop.submit_feedback(
        candidate_id=candidate_id,
        original_score=original_score,
        original_decision=original_decision,
        feedback_type=FeedbackType.HIRE_OUTCOME,
        actual_outcome=outcome,
        role=role,
        notes=notes
    )


def get_feedback_analytics() -> Dict:
    """Get current feedback analytics"""
    return feedback_loop.analyze_feedback().model_dump()
