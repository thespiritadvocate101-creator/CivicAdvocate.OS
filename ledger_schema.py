#!/usr/bin/env python3
"""
Production-Grade Truth Mandate Ledger Schema
============================================

Strict separation of:
  - Technical fact (verifiable, measurable)
  - Legal claim (requires jurisdiction/authority)
  - Declarative statement (symbolic/philosophical)
  
No mixing of categories. Each entry must declare its type.
"""

from enum import Enum
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
import hashlib
import json
import sqlite3

# ============================================================================
# ENUMERATIONS: Control Categories & Confidence Levels
# ============================================================================

class ClaimType(Enum):
    """Category of what is being asserted."""
    TECHNICAL_FACT = "technical_fact"           # Measurable, testable, verifiable
    LEGAL_CLAIM = "legal_claim"                 # Requires jurisdiction or authority
    DECLARATIVE = "declarative"                 # Assertion, principle, covenant
    CORRECTION = "correction"                   # Fix to a prior entry
    STATUS_UPDATE = "status_update"             # Change in status of existing claim


class Confidence(Enum):
    """How certain we are of the claim."""
    PROVEN = "proven"                           # Verified by independent test
    PROBABLE = "probable"                       # Multiple credible sources
    PLAUSIBLE = "plausible"                     # Consistent with evidence
    UNVERIFIED = "unverified"                   # Claim made but not verified
    DISPUTED = "disputed"                       # Evidence contradicts claim
    WITHDRAWN = "withdrawn"                     # Claim retracted


class EntryStatus(Enum):
    """What stage is this entry in."""
    PENDING = "pending"                         # Awaiting validation
    VALIDATED = "validated"                     # Passed all checks
    CORRECTED = "corrected"                     # Superseded by correction
    DISPUTED = "disputed"                       # Contradicted by other entry
    ARCHIVED = "archived"                       # No longer active


# ============================================================================
# CORE DATA STRUCTURES
# ============================================================================

@dataclass
class Evidence:
    """A single piece of supporting evidence."""
    source_uri: str                 # URL, file path, or verifiable reference
    source_type: str                # "document", "test", "observation", "authority"
    excerpt: Optional[str] = None   # Quote or specific claim from source
    date_accessed: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confidence_weight: float = 1.0  # 0.0 to 1.0: how much this evidence matters


@dataclass
class Assumption:
    """Explicitly state what we're assuming."""
    assumption: str                 # What we're assuming to be true
    reason: str                     # Why we're making this assumption
    risk: str                       # What happens if this is wrong
    status: str = "active"          # "active" or "invalidated"


@dataclass
class Correction:
    """A record of how this entry was corrected."""
    corrected_by_entry_id: str      # ID of the correction entry
    correction_reason: str          # Why the change was needed
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evidence_of_error: str = ""     # What proved the prior version wrong


@dataclass
class TruthMandateEntry:
    """
    A single entry in the Truth Mandate Ledger.
    
    This is the core disciplined structure: claim, evidence, confidence, status.
    Everything else is narrative.
    """
    
    # === IDENTIFICATION ===
    entry_id: str                           # Unique ID for this entry
    claim_type: ClaimType                   # Category: fact, legal, declarative
    
    # === THE CLAIM ===
    claim: str                              # What is being asserted
    claim_scope: str                        # What domain/context this applies to
    
    # === EVIDENCE ===
    evidence: List[Evidence]                # List of supporting sources
    total_evidence_weight: float = 0.0      # Sum of confidence weights
    
    # === ASSUMPTIONS ===
    assumptions: List[Assumption] = field(default_factory=list)
    
    # === CONFIDENCE & STATUS ===
    confidence: Confidence = Confidence.UNVERIFIED
    status: EntryStatus = EntryStatus.PENDING
    
    # === CONTRADICTIONS ===
    contradicted_by: List[str] = field(default_factory=list)  # IDs of conflicting entries
    
    # === CORRECTION HISTORY ===
    corrections: List[Correction] = field(default_factory=list)
    
    # === TIMESTAMPS ===
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # === ACCOUNTABILITY ===
    recorded_by: str                        # Who entered this
    authority: str                          # By what authority (if any)
    
    # === CRYPTOGRAPHIC SEAL ===
    content_hash: str = ""                  # SHA-512 of normalized content
    entry_hash: str = ""                    # SHA-512 of full entry (for chain)
    previous_entry_hash: str = ""           # Link to prior entry (blockchain-style)
    
    # === METADATA ===
    tags: List[str] = field(default_factory=list)
    notes: str = ""

    def compute_content_hash(self) -> str:
        """Compute SHA-512 of the claim content only (for detecting changes)."""
        content_str = json.dumps({
            "claim": self.claim,
            "claim_type": self.claim_type.value,
            "claim_scope": self.claim_scope,
        }, sort_keys=True, separators=(',', ':'))
        return hashlib.sha512(content_str.encode()).hexdigest()

    def compute_entry_hash(self) -> str:
        """Compute SHA-512 of the entire normalized entry (for chain integrity)."""
        entry_dict = asdict(self)
        # Remove hashes to avoid circular dependency
        entry_dict.pop('content_hash', None)
        entry_dict.pop('entry_hash', None)
        # Normalize enums to strings
        entry_dict['claim_type'] = self.claim_type.value
        entry_dict['confidence'] = self.confidence.value
        entry_dict['status'] = self.status.value
        entry_str = json.dumps(entry_dict, sort_keys=True, separators=(',', ':'), default=str)
        return hashlib.sha512(entry_str.encode()).hexdigest()

    def seal(self, previous_entry_hash: str = "") -> None:
        """Compute and set all hashes."""
        self.content_hash = self.compute_content_hash()
        self.previous_entry_hash = previous_entry_hash
        self.entry_hash = self.compute_entry_hash()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        d['claim_type'] = self.claim_type.value
        d['confidence'] = self.confidence.value
        d['status'] = self.status.value
        d['evidence'] = [asdict(e) for e in self.evidence]
        d['assumptions'] = [asdict(a) for a in self.assumptions]
        d['corrections'] = [asdict(c) for c in self.corrections]
        return d


# ============================================================================
# VALIDATION RULES
# ============================================================================

class ValidationError(Exception):
    """Raised when an entry fails validation."""
    pass


def validate_entry(entry: TruthMandateEntry) -> tuple[bool, List[str]]:
    """
    Strict validation of a ledger entry.
    
    Returns: (is_valid, list_of_errors)
    """
    errors = []
    
    # Required fields
    if not entry.entry_id or len(entry.entry_id.strip()) == 0:
        errors.append("entry_id: cannot be empty")
    
    if not entry.claim or len(entry.claim.strip()) == 0:
        errors.append("claim: cannot be empty")
    
    if not entry.claim_scope or len(entry.claim_scope.strip()) == 0:
        errors.append("claim_scope: cannot be empty")
    
    if not entry.recorded_by or len(entry.recorded_by.strip()) == 0:
        errors.append("recorded_by: must identify who made this claim")
    
    # Evidence rules
    if entry.confidence not in [Confidence.DECLARATIVE, Confidence.WITHDRAWN]:
        if len(entry.evidence) == 0:
            errors.append(f"evidence: {entry.confidence.value} confidence requires at least one source")
    
    for i, evid in enumerate(entry.evidence):
        if not evid.source_uri:
            errors.append(f"evidence[{i}].source_uri: cannot be empty")
        if evid.confidence_weight < 0.0 or evid.confidence_weight > 1.0:
            errors.append(f"evidence[{i}].confidence_weight: must be between 0.0 and 1.0")
    
    # Assumption rules: each assumption must explain the risk
    for i, assumption in enumerate(entry.assumptions):
        if not assumption.risk or len(assumption.risk.strip()) == 0:
            errors.append(f"assumptions[{i}].risk: must explain what happens if wrong")
    
    # Legal claims require authority
    if entry.claim_type == ClaimType.LEGAL_CLAIM:
        if not entry.authority or entry.authority == "":
            errors.append("Legal claims must specify authority (jurisdiction, court, statute, etc.)")
    
    # Hash integrity
    if entry.content_hash == "":
        errors.append("content_hash: must be sealed before storage")
    if entry.entry_hash == "":
        errors.append("entry_hash: must be sealed before storage")
    
    return len(errors) == 0, errors


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("TRUTH MANDATE LEDGER: SCHEMA VALIDATION TEST")
    print("=" * 70)
    
    # Test 1: Valid technical fact
    print("\n[TEST 1] Valid Technical Fact Entry")
    print("-" * 70)
    
    entry_1 = TruthMandateEntry(
        entry_id="TECH_001_SHA512_BASELINE",
        claim_type=ClaimType.TECHNICAL_FACT,
        claim="File civic_ledger.db has SHA-512 hash abc123...",
        claim_scope="File Integrity / Abstract 544",
        recorded_by="Brandon Lynn Campbell",
        authority="Self-verifying (cryptographic)",
        evidence=[
            Evidence(
                source_uri="file:///civic_ledger.db",
                source_type="document",
                excerpt="SHA-512 verified by sha512sum command",
                confidence_weight=1.0
            )
        ],
        assumptions=[
            Assumption(
                assumption="SHA-512 is collision-resistant",
                reason="Standard cryptographic assumption",
                risk="If SHA-512 is broken, hash can be forged"
            )
        ],
        confidence=Confidence.PROVEN,
        status=EntryStatus.VALIDATED
    )
    
    entry_1.seal()
    is_valid, errors = validate_entry(entry_1)
    print(f"Valid: {is_valid}")
    if errors:
        for err in errors:
            print(f"  ERROR: {err}")
    print(f"Content Hash: {entry_1.content_hash[:32]}...")
    print(f"Entry Hash:   {entry_1.entry_hash[:32]}...")
    
    # Test 2: Unverified claim (should fail without evidence)
    print("\n[TEST 2] Claim Without Evidence (should fail validation)")
    print("-" * 70)
    
    entry_2 = TruthMandateEntry(
        entry_id="LEGAL_001_ABSTRACT_544",
        claim_type=ClaimType.LEGAL_CLAIM,
        claim="Abstract 544 is the true metes-and-bounds record",
        claim_scope="Johnson County, Texas Property",
        recorded_by="Brandon Lynn Campbell",
        authority="",  # Missing authority
        evidence=[],
        confidence=Confidence.UNVERIFIED,
        status=EntryStatus.PENDING
    )
    
    entry_2.seal()
    is_valid, errors = validate_entry(entry_2)
    print(f"Valid: {is_valid}")
    if errors:
        for err in errors:
            print(f"  ERROR: {err}")
    
    # Test 3: Declarative statement (no evidence required)
    print("\n[TEST 3] Valid Declarative Statement")
    print("-" * 70)
    
    entry_3 = TruthMandateEntry(
        entry_id="DECL_001_COVENANT",
        claim_type=ClaimType.DECLARATIVE,
        claim="I commit to absolute transparency and accountability",
        claim_scope="Personal Sovereign Covenant",
        recorded_by="Brandon Lynn Campbell",
        authority="Self-sovereign",
        evidence=[],
        confidence=Confidence.PROVEN,  # For declarative, this means "stated"
        status=EntryStatus.VALIDATED
    )
    
    entry_3.seal()
    is_valid, errors = validate_entry(entry_3)
    print(f"Valid: {is_valid}")
    if errors:
        for err in errors:
            print(f"  ERROR: {err}")
    print(f"Entry Hash: {entry_3.entry_hash[:32]}...")
    
    # Test 4: Chain verification
    print("\n[TEST 4] Entry Chain Verification")
    print("-" * 70)
    
    entry_4 = TruthMandateEntry(
        entry_id="TECH_002_CORRECTION",
        claim_type=ClaimType.CORRECTION,
        claim="Previous hash was incorrect; correcting to new value",
        claim_scope="File Integrity / Abstract 544",
        recorded_by="Brandon Lynn Campbell",
        authority="Self-correcting error",
        evidence=[
            Evidence(
                source_uri="audit_log.txt",
                source_type="document",
                excerpt="Hash verification detected discrepancy",
                confidence_weight=1.0
            )
        ],
        confidence=Confidence.PROVEN,
        status=EntryStatus.VALIDATED,
        corrections=[
            Correction(
                corrected_by_entry_id="TECH_001_SHA512_BASELINE",
                correction_reason="Original hash was stale",
                evidence_of_error="Re-verification showed different hash"
            )
        ]
    )
    
    entry_4.seal(previous_entry_hash=entry_3.entry_hash)
    is_valid, errors = validate_entry(entry_4)
    print(f"Valid: {is_valid}")
    print(f"Previous Entry Hash: {entry_3.entry_hash[:32]}...")
    print(f"This Entry Hash:     {entry_4.entry_hash[:32]}...")
    print(f"Chain Link: {entry_4.previous_entry_hash[:32]}...")
    
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETE")
    print("=" * 70)
