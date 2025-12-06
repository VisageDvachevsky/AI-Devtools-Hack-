"""
A/B Testing Framework for Scoring Models
Test different scoring algorithms and select the best performer
"""
import hashlib
import json
import random
import statistics
import time
from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class ScoringModel(str, Enum):
    BASELINE = "baseline"  # Current production model
    VARIANT_A = "variant_a"
    VARIANT_B = "variant_b"
    VARIANT_C = "variant_c"


class ExperimentMetric(BaseModel):
    name: str
    value: float
    unit: str = ""
    higher_is_better: bool = True


class VariantPerformance(BaseModel):
    variant_name: str
    sample_size: int
    metrics: List[ExperimentMetric]
    avg_score: float
    score_stddev: float
    success_rate: float  # % of candidates scored as "go"
    false_positive_rate: Optional[float] = None
    false_negative_rate: Optional[float] = None


class ABTestExperiment(BaseModel):
    experiment_id: str
    name: str
    description: str
    status: ExperimentStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    # Configuration
    variants: List[str]
    traffic_split: Dict[str, float]  # Variant -> % traffic
    minimum_sample_size: int = 100

    # Results
    variant_performance: Dict[str, VariantPerformance] = Field(default_factory=dict)
    winner: Optional[str] = None
    statistical_significance: Optional[float] = None  # p-value
    confidence_level: float = 0.95


class ScoringVariant:
    """
    Represents a scoring model variant for A/B testing
    """

    def __init__(self, name: str, scoring_function: Callable):
        self.name = name
        self.scoring_function = scoring_function
        self.results: List[Dict] = []

    def score_candidate(self, candidate_data: Dict) -> int:
        """Score a candidate using this variant's algorithm"""
        return self.scoring_function(candidate_data)

    def record_result(self, candidate_data: Dict, score: int, ground_truth: Optional[str] = None):
        """Record scoring result for analysis"""
        self.results.append({
            "candidate_id": candidate_data.get("github_username", "unknown"),
            "score": score,
            "ground_truth": ground_truth,  # Actual outcome: "hired", "rejected", etc.
            "timestamp": time.time()
        })


class ABTestingFramework:
    """
    A/B testing framework for scoring models
    """

    def __init__(self):
        self.experiments: Dict[str, ABTestExperiment] = {}
        self.variants: Dict[str, ScoringVariant] = {}

    def create_experiment(
        self,
        name: str,
        description: str,
        variants: List[str],
        traffic_split: Optional[Dict[str, float]] = None,
        minimum_sample_size: int = 100
    ) -> str:
        """
        Create a new A/B test experiment

        Args:
            name: Experiment name
            description: Description
            variants: List of variant names
            traffic_split: Traffic distribution (must sum to 1.0)
            minimum_sample_size: Min samples per variant

        Returns:
            Experiment ID
        """

        # Generate experiment ID
        experiment_id = hashlib.md5(
            f"{name}_{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:12]

        # Default traffic split: equal distribution
        if not traffic_split:
            split = 1.0 / len(variants)
            traffic_split = {v: split for v in variants}

        # Validate traffic split
        total = sum(traffic_split.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Traffic split must sum to 1.0 (got {total})")

        experiment = ABTestExperiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            status=ExperimentStatus.DRAFT,
            created_at=datetime.utcnow().isoformat(),
            variants=variants,
            traffic_split=traffic_split,
            minimum_sample_size=minimum_sample_size
        )

        self.experiments[experiment_id] = experiment
        return experiment_id

    def register_variant(self, variant_name: str, scoring_function: Callable):
        """Register a scoring variant"""
        self.variants[variant_name] = ScoringVariant(variant_name, scoring_function)

    def start_experiment(self, experiment_id: str):
        """Start running an experiment"""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.utcnow().isoformat()

    def assign_variant(self, experiment_id: str, candidate_id: str) -> str:
        """
        Assign a candidate to a variant using consistent hashing

        Args:
            experiment_id: Experiment ID
            candidate_id: Candidate identifier

        Returns:
            Assigned variant name
        """

        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Consistent hashing for deterministic assignment
        hash_input = f"{experiment_id}:{candidate_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        random_value = (hash_value % 10000) / 10000.0  # 0.0 to 1.0

        # Assign based on traffic split
        cumulative = 0.0
        for variant, split in experiment.traffic_split.items():
            cumulative += split
            if random_value <= cumulative:
                return variant

        # Fallback (shouldn't happen)
        return experiment.variants[0]

    def score_candidate_with_variant(
        self,
        experiment_id: str,
        candidate_id: str,
        candidate_data: Dict,
        ground_truth: Optional[str] = None
    ) -> Tuple[str, int]:
        """
        Score a candidate using assigned variant

        Args:
            experiment_id: Experiment ID
            candidate_id: Candidate ID
            candidate_data: Candidate data
            ground_truth: Actual outcome (for later analysis)

        Returns:
            (variant_name, score)
        """

        # Assign variant
        variant_name = self.assign_variant(experiment_id, candidate_id)

        # Get variant
        variant = self.variants.get(variant_name)
        if not variant:
            raise ValueError(f"Variant {variant_name} not registered")

        # Score candidate
        score = variant.score_candidate(candidate_data)

        # Record result
        variant.record_result(candidate_data, score, ground_truth)

        return variant_name, score

    def analyze_experiment(self, experiment_id: str) -> ABTestExperiment:
        """
        Analyze experiment results and determine winner

        Args:
            experiment_id: Experiment ID

        Returns:
            Updated experiment with results
        """

        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        variant_performance = {}

        for variant_name in experiment.variants:
            variant = self.variants.get(variant_name)
            if not variant or not variant.results:
                continue

            results = variant.results
            scores = [r["score"] for r in results]

            # Calculate metrics
            avg_score = statistics.mean(scores)
            score_stddev = statistics.stdev(scores) if len(scores) > 1 else 0.0

            # Success rate (score >= 70 = "go")
            success_count = sum(1 for s in scores if s >= 70)
            success_rate = success_count / len(scores) if scores else 0.0

            # Calculate false positive/negative rates if ground truth available
            fp_rate = None
            fn_rate = None

            ground_truths = [r.get("ground_truth") for r in results if r.get("ground_truth")]
            if ground_truths:
                true_positives = sum(
                    1 for r in results
                    if r["score"] >= 70 and r.get("ground_truth") == "hired"
                )
                false_positives = sum(
                    1 for r in results
                    if r["score"] >= 70 and r.get("ground_truth") in ["rejected", "not_hired"]
                )
                false_negatives = sum(
                    1 for r in results
                    if r["score"] < 70 and r.get("ground_truth") == "hired"
                )

                total_positives = true_positives + false_positives
                total_actual_hires = true_positives + false_negatives

                if total_positives > 0:
                    fp_rate = false_positives / total_positives
                if total_actual_hires > 0:
                    fn_rate = false_negatives / total_actual_hires

            # Build metrics
            metrics = [
                ExperimentMetric(name="avg_score", value=round(avg_score, 2), higher_is_better=True),
                ExperimentMetric(name="success_rate", value=round(success_rate * 100, 1), unit="%", higher_is_better=True),
                ExperimentMetric(name="score_variance", value=round(score_stddev, 2), higher_is_better=False),
            ]

            if fp_rate is not None:
                metrics.append(ExperimentMetric(
                    name="false_positive_rate",
                    value=round(fp_rate * 100, 1),
                    unit="%",
                    higher_is_better=False
                ))

            if fn_rate is not None:
                metrics.append(ExperimentMetric(
                    name="false_negative_rate",
                    value=round(fn_rate * 100, 1),
                    unit="%",
                    higher_is_better=False
                ))

            variant_performance[variant_name] = VariantPerformance(
                variant_name=variant_name,
                sample_size=len(results),
                metrics=metrics,
                avg_score=round(avg_score, 2),
                score_stddev=round(score_stddev, 2),
                success_rate=round(success_rate, 2),
                false_positive_rate=fp_rate,
                false_negative_rate=fn_rate
            )

        experiment.variant_performance = variant_performance

        # Determine winner (simple: highest avg score)
        if variant_performance:
            winner = max(
                variant_performance.keys(),
                key=lambda v: variant_performance[v].avg_score
            )
            experiment.winner = winner

            # Calculate statistical significance (simplified t-test)
            if len(variant_performance) == 2:
                variants_list = list(variant_performance.keys())
                v1_scores = [r["score"] for r in self.variants[variants_list[0]].results]
                v2_scores = [r["score"] for r in self.variants[variants_list[1]].results]

                if len(v1_scores) > 1 and len(v2_scores) > 1:
                    # Simplified t-test
                    mean_diff = abs(statistics.mean(v1_scores) - statistics.mean(v2_scores))
                    pooled_std = math.sqrt(
                        (statistics.variance(v1_scores) + statistics.variance(v2_scores)) / 2
                    )
                    t_stat = mean_diff / (pooled_std / math.sqrt(min(len(v1_scores), len(v2_scores))))

                    # Rough p-value approximation
                    p_value = 1.0 / (1.0 + t_stat)  # Simplified
                    experiment.statistical_significance = round(p_value, 4)

        return experiment

    def get_experiment(self, experiment_id: str) -> Optional[ABTestExperiment]:
        """Get experiment details"""
        return self.experiments.get(experiment_id)

    def list_experiments(self) -> List[ABTestExperiment]:
        """List all experiments"""
        return list(self.experiments.values())


# Example scoring functions for testing

def baseline_scoring_function(candidate_data: Dict) -> int:
    """Baseline scoring algorithm"""
    score = 50

    skill_scores = candidate_data.get("skill_scores", [])
    if skill_scores:
        avg_skill = sum(s.get("score", 0) for s in skill_scores) / len(skill_scores)
        score += int(avg_skill * 40)

    repos_analyzed = candidate_data.get("repos_analyzed", 0)
    score += min(10, repos_analyzed)

    return min(100, score)


def variant_a_scoring_function(candidate_data: Dict) -> int:
    """Variant A: Weight code analysis more heavily"""
    score = 40

    skill_scores = candidate_data.get("skill_scores", [])
    if skill_scores:
        # Higher weight on skills
        avg_skill = sum(s.get("score", 0) for s in skill_scores) / len(skill_scores)
        score += int(avg_skill * 50)

    # Bonus for code analysis
    code_analysis = candidate_data.get("code_analysis", {})
    if code_analysis.get("dependency_files_found", 0) > 0:
        score += 10

    return min(100, score)


def variant_b_scoring_function(candidate_data: Dict) -> int:
    """Variant B: Weight activity metrics more"""
    score = 45

    skill_scores = candidate_data.get("skill_scores", [])
    if skill_scores:
        avg_skill = sum(s.get("score", 0) for s in skill_scores) / len(skill_scores)
        score += int(avg_skill * 35)

    # Higher weight on activity
    activity = candidate_data.get("activity_metrics", {})
    stars = activity.get("total_stars", 0)
    if stars > 100:
        score += 20
    elif stars > 20:
        score += 10

    return min(100, score)


import math
# Global framework instance
ab_testing_framework = ABTestingFramework()
