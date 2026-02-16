"""
Contract Analyzer Module
========================
Core intelligence for contract analysis:
- Clause identification and extraction
- Risk scoring with reasoning
- Benchmark comparison (RAG)
- Negotiation recommendations

Uses structured prompting for consistent, reliable outputs.
"""

import os
import json
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


class ClauseType(Enum):
    """Standard contract clause categories"""
    PARTIES = "parties"
    DEFINITIONS = "definitions"
    SCOPE_OF_WORK = "scope_of_work"
    PAYMENT_TERMS = "payment_terms"
    TERM_DURATION = "term_duration"
    TERMINATION = "termination"
    CONFIDENTIALITY = "confidentiality"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    LIABILITY = "liability"
    INDEMNIFICATION = "indemnification"
    WARRANTIES = "warranties"
    FORCE_MAJEURE = "force_majeure"
    DISPUTE_RESOLUTION = "dispute_resolution"
    GOVERNING_LAW = "governing_law"
    ASSIGNMENT = "assignment"
    AMENDMENT = "amendment"
    NOTICES = "notices"
    INSURANCE = "insurance"
    DATA_PROTECTION = "data_protection"
    NON_COMPETE = "non_compete"
    NON_SOLICITATION = "non_solicitation"
    COMPLIANCE = "compliance"
    AUDIT_RIGHTS = "audit_rights"
    OTHER = "other"


class RiskLevel(Enum):
    """Risk levels for clause assessment"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    STANDARD = "standard"


@dataclass
class ExtractedClause:
    """Represents an extracted contract clause"""
    clause_type: ClauseType
    title: str
    text: str
    section_reference: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 0.0


@dataclass
class RiskAssessment:
    """Risk assessment for a single clause"""
    clause_type: ClauseType
    risk_level: RiskLevel
    risk_score: int  # 1-10
    findings: List[str]
    reasoning: str
    market_comparison: str
    recommendations: List[str]
    red_flags: List[str] = field(default_factory=list)


@dataclass
class ContractMetadata:
    """Basic contract metadata"""
    contract_type: str
    parties: List[str]
    effective_date: Optional[str]
    expiration_date: Optional[str]
    total_value: Optional[str]
    governing_law: Optional[str]
    jurisdiction: Optional[str]


@dataclass 
class ContractAnalysis:
    """Complete contract analysis result"""
    metadata: ContractMetadata
    clauses: List[ExtractedClause]
    risk_assessments: List[RiskAssessment]
    overall_risk_score: float
    overall_risk_level: RiskLevel
    executive_summary: str
    key_concerns: List[str]
    negotiation_points: List[Dict]
    analysis_timestamp: str


# =============================================================================
# BENCHMARK KNOWLEDGE BASE
# =============================================================================

MARKET_BENCHMARKS = {
    ClauseType.LIABILITY: {
        "market_standard": "Liability caps typically range from 1x to 2x the contract value for general liability, with carve-outs for gross negligence, willful misconduct, and IP infringement.",
        "red_flags": [
            "Unlimited liability",
            "Liability cap below 50% of contract value",
            "No carve-outs for gross negligence",
            "One-sided liability (only one party limited)",
            "Waiver of consequential damages for receiving party only"
        ],
        "best_practice": "Mutual liability cap at 1-2x annual contract value with appropriate carve-outs for IP infringement, confidentiality breaches, and gross negligence."
    },
    
    ClauseType.TERMINATION: {
        "market_standard": "30-90 days written notice for termination for convenience. Immediate termination for material breach with cure period (typically 30 days).",
        "red_flags": [
            "No termination for convenience",
            "Termination notice period > 180 days",
            "No cure period for breaches",
            "Automatic renewal without notice",
            "Excessive termination fees",
            "One-sided termination rights"
        ],
        "best_practice": "Mutual termination rights with 60-90 day notice. 30-day cure period for material breaches. Clear definition of material breach."
    },
    
    ClauseType.INTELLECTUAL_PROPERTY: {
        "market_standard": "Work product created specifically for client belongs to client. Pre-existing IP remains with original owner. License to use pre-existing IP incorporated in deliverables.",
        "red_flags": [
            "Blanket IP transfer including pre-existing IP",
            "No license to use deliverables",
            "Unclear ownership of derivative works",
            "IP assignment without compensation",
            "Moral rights waiver required",
            "Unlimited license scope"
        ],
        "best_practice": "Clear delineation between work product (client owns), pre-existing IP (owner retains), and licensed materials. Specific license grants for each category."
    },
    
    ClauseType.INDEMNIFICATION: {
        "market_standard": "Mutual indemnification for third-party claims arising from breach, negligence, or IP infringement. Indemnifying party controls defense.",
        "red_flags": [
            "One-sided indemnification",
            "Indemnification for indirect/consequential damages",
            "No cap on indemnification",
            "Indemnification triggered by mere allegations",
            "Duty to indemnify without defense control",
            "Indemnification survives termination indefinitely"
        ],
        "best_practice": "Mutual, balanced indemnification. Cap on indemnification obligations. Indemnifying party controls defense with cooperation from indemnified party."
    },
    
    ClauseType.CONFIDENTIALITY: {
        "market_standard": "Mutual confidentiality obligations. 3-5 year term post-termination. Standard exceptions (public information, independently developed, etc.).",
        "red_flags": [
            "Perpetual confidentiality obligations",
            "One-sided confidentiality",
            "No standard exceptions",
            "Overly broad definition of confidential information",
            "No ability to disclose under legal compulsion",
            "Confidentiality survives indefinitely"
        ],
        "best_practice": "Mutual obligations with 3-year post-termination term. Standard exceptions included. Clear marking requirements for confidential materials."
    },
    
    ClauseType.PAYMENT_TERMS: {
        "market_standard": "Net 30-45 days payment terms. Clear invoicing requirements. Interest on late payments (1-1.5% monthly).",
        "red_flags": [
            "Payment terms > Net 60",
            "Payment contingent on third-party actions",
            "No late payment penalties for customer",
            "Excessive early payment discounts demanded",
            "Right to offset disputed amounts",
            "Acceptance criteria not clearly defined"
        ],
        "best_practice": "Net 30 payment terms. Clear acceptance criteria. Late payment interest at 1.5% monthly or maximum legal rate."
    },
    
    ClauseType.WARRANTIES: {
        "market_standard": "Warranty that services will be performed in professional manner. 90-day warranty period for deliverables. Warranty disclaimed for third-party components.",
        "red_flags": [
            "No warranties provided",
            "Warranty period < 30 days",
            "Complete warranty disclaimer (AS-IS)",
            "Fitness for particular purpose warranty without limitations",
            "Warranty contingent on payment",
            "No warranty remedy specified"
        ],
        "best_practice": "90-day warranty on deliverables. Professional service warranty. Clear remedy (repair, replace, refund). Appropriate disclaimers for third-party components."
    },
    
    ClauseType.FORCE_MAJEURE: {
        "market_standard": "Excuses performance for events beyond reasonable control. 30-90 day trigger for termination rights. Notification requirements.",
        "red_flags": [
            "No force majeure clause",
            "Pandemic/epidemic excluded",
            "One-sided force majeure protection",
            "No termination right after extended force majeure",
            "No notification requirements",
            "Economic hardship included as force majeure"
        ],
        "best_practice": "Mutual protection for events beyond reasonable control. 90-day trigger for termination. Prompt notification required. Duty to mitigate."
    },
    
    ClauseType.DATA_PROTECTION: {
        "market_standard": "Compliance with applicable data protection laws (GDPR, CCPA). Data processing agreement required. Security measures specified.",
        "red_flags": [
            "No data protection provisions",
            "Unlimited data retention",
            "No breach notification requirements",
            "Subprocessor use without consent",
            "No security requirements",
            "Data can be used for provider's purposes"
        ],
        "best_practice": "GDPR/CCPA compliant provisions. 72-hour breach notification. Subprocessor restrictions. Annual security audits. Data deletion upon termination."
    },
    
    ClauseType.DISPUTE_RESOLUTION: {
        "market_standard": "Escalation procedure (operational -> management -> executive). Mediation before arbitration/litigation. Choice of neutral venue.",
        "red_flags": [
            "Litigation as first resort",
            "Venue in distant/unfavorable jurisdiction",
            "Waiver of jury trial without reciprocity",
            "Class action waiver for consumer contracts",
            "Loser pays all costs",
            "Binding arbitration with no appeal rights"
        ],
        "best_practice": "Escalation procedure with defined timelines. Mediation required before formal proceedings. Neutral venue. Prevailing party attorney fees."
    }
}


# =============================================================================
# LLM INTERFACE
# =============================================================================

class ContractLLM:
    """
    Interface for LLM-powered contract analysis.
    Supports Groq (free, fast) and Google Gemini (free tier).
    """
    
    def __init__(self, provider: str = "groq", api_key: str = None):
        """
        Initialize the LLM interface.
        
        Args:
            provider: "groq" or "gemini"
            api_key: API key for the provider
        """
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv(
            "GROQ_API_KEY" if provider == "groq" else "GOOGLE_API_KEY"
        )
        
        if self.provider == "groq":
            self._init_groq()
        elif self.provider == "gemini":
            self._init_gemini()
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def _init_groq(self):
        """Initialize Groq client."""
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            self.model = "llama-3.3-70b-versatile"
        except ImportError:
            raise ImportError("groq package required. Install with: pip install groq")
    
    def _init_gemini(self):
        """Initialize Gemini client."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            # FIXED: Use gemini-2.0-flash instead of deprecated gemini-1.5-flash
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        except ImportError:
            raise ImportError("google-generativeai required. Install with: pip install google-generativeai")
    
    def generate(self, prompt: str, temperature: float = 0.1) -> str:
        """
        Generate response from LLM.
        
        Args:
            prompt: The prompt to send
            temperature: Sampling temperature (lower = more deterministic)
            
        Returns:
            Generated text response
        """
        if self.provider == "groq":
            return self._generate_groq(prompt, temperature)
        else:
            return self._generate_gemini(prompt, temperature)
    
    def _generate_groq(self, prompt: str, temperature: float) -> str:
        """Generate using Groq."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=4096
        )
        return response.choices[0].message.content
    
    def _generate_gemini(self, prompt: str, temperature: float) -> str:
        """Generate using Gemini."""
        response = self.model.generate_content(
            prompt,
            generation_config={"temperature": temperature}
        )
        return response.text


# =============================================================================
# CONTRACT ANALYZER
# =============================================================================

class ContractAnalyzer:
    """
    Main contract analysis engine.
    Orchestrates extraction, risk assessment, and recommendations.
    """
    
    def __init__(self, llm: ContractLLM = None):
        """
        Initialize the analyzer.
        
        Args:
            llm: ContractLLM instance (will create default if not provided)
        """
        self.llm = llm or ContractLLM()
    
    def analyze(self, contract_text: str) -> ContractAnalysis:
        """
        Perform full contract analysis.
        
        Args:
            contract_text: Full text of the contract
            
        Returns:
            ContractAnalysis with complete results
        """
        # Step 1: Extract metadata
        metadata = self._extract_metadata(contract_text)
        
        # Step 2: Extract and categorize clauses
        clauses = self._extract_clauses(contract_text)
        
        # Step 3: Assess risk for each clause
        risk_assessments = []
        for clause in clauses:
            if clause.clause_type != ClauseType.OTHER:
                assessment = self._assess_clause_risk(clause)
                risk_assessments.append(assessment)
        
        # Step 4: Calculate overall risk
        overall_score, overall_level = self._calculate_overall_risk(risk_assessments)
        
        # Step 5: Generate executive summary
        executive_summary = self._generate_executive_summary(
            metadata, clauses, risk_assessments, overall_score
        )
        
        # Step 6: Identify key concerns
        key_concerns = self._identify_key_concerns(risk_assessments)
        
        # Step 7: Generate negotiation points
        negotiation_points = self._generate_negotiation_points(risk_assessments)
        
        return ContractAnalysis(
            metadata=metadata,
            clauses=clauses,
            risk_assessments=risk_assessments,
            overall_risk_score=overall_score,
            overall_risk_level=overall_level,
            executive_summary=executive_summary,
            key_concerns=key_concerns,
            negotiation_points=negotiation_points,
            analysis_timestamp=datetime.now().isoformat()
        )
    
    def _extract_metadata(self, contract_text: str) -> ContractMetadata:
        """Extract basic contract metadata."""
        
        prompt = f"""Analyze this contract and extract the following metadata.
Return ONLY a JSON object with these fields (use null if not found):

{{
    "contract_type": "type of contract (e.g., Service Agreement, NDA, Employment)",
    "parties": ["list", "of", "party", "names"],
    "effective_date": "YYYY-MM-DD or null",
    "expiration_date": "YYYY-MM-DD or null",
    "total_value": "contract value if mentioned or null",
    "governing_law": "jurisdiction/governing law or null",
    "jurisdiction": "dispute jurisdiction or null"
}}

CONTRACT TEXT:
{contract_text[:8000]}

Return ONLY the JSON object, no other text:"""

        response = self.llm.generate(prompt)
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return ContractMetadata(
                    contract_type=data.get("contract_type", "Unknown"),
                    parties=data.get("parties", []),
                    effective_date=data.get("effective_date"),
                    expiration_date=data.get("expiration_date"),
                    total_value=data.get("total_value"),
                    governing_law=data.get("governing_law"),
                    jurisdiction=data.get("jurisdiction")
                )
        except json.JSONDecodeError:
            pass
        
        return ContractMetadata(
            contract_type="Unknown",
            parties=[],
            effective_date=None,
            expiration_date=None,
            total_value=None,
            governing_law=None,
            jurisdiction=None
        )
    
    def _extract_clauses(self, contract_text: str) -> List[ExtractedClause]:
        """Extract and categorize contract clauses."""
        
        clause_types_str = ", ".join([ct.value for ct in ClauseType])
        
        prompt = f"""Analyze this contract and identify all clauses.
For each clause, extract:
1. The clause type (from: {clause_types_str})
2. The clause title as it appears in the contract
3. The full clause text
4. Section reference if present (e.g., "Section 5.2")

Return a JSON array of clauses:
[
    {{
        "clause_type": "one of the types listed above",
        "title": "clause title",
        "text": "full clause text",
        "section_reference": "section number or null"
    }}
]

CONTRACT TEXT:
{contract_text[:12000]}

Return ONLY the JSON array, no other text:"""

        response = self.llm.generate(prompt)
        
        clauses = []
        try:
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                for item in data:
                    try:
                        clause_type = ClauseType(item.get("clause_type", "other"))
                    except ValueError:
                        clause_type = ClauseType.OTHER
                    
                    clauses.append(ExtractedClause(
                        clause_type=clause_type,
                        title=item.get("title", ""),
                        text=item.get("text", ""),
                        section_reference=item.get("section_reference"),
                        confidence=0.85
                    ))
        except json.JSONDecodeError:
            pass
        
        return clauses
    
    def _assess_clause_risk(self, clause: ExtractedClause) -> RiskAssessment:
        """Assess risk for a specific clause."""
        
        # Get benchmark data for this clause type
        benchmark = MARKET_BENCHMARKS.get(clause.clause_type, {})
        market_standard = benchmark.get("market_standard", "No specific benchmark available.")
        known_red_flags = benchmark.get("red_flags", [])
        best_practice = benchmark.get("best_practice", "Follow industry standards.")
        
        prompt = f"""You are a contract risk analyst. Assess this clause against market standards.

CLAUSE TYPE: {clause.clause_type.value}
CLAUSE TITLE: {clause.title}
CLAUSE TEXT:
{clause.text}

MARKET BENCHMARK:
{market_standard}

KNOWN RED FLAGS TO CHECK:
{json.dumps(known_red_flags, indent=2)}

BEST PRACTICE:
{best_practice}

Analyze and return ONLY a JSON object:
{{
    "risk_level": "critical/high/medium/low/standard",
    "risk_score": 1-10 (10 = highest risk),
    "findings": ["list of specific findings from the clause"],
    "reasoning": "detailed explanation of risk assessment",
    "red_flags_found": ["list of red flags present in this clause"],
    "recommendations": ["specific recommendations to improve this clause"]
}}

Return ONLY the JSON object:"""

        response = self.llm.generate(prompt)
        
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                try:
                    risk_level = RiskLevel(data.get("risk_level", "medium"))
                except ValueError:
                    risk_level = RiskLevel.MEDIUM
                
                return RiskAssessment(
                    clause_type=clause.clause_type,
                    risk_level=risk_level,
                    risk_score=min(10, max(1, data.get("risk_score", 5))),
                    findings=data.get("findings", []),
                    reasoning=data.get("reasoning", ""),
                    market_comparison=market_standard,
                    recommendations=data.get("recommendations", []),
                    red_flags=data.get("red_flags_found", [])
                )
        except json.JSONDecodeError:
            pass
        
        # Default assessment if parsing fails
        return RiskAssessment(
            clause_type=clause.clause_type,
            risk_level=RiskLevel.MEDIUM,
            risk_score=5,
            findings=["Unable to fully analyze clause"],
            reasoning="Analysis incomplete",
            market_comparison=market_standard,
            recommendations=["Manual review recommended"],
            red_flags=[]
        )
    
    def _calculate_overall_risk(
        self, assessments: List[RiskAssessment]
    ) -> Tuple[float, RiskLevel]:
        """Calculate overall contract risk."""
        
        if not assessments:
            return 5.0, RiskLevel.MEDIUM
        
        # Weighted average (critical clauses weighted more)
        weights = {
            RiskLevel.CRITICAL: 2.0,
            RiskLevel.HIGH: 1.5,
            RiskLevel.MEDIUM: 1.0,
            RiskLevel.LOW: 0.75,
            RiskLevel.STANDARD: 0.5
        }
        
        weighted_sum = 0
        total_weight = 0
        
        for assessment in assessments:
            weight = weights.get(assessment.risk_level, 1.0)
            weighted_sum += assessment.risk_score * weight
            total_weight += weight
        
        overall_score = weighted_sum / total_weight if total_weight > 0 else 5.0
        
        # Determine overall level
        if overall_score >= 8:
            overall_level = RiskLevel.CRITICAL
        elif overall_score >= 6:
            overall_level = RiskLevel.HIGH
        elif overall_score >= 4:
            overall_level = RiskLevel.MEDIUM
        elif overall_score >= 2:
            overall_level = RiskLevel.LOW
        else:
            overall_level = RiskLevel.STANDARD
        
        return round(overall_score, 1), overall_level
    
    def _generate_executive_summary(
        self, 
        metadata: ContractMetadata,
        clauses: List[ExtractedClause],
        assessments: List[RiskAssessment],
        overall_score: float
    ) -> str:
        """Generate executive summary."""
        
        high_risk_clauses = [a for a in assessments if a.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]]
        total_red_flags = sum(len(a.red_flags) for a in assessments)
        
        prompt = f"""Generate a concise executive summary (3-4 paragraphs) for this contract analysis.

CONTRACT TYPE: {metadata.contract_type}
PARTIES: {', '.join(metadata.parties)}
EFFECTIVE DATE: {metadata.effective_date or 'Not specified'}

ANALYSIS RESULTS:
- Total clauses analyzed: {len(clauses)}
- Overall risk score: {overall_score}/10
- High/Critical risk clauses: {len(high_risk_clauses)}
- Red flags identified: {total_red_flags}

HIGH RISK AREAS:
{json.dumps([{"type": a.clause_type.value, "score": a.risk_score, "flags": a.red_flags} for a in high_risk_clauses], indent=2)}

Write a professional executive summary that:
1. States the contract type and parties
2. Summarizes the overall risk profile
3. Highlights the most critical concerns
4. Provides a recommendation (proceed/negotiate/reject)

Be direct and specific. This is for a legal/business audience."""

        return self.llm.generate(prompt)
    
    def _identify_key_concerns(self, assessments: List[RiskAssessment]) -> List[str]:
        """Identify top concerns from all assessments."""
        concerns = []
        
        for assessment in assessments:
            if assessment.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                for flag in assessment.red_flags:
                    concerns.append(f"[{assessment.clause_type.value.upper()}] {flag}")
        
        return concerns[:10]  # Top 10 concerns
    
    def _generate_negotiation_points(
        self, assessments: List[RiskAssessment]
    ) -> List[Dict]:
        """Generate prioritized negotiation points."""
        
        points = []
        
        # Sort by risk score descending
        sorted_assessments = sorted(
            assessments, 
            key=lambda x: x.risk_score, 
            reverse=True
        )
        
        for assessment in sorted_assessments[:5]:  # Top 5 priority items
            if assessment.recommendations:
                points.append({
                    "priority": len(points) + 1,
                    "clause": assessment.clause_type.value,
                    "risk_score": assessment.risk_score,
                    "issue": assessment.findings[0] if assessment.findings else "Risk identified",
                    "recommendation": assessment.recommendations[0],
                    "suggested_language": self._suggest_alternative_language(assessment)
                })
        
        return points
    
    def _suggest_alternative_language(self, assessment: RiskAssessment) -> str:
        """Generate suggested alternative contract language."""
        
        benchmark = MARKET_BENCHMARKS.get(assessment.clause_type, {})
        best_practice = benchmark.get("best_practice", "")
        
        if not assessment.recommendations or not best_practice:
            return "Consult with legal counsel for specific language."
        
        prompt = f"""Based on this contract clause issue, suggest specific alternative language.

CLAUSE TYPE: {assessment.clause_type.value}
CURRENT ISSUE: {assessment.findings[0] if assessment.findings else 'Risk identified'}
BEST PRACTICE: {best_practice}
RECOMMENDATION: {assessment.recommendations[0]}

Provide 2-3 sentences of suggested contract language that addresses the issue.
Be specific and use standard legal terminology.
Return ONLY the suggested language, nothing else."""

        return self.llm.generate(prompt, temperature=0.3)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_risk_badge(risk_level: RiskLevel) -> str:
    """Return emoji badge for risk level."""
    badges = {
        RiskLevel.CRITICAL: "🔴 CRITICAL",
        RiskLevel.HIGH: "🟠 HIGH",
        RiskLevel.MEDIUM: "🟡 MEDIUM",
        RiskLevel.LOW: "🟢 LOW",
        RiskLevel.STANDARD: "✅ STANDARD"
    }
    return badges.get(risk_level, "⚪ UNKNOWN")


def analysis_to_dict(analysis: ContractAnalysis) -> Dict:
    """Convert ContractAnalysis to dictionary for JSON export."""
    return {
        "metadata": {
            "contract_type": analysis.metadata.contract_type,
            "parties": analysis.metadata.parties,
            "effective_date": analysis.metadata.effective_date,
            "expiration_date": analysis.metadata.expiration_date,
            "total_value": analysis.metadata.total_value,
            "governing_law": analysis.metadata.governing_law,
            "jurisdiction": analysis.metadata.jurisdiction
        },
        "clauses": [
            {
                "type": c.clause_type.value,
                "title": c.title,
                "text": c.text[:500] + "..." if len(c.text) > 500 else c.text,
                "section": c.section_reference
            }
            for c in analysis.clauses
        ],
        "risk_assessments": [
            {
                "clause_type": a.clause_type.value,
                "risk_level": a.risk_level.value,
                "risk_score": a.risk_score,
                "findings": a.findings,
                "reasoning": a.reasoning,
                "red_flags": a.red_flags,
                "recommendations": a.recommendations
            }
            for a in analysis.risk_assessments
        ],
        "overall_risk_score": analysis.overall_risk_score,
        "overall_risk_level": analysis.overall_risk_level.value,
        "executive_summary": analysis.executive_summary,
        "key_concerns": analysis.key_concerns,
        "negotiation_points": analysis.negotiation_points,
        "analysis_timestamp": analysis.analysis_timestamp
    }
