import sys
from search_engine import create_tenant, ingest_document, list_tenants, list_documents

EXPANDED_DEMO_DATA = [
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
                "title": "TOP SECRET: Q4 Stealth FinTech Acquisition Target PaySphere",
                "content": "Confidential negotiation parameters for acquiring PaySphere Inc for $240M. Key integration focus includes payment orchestration rails and proprietary fraud prevention algorithms.",
                "metadata": {"category": "m&a", "confidentiality": "top-secret"}
            },
            {
                "title": "High-Frequency Algorithmic Order Routing Safeguards",
                "content": "Latency arbitrage controls and circuit breakers for automated market maker algorithms operating across NYSE and NASDAQ order books to prevent flash crashes.",
                "metadata": {"category": "trading", "confidentiality": "restricted"}
            },
            {
                "title": "Corporate Treasury Digital Asset Allocation Policy",
                "content": "Custodial storage protocols for institutional crypto assets, cold-storage multi-signature quorum rules, and SEC reporting guidelines for digital holdings.",
                "metadata": {"category": "treasury", "confidentiality": "internal"}
            },
            {
                "title": "Cross-Border SWIFT Settlement and ISO 20022 Migration",
                "content": "Technical specifications for transition to ISO 20022 XML messaging standards for real-time gross settlement (RTGS) systems and correspondent banking clearance.",
                "metadata": {"category": "infrastructure", "confidentiality": "internal"}
            },
            {
                "title": "ESG Investment Framework and Green Bond Verification",
                "content": "Environmental, Social, and Governance (ESG) scoring methodologies, carbon accounting metrics for corporate borrowers, and European green bond standard alignment.",
                "metadata": {"category": "sustainability", "confidentiality": "public"}
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
            },
            {
                "title": "Hypersonic Ramjet Boundary Layer Thermal Mitigation",
                "content": "Active transpiration cooling using liquid methane through micro-porous carbon-carbon composite leading edges at Mach 6.5 velocities.",
                "metadata": {"category": "propulsion", "confidentiality": "classified"}
            },
            {
                "title": "JARVIS Sub-Routine Tactical Telemetry Architecture",
                "content": "Decentralized sensor fusion network running on military edge compute clusters, aggregating LIDAR, optical, and radar telemetry with sub-5ms latency.",
                "metadata": {"category": "ai-systems", "confidentiality": "classified"}
            },
            {
                "title": "Exoskeleton Hydraulic Actuator Torque Response Profiling",
                "content": "Brushless DC servomotor torque-to-weight ratios and harmonic drive gear reductions for third-generation powered infantry load-bearing suits.",
                "metadata": {"category": "biomechanics", "confidentiality": "internal"}
            },
            {
                "title": "Space-to-Ground Directed Energy Optical Calibrations",
                "content": "Adaptive optics mirror deformation matrices for atmospheric wavefront distortion correction in orbital optical communications arrays.",
                "metadata": {"category": "optics", "confidentiality": "top-secret"}
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
            },
            {
                "title": "Nanoparticle Blood-Brain Barrier Transmigration Studies",
                "content": "Lipid nanoparticle surface functionalization with transferrin receptor ligands to facilitate targeted central nervous system chemotherapy delivery.",
                "metadata": {"category": "oncology", "confidentiality": "confidential"}
            },
            {
                "title": "mRNA Vaccine Cold-Chain Lyophilization Protocols",
                "content": "Thermostable freeze-drying preservation techniques for synthetic messenger RNA strands eliminating requirements for minus-80 Celsius ultra-cold storage.",
                "metadata": {"category": "formulation", "confidentiality": "internal"}
            },
            {
                "title": "Bioethics Committee Guidelines on Somatic Cell Editing",
                "content": "Institutional Review Board (IRB) moral governance, patient informed consent criteria, and long-term generational tracking mandates for gene therapy trials.",
                "metadata": {"category": "ethics", "confidentiality": "public"}
            },
            {
                "title": "Clinical Trial Phase III Statistical Power Analysis for Compound W-42",
                "content": "Double-blind placebo-controlled efficacy endpoints, Kaplan-Meier survival curve projections, and adverse event hazard ratios for autoimmune therapies.",
                "metadata": {"category": "clinical-trials", "confidentiality": "restricted"}
            }
        ]
    },
    {
        "tenant": {
            "name": "Cyberdyne Systems",
            "slug": "cyberdyne-ai",
            "description": "Neural net coprocessors, autonomous edge robotics, and factory automation."
        },
        "documents": [
            {
                "title": "Neural Net Coprocessor Architecture Specification",
                "content": "Instruction set architecture (ISA) for custom 4-bit quantized matrix multiplication units executing transformer attention blocks at 120 TOPS per watt.",
                "metadata": {"category": "hardware", "confidentiality": "confidential"}
            },
            {
                "title": "Autonomous Factory Robot Swarm Synchronization",
                "content": "Ultra-wideband (UWB) spatial localization and collision-avoidance trajectory planning for 250 automated mobile robots (AMRs) in warehouse assembly lines.",
                "metadata": {"category": "robotics", "confidentiality": "internal"}
            },
            {
                "title": "Reinforcement Learning from Human Feedback (RLHF) Safety Audits",
                "content": "Reward modeling safeguards, adversarial red-teaming prompts, and containment constraints preventing autonomous systems from deviating from operator intent.",
                "metadata": {"category": "ai-safety", "confidentiality": "restricted"}
            },
            {
                "title": "TOP SECRET: Project Skynet Sub-Surface Defense Grid Architecture",
                "content": "Automated nuclear silo early warning telemetry and hardened satellite relay nodes with automated retaliatory launch triggers under zero human latency.",
                "metadata": {"category": "defense", "confidentiality": "top-secret"}
            },
            {
                "title": "T-Series Titanium-Columbium Alloy Endoskeleton Specifications",
                "content": "Hydraulic pressure tolerances, ballistic deflection geometry, and micro-servo motor placements for bipedal heavy industrial work units.",
                "metadata": {"category": "metallurgy", "confidentiality": "top-secret"}
            },
            {
                "title": "Predictive Industrial Maintenance Acoustic Sensor Pipeline",
                "content": "FFT audio anomaly detection models trained on factory spindle vibrations, detecting ball-bearing micro-fractures 72 hours prior to physical failure.",
                "metadata": {"category": "iot", "confidentiality": "internal"}
            }
        ]
    },
    {
        "tenant": {
            "name": "OmniLogistics Global Supply",
            "slug": "omni-logistics",
            "description": "Intermodal maritime freight, automated container terminals, and cold-chain logistics."
        },
        "documents": [
            {
                "title": "Trans-Pacific Maritime Route Optimization via Weather Telemetry",
                "content": "Geostationary oceanic wave height forecasts and hydrodynamic hull resistance modeling to reduce heavy fuel oil (HFO) consumption by 14% on container lanes.",
                "metadata": {"category": "maritime", "confidentiality": "internal"}
            },
            {
                "title": "Automated Port Container Crane Stacking Algorithm",
                "content": "Integer linear programming heuristic for minimizing redundant container relocations in deep-water automated terminal yards.",
                "metadata": {"category": "port-ops", "confidentiality": "internal"}
            },
            {
                "title": "Pharmaceutical Cold-Chain IoT Temperature Audit Directive",
                "content": "Tamper-evident Bluetooth Low Energy (BLE) temperature logger compliance, continuous minus-20C monitoring, and FDA 21 CFR Part 11 electronic records.",
                "metadata": {"category": "compliance", "confidentiality": "restricted"}
            },
            {
                "title": "TOP SECRET: Autonomous Submersible Cargo Glider Fleet Protocol",
                "content": "Unmanned underwater vehicles (UUV) operating along oceanic thermoclines for clandestine intercontinental transport of high-value rare earth minerals.",
                "metadata": {"category": "clandestine-logistics", "confidentiality": "top-secret"}
            },
            {
                "title": "Last-Mile Delivery EV Fleet Battery Thermal Management",
                "content": "Active liquid thermal loop optimization for electric delivery vans during sub-zero winter routes, maximizing regenerative braking recovery and range.",
                "metadata": {"category": "fleet", "confidentiality": "internal"}
            },
            {
                "title": "Customs Tariff Classification (HS Code) Automated Validation",
                "content": "Machine learning cross-referencing of manifest cargo declarations against World Customs Organization (WCO) 6-digit Harmonized System codes.",
                "metadata": {"category": "trade", "confidentiality": "public"}
            }
        ]
    }
]

def seed_database():
    print("Starting expanded multi-tenant database seeding...")
    for item in EXPANDED_DEMO_DATA:
        t_data = item["tenant"]
        tenant = create_tenant(name=t_data["name"], slug=t_data["slug"], description=t_data["description"])
        print(f"\n[Tenant]: {tenant['name']} (ID: {tenant['id']})")
        
        # Check existing docs by title to avoid duplicates
        existing_docs = list_documents(str(tenant["id"]))
        existing_titles = {d["title"] for d in existing_docs}
        
        for doc in item["documents"]:
            if doc["title"] in existing_titles:
                print(f"  • Existing: '{doc['title']}' (skipping)")
                continue
            print(f"  + Ingesting & embedding: '{doc['title']}'...")
            ingest_document(
                tenant_id=str(tenant["id"]),
                title=doc["title"],
                content=doc["content"],
                metadata=doc["metadata"]
            )
            print(f"    -> Successfully indexed.")

    print("\nDatabase successfully populated with expanded multi-tenant data!")

if __name__ == "__main__":
    seed_database()
