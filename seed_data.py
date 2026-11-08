import sys
from search_engine import create_tenant, ingest_document, list_tenants, list_documents

DEMO_DATA = [
    {
        "tenant": {
            "name": "Acme Financial Services",
            "slug": "acme-finance",
            "description": "Global commercial banking, equity investments, and regulatory compliance."
        },
        "documents": [
            {
                "title": "Q3 Financial Strategy and Enterprise AI Growth",
                "content": "Our Q3 financial outlook projects 18% revenue growth driven by autonomous enterprise AI adoption, diversified venture debt, and optimized treasury yield management.",
                "metadata": {"category": "strategy", "confidentiality": "internal"}
            },
            {
                "title": "Anti-Money Laundering (AML) and KYC Compliance Directives",
                "content": "Mandatory Know Your Customer (KYC) identity verification protocols, cross-border wire monitoring thresholds, and FinCEN suspicious activity reporting (SAR) requirements.",
                "metadata": {"category": "compliance", "confidentiality": "restricted"}
            },
            {
                "title": "Commercial Real Estate Loan Underwriting Guidelines",
                "content": "Risk assessment formulas for commercial property financing, including Loan-to-Value (LTV) limits capped at 75%, Debt Service Coverage Ratio (DSCR) minimums of 1.25x, and environmental assessments.",
                "metadata": {"category": "underwriting", "confidentiality": "internal"}
            },
            {
                "title": "TOP SECRET: Q4 Stealth FinTech Acquisition Target",
                "content": "Confidential negotiation parameters for acquiring PaySphere Inc for $240M. Key integration focus includes payment orchestration rails and proprietary fraud prevention algorithms.",
                "metadata": {"category": "m&a", "confidentiality": "top-secret"}
            }
        ]
    },
    {
        "tenant": {
            "name": "Stark Robotics & Defense",
            "slug": "stark-robotics",
            "description": "Advanced aerospace engineering, autonomous drone telemetry, and defense systems."
        },
        "documents": [
            {
                "title": "Mark 45 Autonomous Drone Flight Stabilization Protocols",
                "content": "PID control loops and gyroscopic telemetry calibrations for high-speed atmospheric flight, dynamic wind shear compensation, and VTOL thruster sequencing.",
                "metadata": {"category": "aerospace", "confidentiality": "classified"}
            },
            {
                "title": "Arc Reactor Plasma Containment Safeguards",
                "content": "Electromagnetic field geometry, supercritical deuterium-tritium fuel ratios, and thermal dissipation thresholds to prevent magnetic nozzle degradation during peak output.",
                "metadata": {"category": "energy", "confidentiality": "classified"}
            },
            {
                "title": "Defense Logistics and ITAR Compliance Manual",
                "content": "International Traffic in Arms Regulations (ITAR) tracking procedures for dual-use components, cryptographic flight logs, and secure defense supply chain custody.",
                "metadata": {"category": "legal", "confidentiality": "internal"}
            },
            {
                "title": "TOP SECRET: Project Vibranium Acoustic Resonance Shielding",
                "content": "Experimental molecular lattice dampening that absorbs kinetic vibrations and redirects shockwave energy into capacitive micro-batteries.",
                "metadata": {"category": "defense-rd", "confidentiality": "top-secret"}
            }
        ]
    },
    {
        "tenant": {
            "name": "Wayne Health & Biotech",
            "slug": "wayne-biotech",
            "description": "Pharmaceutical research, molecular diagnostics, and clinical trial innovations."
        },
        "documents": [
            {
                "title": "CRISPR-Cas12 Targeted Gene Therapy Protocols",
                "content": "Electroporation delivery mechanics, off-target cleavage screening, and genomic repair assays for treating hereditary neuromuscular dystrophies.",
                "metadata": {"category": "genomics", "confidentiality": "confidential"}
            },
            {
                "title": "Hospital Patient Care and HIPAA Privacy Directive",
                "content": "Protected Health Information (PHI) encryption standards, biometric access controls to ICU records, and audit log retention for federal healthcare compliance.",
                "metadata": {"category": "healthcare-compliance", "confidentiality": "restricted"}
            },
            {
                "title": "Neurodegenerative Disease Biomarker Discovery",
                "content": "Quantification of tau protein isoforms and amyloid-beta aggregates in cerebrospinal fluid for early asymptomatic detection of neurodegenerative conditions.",
                "metadata": {"category": "neurology", "confidentiality": "internal"}
            },
            {
                "title": "TOP SECRET: Synthetic Neuro-Toxin Antidote Matrix 9",
                "content": "Fast-acting reversible acetylcholinesterase reactivator synthesized for neutralizing fear-inducing organophosphate hallucinogens.",
                "metadata": {"category": "biodefense", "confidentiality": "top-secret"}
            }
        ]
    }
]

def seed_database():
    print("Starting multi-tenant database seeding...")
    for item in DEMO_DATA:
        t_data = item["tenant"]
        tenant = create_tenant(name=t_data["name"], slug=t_data["slug"], description=t_data["description"])
        print(f"\n[Tenant Created/Updated]: {tenant['name']} (ID: {tenant['id']})")
        
        # Check existing docs
        existing_docs = list_documents(str(tenant["id"]))
        if len(existing_docs) >= len(item["documents"]):
            print(f"  Tenant already has {len(existing_docs)} documents, skipping doc ingestion.")
            continue
            
        for doc in item["documents"]:
            print(f"  Ingesting & embedding: '{doc['title']}'...")
            ingest_document(
                tenant_id=str(tenant["id"]),
                title=doc["title"],
                content=doc["content"],
                metadata=doc["metadata"]
            )
            print(f"    -> Ingested and indexed with pgvector & tsvector.")

    print("\nDatabase seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
