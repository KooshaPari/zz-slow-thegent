"""Domain layer - SLA, SLO, contracts and core types.

This module defines the core domain entities shared across thegent:
- Service Level Agreements (SLA)
- Service Level Objectives (SLO)
- Compliance contracts and attestations
- OutputProtocol for structured output parsing
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar, runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path

T = TypeVar("T")


class ContractStatus(Enum):
    """Status of a contract or agreement."""

    DRAFT = auto()
    ACTIVE = auto()
    EXPIRED = auto()
    VIOLATED = auto()
    TERMINATED = auto()


class ContractType(Enum):
    """Types of contracts supported."""

    SLA = "sla"
    SLO = "slo"
    COMPLIANCE = "compliance"
    DATA_PROCESSING = "data_processing"


@dataclass
class SLOTarget:
    """A single SLO target metric."""

    metric: str
    threshold: float
    operator: str = "<="
    window: str = "1h"
    description: str = ""

    def evaluate(self, value: float) -> bool:
        """Evaluate if value meets the SLO target."""
        if self.operator == "<=":
            return value <= self.threshold
        elif self.operator == ">=":
            return value >= self.threshold
        elif self.operator == "==":
            return value == self.threshold
        elif self.operator == "<":
            return value < self.threshold
        elif self.operator == ">":
            return value > self.threshold
        return False


@dataclass
class SLODefinition:
    """Definition of Service Level Objectives."""

    name: str
    description: str = ""
    targets: list[SLOTarget] = field(default_factory=list)
    burn_rate_alerts: list[float] = field(default_factory=lambda: [2.0, 4.0, 8.0])
    alert_channels: list[str] = field(default_factory=list)

    def add_target(self, target: SLOTarget) -> None:
        """Add an SLO target."""
        self.targets.append(target)


@dataclass
class SLAAgreement:
    """Service Level Agreement definition."""

    id: str
    name: str
    provider: str = ""
    consumer: str = ""
    description: str = ""
    slos: list[SLODefinition] = field(default_factory=list)
    penalties: dict[str, Any] = field(default_factory=dict)
    credits: dict[str, Any] = field(default_factory=dict)
    status: ContractStatus = ContractStatus.DRAFT
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    def add_slo(self, slo: SLODefinition) -> None:
        """Add an SLO to this SLA."""
        self.slos.append(slo)

    def is_active(self) -> bool:
        """Check if SLA is currently active."""
        if self.status != ContractStatus.ACTIVE:
            return False
        now = datetime.now()
        if self.valid_from and now < self.valid_from:
            return False
        return not (self.valid_until and now > self.valid_until)


@dataclass
class ComplianceRequirement:
    """A single compliance requirement."""

    id: str
    framework: str
    control: str
    description: str
    severity: str = "medium"
    evidence_required: list[str] = field(default_factory=list)


@dataclass
class ComplianceContract:
    """Compliance contract for regulatory requirements."""

    id: str
    name: str
    framework: str
    version: str
    description: str = ""
    requirements: list[ComplianceRequirement] = field(default_factory=list)
    status: ContractStatus = ContractStatus.DRAFT
    attestations: list[Attestation] = field(default_factory=list)

    def add_requirement(self, req: ComplianceRequirement) -> None:
        """Add a compliance requirement."""
        self.requirements.append(req)


@dataclass
class Attestation:
    """An attestation of compliance."""

    id: str
    contract_id: str
    timestamp: datetime
    attester: str
    scope: str
    evidence: dict[str, Any] = field(default_factory=dict)
    signature: str = ""


@dataclass
class ContractRegistry:
    """Registry for managing contracts."""

    contracts: dict[str, SLAAgreement | ComplianceContract] = field(
        default_factory=dict
    )

    def register(self, contract: SLAAgreement | ComplianceContract) -> None:
        """Register a contract."""
        self.contracts[contract.id] = contract

    def get(self, contract_id: str) -> SLAAgreement | ComplianceContract | None:
        """Get a contract by ID."""
        return self.contracts.get(contract_id)

    def list_by_type(self, contract_type: ContractType) -> list:
        """List contracts by type."""
        if contract_type == ContractType.SLA:
            return [c for c in self.contracts.values() if isinstance(c, SLAAgreement)]
        elif contract_type == ContractType.COMPLIANCE:
            return [
                c for c in self.contracts.values()
                if isinstance(c, ComplianceContract)
            ]
        return []

    def active_slas(self) -> list[SLAAgreement]:
        """Get all active SLAs."""
        return [
            c for c in self.contracts.values()
            if isinstance(c, SLAAgreement) and c.is_active()
        ]


@dataclass
class ParsedOutput[T]:
    """Container for parsed output with metadata."""

    content: T
    format: str
    raw: str
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class OutputProtocol(Protocol[T]):
    """Protocol for output parsing (shared between contracts and output_parser)."""

    def parse(self, raw_output: str) -> ParsedOutput[T]:
        """Parse raw output into structured form."""
        ...

    def validate(self, parsed: ParsedOutput[T]) -> bool:
        """Validate parsed output."""
        ...


__all__ = [
    # Enums
    "ContractStatus",
    "ContractType",
    # SLO
    "SLOTarget",
    "SLODefinition",
    # SLA
    "SLAAgreement",
    # Compliance
    "ComplianceRequirement",
    "ComplianceContract",
    "Attestation",
    # Registry
    "ContractRegistry",
    # Output parsing (shared protocol)
    "ParsedOutput",
    "OutputProtocol",
]
