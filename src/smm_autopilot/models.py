from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class SourceType(str, Enum):
    rss = "rss"
    telegram_channel = "telegram_channel"
    web_page = "web_page"


class RawItemStatus(str, Enum):
    pending = "pending"
    processed = "processed"
    error = "error"


class Category(str, Enum):
    privacy = "privacy"
    circumvention = "circumvention"
    platform_policy = "platform_policy"
    competitors = "competitors"
    product_launches = "product_launches"
    other = "other"


class ClassificationMethod(str, Enum):
    llm = "llm"
    keyword_fallback = "keyword_fallback"


class ClassifiedItemStatus(str, Enum):
    classified = "classified"
    discarded = "discarded"
    generation_failed = "generation_failed"


class Platform(str, Enum):
    telegram = "telegram"
    x = "x"
    threads = "threads"
    instagram = "instagram"


class DraftStatus(str, Enum):
    ready = "ready"
    unverified = "unverified"
    approved = "approved"
    rejected = "rejected"
    deferred = "deferred"
    expired = "expired"
    generation_failed = "generation_failed"


class ChosenVariant(str, Enum):
    a = "a"
    b = "b"


class PublishJobStatus(str, Enum):
    scheduled = "scheduled"
    publishing = "publishing"
    published = "published"
    failed = "failed"
    cancelled = "cancelled"


class SourceCandidateStatus(str, Enum):
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"


class PublishLogEvent(str, Enum):
    attempt = "attempt"
    success = "success"
    failure = "failure"
    retry = "retry"


class MetricsPeriod(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    total = "total"


class AddedBy(str, Enum):
    po_manual = "po_manual"
    autodiscovery = "autodiscovery"


@dataclass
class SchemaVersion:
    id: int = 1
    version: int = 0
    applied_at: Optional[datetime] = None


@dataclass
class Source:
    id: Optional[int] = None
    type: SourceType = SourceType.rss
    url: str = ""
    name: str = ""
    is_active: bool = True
    added_by: AddedBy = AddedBy.po_manual
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class RawItem:
    id: Optional[int] = None
    source_id: int = 0
    external_id: str = ""
    title: Optional[str] = None
    body: str = ""
    url: Optional[str] = None
    image_url: Optional[str] = None
    published_at: Optional[datetime] = None
    ingested_at: Optional[datetime] = None
    status: RawItemStatus = RawItemStatus.pending


@dataclass
class ClassifiedItem:
    id: Optional[int] = None
    raw_item_id: int = 0
    category: Category = Category.other
    is_sensitive: bool = False
    is_time_sensitive: bool = False
    relevance_score: float = 0.0
    classification_method: ClassificationMethod = ClassificationMethod.llm
    status: ClassifiedItemStatus = ClassifiedItemStatus.classified
    generation_retry_count: int = 0
    next_generation_attempt_at: Optional[datetime] = None
    last_generation_error: Optional[str] = None
    classified_at: Optional[datetime] = None


@dataclass
class Channel:
    id: Optional[int] = None
    platform: Platform = Platform.telegram
    name: str = ""
    is_active: bool = False
    credentials_provisioned: bool = False
    cadence_posts_per_day: int = 1
    cadence_posts_per_week_target: int = 0
    publish_window_utc: str = ""
    char_limit: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Draft:
    id: Optional[int] = None
    classified_item_id: int = 0
    channel_id: int = 0
    variant_a_text: str = ""
    variant_b_text: str = ""
    image_url: Optional[str] = None
    citations: str = ""
    status: DraftStatus = DraftStatus.ready
    chosen_variant: Optional[ChosenVariant] = None
    po_edit_text: Optional[str] = None
    is_sensitive: bool = False
    approved_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class PublishJob:
    id: Optional[int] = None
    draft_id: int = 0
    channel_id: int = 0
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    platform_post_id: Optional[str] = None
    status: PublishJobStatus = PublishJobStatus.scheduled
    retry_count: int = 0
    max_retry_count: int = 3
    last_error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class SourceCandidate:
    id: Optional[int] = None
    url: str = ""
    type: SourceType = SourceType.rss
    discovered_from_item_id: int = 0
    status: SourceCandidateStatus = SourceCandidateStatus.pending_approval
    created_at: Optional[datetime] = None


@dataclass
class CadenceConfig:
    id: Optional[int] = None
    global_kill_switch: bool = False
    updated_at: Optional[datetime] = None


@dataclass
class SensitivityKeyword:
    id: Optional[int] = None
    keyword: str = ""
    created_at: Optional[datetime] = None


@dataclass
class PublishLog:
    id: Optional[int] = None
    publish_job_id: int = 0
    event: PublishLogEvent = PublishLogEvent.attempt
    detail: str = ""
    timestamp: Optional[datetime] = None


@dataclass
class Metrics:
    name: str = ""
    period: MetricsPeriod = MetricsPeriod.daily
    value: int = 0
    period_date: str = ""
    updated_at: Optional[datetime] = None


METRICS_COUNTER_NAMES: list[str] = [
    "items_ingested",
    "items_classified",
    "drafts_generated",
    "drafts_approved",
    "drafts_rejected",
    "posts_published",
    "posts_failed",
    "llm_calls_total",
    "llm_tokens_total",
    "llm_errors",
]
