from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any


# Enums for various categorical data
class UserType(str, Enum):
    B2C = "b2c"
    B2B = "b2b"


class AccountType(str, Enum):
    MASTER = "master"
    MEMBER = "member"


class CompanyType(str, Enum):
    STARTUP = "startup"
    SME = "sme"
    CORPORATION = "corporation"
    NON_PROFIT = "non_profit"
    GOVERNMENT = "government"
    OTHER = "other"


class CompanySize(str, Enum):
    MICRO = "micro"  # 1-9 employees
    SMALL = "small"  # 10-49 employees
    MEDIUM = "medium"  # 50-249 employees
    LARGE = "large"  # 250+ employees


class PricingPlan(str, Enum):
    WEEK_PASS = "week_pass"
    BESTPRICE = "bestprice"


class QueryType(str, Enum):
    LIGHT = "light"
    MAIN = "main"


class Language(str, Enum):
    BG = "bg"  # Bulgarian
    CS = "cs"  # Czech
    DA = "da"  # Danish
    DE = "de"  # German
    EL = "el"  # Greek
    EN = "en"  # English
    ES = "es"  # Spanish
    ET = "et"  # Estonian
    FI = "fi"  # Finnish
    FR = "fr"  # French
    GA = "ga"  # Irish
    HR = "hr"  # Croatian
    HU = "hu"  # Hungarian
    IT = "it"  # Italian
    LT = "lt"  # Lithuanian
    LV = "lv"  # Latvian
    MT = "mt"  # Maltese
    NL = "nl"  # Dutch
    PL = "pl"  # Polish
    PT = "pt"  # Portuguese
    RO = "ro"  # Romanian
    SK = "sk"  # Slovak
    SL = "sl"  # Slovenian
    SV = "sv"  # Swedish


# Core user management models
class Organization(SQLModel, table=True):
    __tablename__ = "organizations"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200)
    company_type: CompanyType
    company_size: CompanySize
    headquarters_location: str = Field(max_length=100)
    subsidiary_locations: List[str] = Field(default=[], sa_column=Column(JSON))
    sso_enabled: bool = Field(default=False)
    sso_config: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    users: List["User"] = Relationship(back_populates="organization")
    api_keys: List["APIKey"] = Relationship(back_populates="organization")


class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, max_length=255)
    password_hash: str = Field(max_length=255)
    user_type: UserType
    account_type: Optional[AccountType] = Field(default=None)
    organization_id: Optional[int] = Field(default=None, foreign_key="organizations.id")
    is_active: bool = Field(default=True)
    can_generate_api_keys: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    organization: Optional[Organization] = Relationship(back_populates="users")
    user_context: Optional["UserContext"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"uselist": False}
    )
    subscriptions: List["Subscription"] = Relationship(back_populates="user")
    api_keys: List["APIKey"] = Relationship(back_populates="user")
    chat_sessions: List["ChatSession"] = Relationship(back_populates="user")
    queries: List["Query"] = Relationship(back_populates="user")
    documents: List["Document"] = Relationship(back_populates="user")
    billing_records: List["BillingRecord"] = Relationship(back_populates="user")


class UserContext(SQLModel, table=True):
    __tablename__ = "user_contexts"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True)
    user_type_context: str = Field(max_length=50)  # "private_person" or "company"
    home_location: str = Field(max_length=100)
    preferred_language: Language
    profession: str = Field(max_length=100)
    personal_notes: str = Field(default="", max_length=2000)
    context_data: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Additional flexible context
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="user_context")


# API Key management
class APIKey(SQLModel, table=True):
    __tablename__ = "api_keys"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    key_hash: str = Field(max_length=255, unique=True)
    name: str = Field(max_length=100)
    user_id: int = Field(foreign_key="users.id")
    organization_id: Optional[int] = Field(default=None, foreign_key="organizations.id")
    is_active: bool = Field(default=True)
    last_used_at: Optional[datetime] = Field(default=None)
    expires_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="api_keys")
    organization: Optional[Organization] = Relationship(back_populates="api_keys")


# Pricing and subscription models
class Subscription(SQLModel, table=True):
    __tablename__ = "subscriptions"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    pricing_plan: PricingPlan
    is_active: bool = Field(default=True)

    # Week Pass specific fields
    token_allowance: Optional[int] = Field(default=None)  # Total tokens for week pass
    tokens_used: int = Field(default=0)
    week_pass_expires_at: Optional[datetime] = Field(default=None)
    week_pass_price: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=10)

    # Bestprice Plan specific fields
    current_price_per_1k_tokens: Optional[Decimal] = Field(default=None, decimal_places=4, max_digits=10)
    total_tokens_consumed: int = Field(default=0)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="subscriptions")
    token_usages: List["TokenUsage"] = Relationship(back_populates="subscription")
    billing_records: List["BillingRecord"] = Relationship(back_populates="subscription")


class TokenUsage(SQLModel, table=True):
    __tablename__ = "token_usages"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    subscription_id: int = Field(foreign_key="subscriptions.id")
    query_id: Optional[int] = Field(default=None, foreign_key="queries.id")
    tokens_consumed: int
    cost: Decimal = Field(decimal_places=4, max_digits=10)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    subscription: Subscription = Relationship(back_populates="token_usages")
    query: Optional["Query"] = Relationship(back_populates="token_usage")


# Document management
class Document(SQLModel, table=True):
    __tablename__ = "documents"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    filename: str = Field(max_length=255)
    original_filename: str = Field(max_length=255)
    file_size: int  # in bytes
    mime_type: str = Field(max_length=100)
    file_path: str = Field(max_length=500)  # Storage path
    language: Optional[Language] = Field(default=None)
    processed: bool = Field(default=False)
    processing_error: Optional[str] = Field(default=None, max_length=1000)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = Field(default=None)

    user: User = Relationship(back_populates="documents")
    chat_session_links: List["ChatSessionDocument"] = Relationship(back_populates="document")


# Chat and query models
class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    title: str = Field(max_length=200)
    query_type: QueryType
    language: Language
    is_active: bool = Field(default=True)
    session_context: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Applied user context
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="chat_sessions")
    queries: List["Query"] = Relationship(back_populates="chat_session")
    document_links: List["ChatSessionDocument"] = Relationship(back_populates="chat_session")


class ChatSessionDocument(SQLModel, table=True):
    __tablename__ = "chat_session_documents"  # type: ignore[assignment]

    chat_session_id: int = Field(foreign_key="chat_sessions.id", primary_key=True)
    document_id: int = Field(foreign_key="documents.id", primary_key=True)
    added_at: datetime = Field(default_factory=datetime.utcnow)

    chat_session: "ChatSession" = Relationship()
    document: "Document" = Relationship()


class Query(SQLModel, table=True):
    __tablename__ = "queries"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    chat_session_id: Optional[int] = Field(default=None, foreign_key="chat_sessions.id")
    query_type: QueryType
    query_text: str = Field(max_length=5000)
    response_text: str = Field(default="")
    language: Language
    tokens_consumed: int = Field(default=0)
    processing_time_ms: Optional[int] = Field(default=None)
    sources: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))  # References to original sources
    chunks: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))  # Document chunks for Light version
    context_used: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # User context applied to this query
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="queries")
    chat_session: Optional[ChatSession] = Relationship(back_populates="queries")
    token_usage: Optional[TokenUsage] = Relationship(back_populates="query", sa_relationship_kwargs={"uselist": False})


# Billing and payment tracking
class BillingRecord(SQLModel, table=True):
    __tablename__ = "billing_records"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    subscription_id: int = Field(foreign_key="subscriptions.id")
    billing_period_start: datetime
    billing_period_end: datetime
    total_tokens: int
    total_cost: Decimal = Field(decimal_places=2, max_digits=10)
    currency: str = Field(default="EUR", max_length=3)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: "User" = Relationship()
    subscription: "Subscription" = Relationship()


# Non-persistent schemas for validation and API
class UserCreate(SQLModel, table=False):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8)
    user_type: UserType
    organization_name: Optional[str] = Field(default=None, max_length=200)


class UserContextCreate(SQLModel, table=False):
    user_type_context: str = Field(max_length=50)
    home_location: str = Field(max_length=100)
    preferred_language: Language
    profession: str = Field(max_length=100)
    personal_notes: str = Field(default="", max_length=2000)
    context_data: Dict[str, Any] = Field(default={})


class UserContextUpdate(SQLModel, table=False):
    user_type_context: Optional[str] = Field(default=None, max_length=50)
    home_location: Optional[str] = Field(default=None, max_length=100)
    preferred_language: Optional[Language] = Field(default=None)
    profession: Optional[str] = Field(default=None, max_length=100)
    personal_notes: Optional[str] = Field(default=None, max_length=2000)
    context_data: Optional[Dict[str, Any]] = Field(default=None)


class OrganizationCreate(SQLModel, table=False):
    name: str = Field(max_length=200)
    company_type: CompanyType
    company_size: CompanySize
    headquarters_location: str = Field(max_length=100)
    subsidiary_locations: List[str] = Field(default=[])


class QueryCreate(SQLModel, table=False):
    query_text: str = Field(max_length=5000)
    query_type: QueryType
    language: Language
    chat_session_id: Optional[int] = Field(default=None)


class SubscriptionCreate(SQLModel, table=False):
    pricing_plan: PricingPlan
    token_allowance: Optional[int] = Field(default=None)
    week_pass_price: Optional[Decimal] = Field(default=None)


class APIKeyCreate(SQLModel, table=False):
    name: str = Field(max_length=100)
    expires_at: Optional[datetime] = Field(default=None)


class DocumentUpload(SQLModel, table=False):
    filename: str = Field(max_length=255)
    file_size: int
    mime_type: str = Field(max_length=100)
    language: Optional[Language] = Field(default=None)


class ChatSessionCreate(SQLModel, table=False):
    title: str = Field(max_length=200)
    query_type: QueryType
    language: Language
    document_ids: List[int] = Field(default=[])
