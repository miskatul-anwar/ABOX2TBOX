# Milestone 1: Multi-Domain Benchmark Datasets Generation Report

**Author:** `worker_m1_gen2` (teamwork_preview_worker)  
**Date:** 2026-10-15  
**Milestone:** M1 (Multi-Domain Benchmark Datasets Generation)  
**Project:** ABox2TBox Induction Pipeline Generalization & Hardening  

---

## 1. Executive Summary

Milestone 1 required the creation of four distinct, rich, and syntactically valid W3C Turtle benchmark knowledge graphs (`ABox.ttl`) across diverse real-world domains:
1. **E-Commerce / Retail Catalog** (`input/ecommerce_abox.ttl`)
2. **Hospital / Biomedical Records** (`input/hospital_abox.ttl`)
3. **Enterprise Organization** (`input/enterprise_abox.ttl`)
4. **Financial / Banking Systems** (`input/banking_abox.ttl`)

Each dataset was engineered from scratch to rigorously stress-test all phases of the neuro-symbolic ontology induction pipeline—including characteristic set profiling, open-vocabulary concept synthesis, statistical subsumption and disjointness candidate mining, tournament adjudication, graph-theoretic repair (Tarjan SCC collapsing, MFAS cycle elimination, transitive reduction), and consistency enforcement.

All four benchmark datasets strictly satisfy all volume, ontological, taxonomic, and structural challenge criteria.

---

## 2. Benchmark Datasets Overview & Verification Matrix

| Domain Benchmark | File Path | Prefix & Namespace | Triples | Explicit Classes | Total Subjects | Untyped Clusters | Taxonomy Depth (Hasse) | Disjointness (DVC Pre/Post) | Property Algebraic Metrics (Trans/Sym/Func) |
|---|---|---|---|---|---|---|---|---|---|
| **E-Commerce / Retail** | `input/ecommerce_abox.ttl` | `: <http://example.org/ecommerce#>` | 733 | 32 | 148 | 3 (24 insts) | 5 levels | 8 / 0 | 1.00 / 1.00 / 1.00 |
| **Hospital / Biomedical** | `input/hospital_abox.ttl` | `: <http://example.org/hospital#>` | 576 | 25 | 133 | 3 (24 insts) | 5 levels | 3 / 0 | 1.00 / 1.00 / 1.00 |
| **Enterprise Organization** | `input/enterprise_abox.ttl` | `: <http://example.org/enterprise#>` | 590 | 25 | 130 | 3 (24 insts) | 4 levels | 5 / 0 | 1.00 / 1.00 / 1.00 |
| **Financial / Banking** | `input/banking_abox.ttl` | `: <http://example.org/banking#>` | 704 | 26 | 149 | 3 (24 insts) | 4 levels | 8 / 0 | 1.00 / 1.00 / 1.00 |

*All datasets strictly satisfy the $500 \le N \le 1,500$ triple requirement and the $\ge 15$ class threshold.*

---

## 3. Detailed Domain Specifications

### 3.1 Domain 1: E-Commerce / Retail (`input/ecommerce_abox.ttl`)
- **Prefix:** `@prefix : <http://example.org/ecommerce#> .`
- **Volume:** 733 triples, 148 subjects, 32 declared classes.
- **Taxonomic Class Hierarchies:**
  - *Customer Chain (5 levels):*  
    `PlatinumVIPCustomer` (3) $\sqsubseteq$ `VIPCustomer` (8) $\sqsubseteq$ `RegisteredCustomer` (16) $\sqsubseteq$ `Customer` (24) $\sqsubseteq$ `Party` (35).
  - *Physical Product Chain (4 levels):*  
    `Smartphone` (6) $\sqsubseteq$ `ConsumerElectronics` (12) $\sqsubseteq$ `PhysicalProduct` (24) $\sqsubseteq$ `Product` (40).
  - *Apparel Chain (4 levels):*  
    `Footwear` (6) $\sqsubseteq$ `Apparel` (12) $\sqsubseteq$ `PhysicalProduct` (24) $\sqsubseteq$ `Product` (40).
  - *Digital Product Chain (4 levels):*  
    `MobileApp` (4) $\sqsubseteq$ `SoftwareProduct` (8) $\sqsubseteq$ `DigitalProduct` (16) $\sqsubseteq$ `Product` (40).
- **Disjointness Boundary:**
  - Disjoint pair: `PhysicalProduct` vs `DigitalProduct`.
  - Injected conflict: `:noisy_hybrid_product` asserted with `a :Smartphone, :EBook .`
  - Pre-repair violations: `DVC_pre = 8`, Post-repair violations: `DVC_post = 0`.
- **Untyped Entity Clusters (3 clusters, 8 entities each):**
  1. *Shipment Tracking:* `:shipment_01..08`, incoming `:orderHasShipment`, outgoing `[:shippingCarrier, :shippingStatus, :trackingNumber]`. Synthesizes `:ShippingCarrier`.
  2. *Promotion / Discount:* `:promo_01..08`, incoming `:appliedPromotion`, outgoing `[:couponCode, :discountPercentage, :promotionTitle]`. Synthesizes `:PromotionCoupon`.
  3. *Technical Specification:* `:spec_01..08`, incoming `:hasSpecification`, outgoing `[:dimensionMeasurement, :technicalWeight, :warrantyPeriod]`. Synthesizes `:DimensionMeasurement`.
- **Property Characteristics:**
  - Transitive: `:isSubCategoryOf` ($\rho_{\text{trans}} = 1.000$).
  - Symmetric: `:frequentlyBoughtTogether` ($\rho_{\text{sym}} = 1.000$).
  - Functional: `:primaryContactCustomer` ($\rho_{\text{func}} = 1.000$).
  - InverseFunctional: `:trackingCode` ($\rho_{\text{invfunc}} = 1.000$).
  - Empirical Noise: Near-transitive `:crossPromotedWith` ($\rho_{\text{trans}} = 0.50$), Near-symmetric `:recommendedWith` ($\rho_{\text{sym}} = 0.67$).
- **Structural Challenge Noise:**
  - Tarjan SCC: Mutual 2-cycle between `:Buyer` and `:Purchaser` with 100% shared instances (10 entities).
  - MFAS DAG cycle: Directed 3-cycle `:ReviewTierA` $\to$ `:ReviewTierB` $\to$ `:ReviewTierC` $\to$ `:ReviewTierA`.
  - Redundant Transitive Edge: Asserted `:Smartphone` $\to$ `:Product` reduced by Transitive Reduction to minimal Hasse diagram.

---

### 3.2 Domain 2: Hospital / Biomedical (`input/hospital_abox.ttl`)
- **Prefix:** `@prefix : <http://example.org/hospital#> .`
- **Volume:** 576 triples, 133 subjects, 25 declared classes.
- **Taxonomic Class Hierarchies:**
  - *Physician Chain (5 levels):*  
    `Cardiologist` (4) $\sqsubseteq$ `SpecialistPhysician` (8) $\sqsubseteq$ `Physician` (14) $\sqsubseteq$ `HealthcareStaff` (22) $\sqsubseteq$ `Person` (44).
  - *Inpatient Chain (4 levels):*  
    `ICUPatient` (5) $\sqsubseteq$ `Inpatient` (10) $\sqsubseteq$ `Patient` (22) $\sqsubseteq$ `Person` (44).
  - *Outpatient Chain (4 levels):*  
    `EmergencyPatient` (6) $\sqsubseteq$ `Outpatient` (12) $\sqsubseteq$ `Patient` (22) $\sqsubseteq$ `Person` (44).
- **Disjointness Boundary:**
  - Disjoint pair: `Inpatient` vs `Outpatient`.
  - Injected conflict: `:noisy_patient_transfer` asserted with `a :ICUPatient, :ClinicPatient .`
  - Pre-repair violations: `DVC_pre = 3`, Post-repair violations: `DVC_post = 0`.
- **Untyped Entity Clusters (3 clusters, 8 entities each):**
  1. *Dosage Administration:* `:dosage_01..08`, incoming `:treatmentPrescriptionDosage`, outgoing `[:dosageQuantity, :intakeFrequency, :routeAdministration]`. Synthesizes `:DosageQuantity`.
  2. *Laboratory Result:* `:lab_res_01..08`, incoming `:patientLabResult`, outgoing `[:labMeasurementValue, :referenceRangeNormal, :testMetricName]`. Synthesizes `:LabMeasurement`.
  3. *Insurance Policy:* `:policy_01..08`, incoming `:patientInsurancePolicy`, outgoing `[:insuranceProviderName, :policyContractNumber, :policyCoverageLimit]`. Synthesizes `:PolicyInsurance`.
- **Property Characteristics:**
  - Transitive: `:subDepartmentOf` ($\rho_{\text{trans}} = 1.000$).
  - Symmetric: `:consultsWith` ($\rho_{\text{sym}} = 1.000$).
  - Functional: `:assignedAttendingDoctor` ($\rho_{\text{func}} = 1.000$).
  - InverseFunctional: `:patientLabResult` ($\rho_{\text{invfunc}} = 1.000$).
  - Empirical Noise: Near-transitive `:transferredToWard` ($\rho_{\text{trans}} = 0.50$), Near-symmetric `:referredPatientTo` ($\rho_{\text{sym}} = 0.67$).
- **Structural Challenge Noise:**
  - Tarjan SCC: Mutual 2-cycle between `:LicensedPhysician` and `:MedicalDoctor` with 100% shared instances (10 entities).
  - MFAS DAG cycle: Directed 3-cycle `:TriageLevelA` $\to$ `:TriageLevelB` $\to$ `:TriageLevelC` $\to$ `:TriageLevelA`.
  - Redundant Transitive Edge: Asserted `:ICUPatient` $\to$ `:Person` reduced by Transitive Reduction to minimal Hasse diagram.

---

### 3.3 Domain 3: Enterprise Organization (`input/enterprise_abox.ttl`)
- **Prefix:** `@prefix : <http://example.org/enterprise#> .`
- **Volume:** 590 triples, 130 subjects, 25 declared classes.
- **Taxonomic Class Hierarchies:**
  - *Employee Chain (5 levels):*  
    `ExecutiveDirector` (4) $\sqsubseteq$ `SeniorFullTimeEmployee` (10) $\sqsubseteq$ `FullTimeEmployee` (18) $\sqsubseteq$ `CorporateEmployee` (30) $\sqsubseteq$ `Person` (42).
  - *Contractor Chain (4 levels):*  
    `ExternalConsultant` (6) $\sqsubseteq$ `ContractWorker` (12) $\sqsubseteq$ `CorporateEmployee` (30) $\sqsubseteq$ `Person` (42).
  - *Computing Asset Chain (4 levels):*  
    `ServerAsset` (6) $\sqsubseteq$ `ComputingDevice` (12) $\sqsubseteq$ `HardwareAsset` (12) $\sqsubseteq$ `EnterpriseAsset` (24).
- **Disjointness Boundary:**
  - Disjoint pair: `FullTimeEmployee` vs `ContractWorker`.
  - Injected conflict: `:noisy_corporate_worker` asserted with `a :ExecutiveDirector, :ExternalConsultant .`
  - Pre-repair violations: `DVC_pre = 5`, Post-repair violations: `DVC_post = 0`.
- **Untyped Entity Clusters (3 clusters, 8 entities each):**
  1. *Expense Report:* `:expense_01..08`, incoming `:submittedExpenseReport`, outgoing `[:approvalStatusCode, :expenseCategoryCode, :reimbursementAmount]`. Synthesizes `:CodeExpense`.
  2. *Software License:* `:lic_01..08`, incoming `:assignedSoftwareLicense`, outgoing `[:expirationDatePeriod, :licenseKeyIdentifier, :vendorEntityName]`. Synthesizes `:LicenseExpiration`.
  3. *Performance Review:* `:perf_rev_01..08`, incoming `:employeePerformanceReview`, outgoing `[:performanceEvaluationPeriod, :reviewRatingScore, :reviewerFeedbackNotes]`. Synthesizes `:PerformanceReview`.
- **Property Characteristics:**
  - Transitive: `:subDivisionOf` ($\rho_{\text{trans}} = 1.000$).
  - Symmetric: `:collaboratesWith` ($\rho_{\text{sym}} = 1.000$).
  - Functional: `:assignedProjectLead` ($\rho_{\text{func}} = 1.000$).
  - InverseFunctional: `:submittedExpenseReport` ($\rho_{\text{invfunc}} = 1.000$).
  - Empirical Noise: Near-transitive `:advises` ($\rho_{\text{trans}} = 0.50$), Near-symmetric `:mentors` ($\rho_{\text{sym}} = 0.67$).
- **Structural Challenge Noise:**
  - Tarjan SCC: Mutual 2-cycle between `:StaffMember` and `:CompanyEmployee` with 100% shared instances (10 entities).
  - MFAS DAG cycle: Directed 3-cycle `:ProjectMilestoneA` $\to$ `:ProjectMilestoneB` $\to$ `:ProjectMilestoneC` $\to$ `:ProjectMilestoneA`.
  - Redundant Transitive Edge: Asserted `:ExecutiveDirector` $\to$ `:Person` reduced by Transitive Reduction to minimal Hasse diagram.

---

### 3.4 Domain 4: Financial / Banking (`input/banking_abox.ttl`)
- **Prefix:** `@prefix : <http://example.org/banking#> .`
- **Volume:** 704 triples, 149 subjects, 26 declared classes.
- **Taxonomic Class Hierarchies:**
  - *Depository Account Chain (4 levels):*  
    `PremiumCheckingAccount` (6) $\sqsubseteq$ `CheckingAccount` (14) $\sqsubseteq$ `DepositoryAccount` (24) $\sqsubseteq$ `FinancialAccount` (42).
  - *Credit Account Chain (4 levels):*  
    `MortgageLoanAccount` (9) $\sqsubseteq$ `LoanAccount` (18) $\sqsubseteq$ `CreditAccount` (18) $\sqsubseteq$ `FinancialAccount` (42).
  - *Payment Card Chain (4 levels):*  
    `PlatinumCreditCard` (4) $\sqsubseteq$ `CreditCard` (9) $\sqsubseteq$ `BankPaymentCard` (16) $\sqsubseteq$ `PaymentInstrument` (24).
- **Disjointness Boundary:**
  - Disjoint pair: `DepositoryAccount` vs `CreditAccount` / `LoanAccount`.
  - Injected conflict: `:noisy_depository_mortgage` asserted with `a :PremiumCheckingAccount, :MortgageLoanAccount .`
  - Pre-repair violations: `DVC_pre = 8`, Post-repair violations: `DVC_post = 0`.
- **Untyped Entity Clusters (3 clusters, 8 entities each):**
  1. *Collateral Guarantee:* `:collateral_01..08`, incoming `:securedByCollateral`, outgoing `[:appraisedCollateralValue, :collateralAssetType, :pledgeDocumentId]`. Synthesizes `:CollateralAppraised`.
  2. *Fee Schedule:* `:fee_sched_01..08`, incoming `:governedByFeeSchedule`, outgoing `[:feeScheduleVersion, :monthlyMaintenanceFee, :penaltyChargeRate]`. Synthesizes `:FeeSchedule`.
  3. *Security Token Credential:* `:token_01..08`, incoming `:customerSecurityToken`, outgoing `[:securityAlgorithmType, :tokenExpirationTimestamp, :tokenSerialNumber]`. Synthesizes `:TokenSecurity`.
- **Property Characteristics:**
  - Transitive: `:parentBranchOf` ($\rho_{\text{trans}} = 1.000$).
  - Symmetric: `:jointAccountWith` ($\rho_{\text{sym}} = 1.000$).
  - Functional: `:accountPrimaryOwner` ($\rho_{\text{func}} = 1.000$).
  - InverseFunctional: `:customerSecurityToken` ($\rho_{\text{invfunc}} = 1.000$).
  - Empirical Noise: Near-transitive `:wireTransferredTo` ($\rho_{\text{trans}} = 0.50$), Near-symmetric `:coSignerWith` ($\rho_{\text{sym}} = 0.67$).
- **Structural Challenge Noise:**
  - Tarjan SCC: Mutual 2-cycle between `:AccountHolder` and `:BankClient` with 100% shared instances (10 entities).
  - MFAS DAG cycle: Directed 3-cycle `:RiskRatingTierA` $\to$ `:RiskRatingTierB` $\to$ `:RiskRatingTierC` $\to$ `:RiskRatingTierA`.
  - Redundant Transitive Edge: Asserted `:PremiumCheckingAccount` $\to$ `:FinancialAccount` reduced by Transitive Reduction to minimal Hasse diagram.

---

## 4. Verification & Non-Regression Results

1. **Benchmark Suite Verification:**
   - Command: `python3 /home/miskat/ABOX2TBOX/.agents/worker_m1_gen2/verify_all_benchmarks.py`
   - Result: **100% of acceptance assertions satisfied** across all 4 benchmark datasets.
2. **University Baseline Non-Regression:**
   - Command: `python3 test_pipeline.py`
   - Result: **7/7 assertions passed (Exit code 0)** without modification to existing tests or regression in pipeline behavior.

---

## 5. File Manifest

The following files constitute the deliverables of Milestone 1:
- `/home/miskat/ABOX2TBOX/input/ecommerce_abox.ttl` (733 triples, E-Commerce ABox)
- `/home/miskat/ABOX2TBOX/input/hospital_abox.ttl` (576 triples, Hospital ABox)
- `/home/miskat/ABOX2TBOX/input/enterprise_abox.ttl` (590 triples, Enterprise ABox)
- `/home/miskat/ABOX2TBOX/input/banking_abox.ttl` (704 triples, Banking ABox)
- `/home/miskat/ABOX2TBOX/.agents/worker_m1_gen2/generate_all_benchmarks.py` (Deterministic multi-domain generator script)
- `/home/miskat/ABOX2TBOX/.agents/worker_m1_gen2/verify_all_benchmarks.py` (Automated verification harness for M1)
- `/home/miskat/ABOX2TBOX/.agents/worker_m1_gen2/report.md` (Detailed milestone report)
- `/home/miskat/ABOX2TBOX/.agents/worker_m1_gen2/handoff.md` (Formal 5-component handoff report)
