#!/usr/bin/env python3
"""generate_all_benchmarks.py - Multi-Domain Synthetic Benchmark Datasets Generator.

Generates 4 distinct real-world domain ABox Turtle datasets:
  1. input/ecommerce_abox.ttl
  2. input/hospital_abox.ttl
  3. input/enterprise_abox.ttl
  4. input/banking_abox.ttl
"""

import os
from collections import defaultdict
import rdflib
from rdflib import Graph, Literal, Namespace, RDF, XSD

XSD_STRING = XSD.string
XSD_DECIMAL = XSD.decimal
XSD_INTEGER = XSD.integer
XSD_BOOLEAN = XSD.boolean


# ==============================================================================
# Domain 1: E-Commerce / Retail
# ==============================================================================
def build_ecommerce_graph() -> Graph:
    g = Graph()
    NS = Namespace("http://example.org/ecommerce#")
    g.bind("", NS)
    g.bind("xsd", XSD)

    # 1. Product Hierarchy (4 levels deep)
    # Product (40) -> PhysicalProduct (24) -> ConsumerElectronics (12) / Apparel (12) -> Leaf classes (6 each)
    for i in range(1, 7):
        p = NS[f"phone_{i:02d}"]
        g.add((p, RDF.type, NS.Smartphone))
        g.add((p, RDF.type, NS.ConsumerElectronics))
        g.add((p, RDF.type, NS.PhysicalProduct))
        g.add((p, RDF.type, NS.Product))
        g.add((p, NS.productTitle, Literal(f"Galaxy Smartphone Neo {i}", datatype=XSD_STRING)))
        g.add((p, NS.unitPrice, Literal(f"{499.0 + i*50:.2f}", datatype=XSD_DECIMAL)))
        g.add((p, NS.skuCode, Literal(f"SKU-PH-{i:04d}", datatype=XSD_STRING)))
        g.add((p, NS.inStockUnits, Literal(10 + i * 5, datatype=XSD_INTEGER)))

    for i in range(1, 7):
        p = NS[f"laptop_{i:02d}"]
        g.add((p, RDF.type, NS.Laptop))
        g.add((p, RDF.type, NS.ConsumerElectronics))
        g.add((p, RDF.type, NS.PhysicalProduct))
        g.add((p, RDF.type, NS.Product))
        g.add((p, NS.productTitle, Literal(f"ProBook Ultra Thin {i}", datatype=XSD_STRING)))
        g.add((p, NS.unitPrice, Literal(f"{899.0 + i*100:.2f}", datatype=XSD_DECIMAL)))
        g.add((p, NS.skuCode, Literal(f"SKU-LP-{i:04d}", datatype=XSD_STRING)))
        g.add((p, NS.inStockUnits, Literal(5 + i * 2, datatype=XSD_INTEGER)))

    for i in range(1, 7):
        p = NS[f"shoes_{i:02d}"]
        g.add((p, RDF.type, NS.Footwear))
        g.add((p, RDF.type, NS.Apparel))
        g.add((p, RDF.type, NS.PhysicalProduct))
        g.add((p, RDF.type, NS.Product))
        g.add((p, NS.productTitle, Literal(f"Aero Runner Sneaker {i}", datatype=XSD_STRING)))
        g.add((p, NS.unitPrice, Literal(f"{79.0 + i*10:.2f}", datatype=XSD_DECIMAL)))
        g.add((p, NS.skuCode, Literal(f"SKU-SH-{i:04d}", datatype=XSD_STRING)))

    for i in range(1, 7):
        p = NS[f"jacket_{i:02d}"]
        g.add((p, RDF.type, NS.Outerwear))
        g.add((p, RDF.type, NS.Apparel))
        g.add((p, RDF.type, NS.PhysicalProduct))
        g.add((p, RDF.type, NS.Product))
        g.add((p, NS.productTitle, Literal(f"All-Weather Parka {i}", datatype=XSD_STRING)))
        g.add((p, NS.unitPrice, Literal(f"{129.0 + i*15:.2f}", datatype=XSD_DECIMAL)))
        g.add((p, NS.skuCode, Literal(f"SKU-JK-{i:04d}", datatype=XSD_STRING)))

    # Digital Products (Disjoint from PhysicalProduct)
    for i in range(1, 5):
        p = NS[f"app_{i:02d}"]
        g.add((p, RDF.type, NS.MobileApp))
        g.add((p, RDF.type, NS.SoftwareProduct))
        g.add((p, RDF.type, NS.DigitalProduct))
        g.add((p, RDF.type, NS.Product))
        g.add((p, NS.productTitle, Literal(f"Cloud Assistant Pro {i}", datatype=XSD_STRING)))
        g.add((p, NS.unitPrice, Literal(f"{9.99 + i:.2f}", datatype=XSD_DECIMAL)))
        g.add((p, NS.downloadUrl, Literal(f"https://store.example.org/apps/{i}", datatype=XSD_STRING)))

    for i in range(1, 5):
        p = NS[f"os_{i:02d}"]
        g.add((p, RDF.type, NS.OperatingSystem))
        g.add((p, RDF.type, NS.SoftwareProduct))
        g.add((p, RDF.type, NS.DigitalProduct))
        g.add((p, RDF.type, NS.Product))
        g.add((p, NS.productTitle, Literal(f"Enterprise Server OS v{i}", datatype=XSD_STRING)))
        g.add((p, NS.unitPrice, Literal(f"{199.99 + i*20:.2f}", datatype=XSD_DECIMAL)))

    for i in range(1, 5):
        p = NS[f"ebook_{i:02d}"]
        g.add((p, RDF.type, NS.EBook))
        g.add((p, RDF.type, NS.DigitalMedia))
        g.add((p, RDF.type, NS.DigitalProduct))
        g.add((p, RDF.type, NS.Product))
        g.add((p, NS.productTitle, Literal(f"Foundations of Semantic Web Vol {i}", datatype=XSD_STRING)))
        g.add((p, NS.unitPrice, Literal(f"{14.99 + i:.2f}", datatype=XSD_DECIMAL)))

    for i in range(1, 5):
        p = NS[f"album_{i:02d}"]
        g.add((p, RDF.type, NS.AudioAlbum))
        g.add((p, RDF.type, NS.DigitalMedia))
        g.add((p, RDF.type, NS.DigitalProduct))
        g.add((p, RDF.type, NS.Product))
        g.add((p, NS.productTitle, Literal(f"Orchestral Masterpieces Vol {i}", datatype=XSD_STRING)))
        g.add((p, NS.unitPrice, Literal(f"{11.99 + i:.2f}", datatype=XSD_DECIMAL)))

    # Injected Disjointness Violation Instance
    violator = NS["noisy_hybrid_product"]
    g.add((violator, RDF.type, NS.Smartphone))
    g.add((violator, RDF.type, NS.EBook))
    g.add((violator, NS.productTitle, Literal("Hybrid E-Reader Smart Phone", datatype=XSD_STRING)))
    g.add((violator, NS.unitPrice, Literal("249.99", datatype=XSD_DECIMAL)))

    # 2. Customer & Supplier Hierarchy (5 levels deep)
    # Party (35) -> Customer (24) -> RegisteredCustomer (16) -> VIPCustomer (8) -> PlatinumVIPCustomer (3)
    for i in range(1, 4):
        c = NS[f"cust_plat_{i:02d}"]
        g.add((c, RDF.type, NS.PlatinumVIPCustomer))
        g.add((c, RDF.type, NS.VIPCustomer))
        g.add((c, RDF.type, NS.RegisteredCustomer))
        g.add((c, RDF.type, NS.Customer))
        g.add((c, RDF.type, NS.Party))
        g.add((c, NS.customerName, Literal(f"Platinum Member {i}", datatype=XSD_STRING)))
        g.add((c, NS.primaryEmail, Literal(f"plat.{i}@domain.com", datatype=XSD_STRING)))

    for i in range(4, 9):
        c = NS[f"cust_vip_{i:02d}"]
        g.add((c, RDF.type, NS.VIPCustomer))
        g.add((c, RDF.type, NS.RegisteredCustomer))
        g.add((c, RDF.type, NS.Customer))
        g.add((c, RDF.type, NS.Party))
        g.add((c, NS.customerName, Literal(f"VIP Member {i}", datatype=XSD_STRING)))
        g.add((c, NS.primaryEmail, Literal(f"vip.{i}@domain.com", datatype=XSD_STRING)))

    for i in range(9, 17):
        c = NS[f"cust_reg_{i:02d}"]
        g.add((c, RDF.type, NS.RegisteredCustomer))
        g.add((c, RDF.type, NS.Customer))
        g.add((c, RDF.type, NS.Party))
        g.add((c, NS.customerName, Literal(f"Standard Registered Member {i}", datatype=XSD_STRING)))
        g.add((c, NS.primaryEmail, Literal(f"reg.{i}@domain.com", datatype=XSD_STRING)))

    for i in range(17, 25):
        c = NS[f"cust_guest_{i:02d}"]
        g.add((c, RDF.type, NS.Customer))
        g.add((c, RDF.type, NS.Party))
        g.add((c, NS.customerName, Literal(f"Guest Shopper {i}", datatype=XSD_STRING)))
        g.add((c, NS.primaryEmail, Literal(f"guest.{i}@domain.com", datatype=XSD_STRING)))

    for i in range(1, 6):
        s = NS[f"supp_dom_{i:02d}"]
        g.add((s, RDF.type, NS.DomesticSupplier))
        g.add((s, RDF.type, NS.VerifiedSupplier))
        g.add((s, RDF.type, NS.Supplier))
        g.add((s, RDF.type, NS.Party))
        g.add((s, NS.supplierName, Literal(f"Domestic Distribution Co {i}", datatype=XSD_STRING)))

    for i in range(1, 6):
        s = NS[f"supp_int_{i:02d}"]
        g.add((s, RDF.type, NS.InternationalSupplier))
        g.add((s, RDF.type, NS.VerifiedSupplier))
        g.add((s, RDF.type, NS.Supplier))
        g.add((s, RDF.type, NS.Party))
        g.add((s, NS.supplierName, Literal(f"Global Freight Alliance {i}", datatype=XSD_STRING)))

    # 3. Equivalent Classes (Tarjan SCC 2-cycle)
    for i in range(1, 11):
        bp = NS[f"buyer_purchaser_{i:02d}"]
        g.add((bp, RDF.type, NS.Buyer))
        g.add((bp, RDF.type, NS.Purchaser))
        g.add((bp, NS.accountIdentifier, Literal(f"ACC-BP-{i:03d}", datatype=XSD_STRING)))

    # 4. MFAS Directed Cycle
    for i in range(1, 6):
        ra = NS[f"rev_cycle_a_{i:02d}"]
        g.add((ra, RDF.type, NS.ReviewTierA))
        g.add((ra, RDF.type, NS.ReviewTierB))
        rb = NS[f"rev_cycle_b_{i:02d}"]
        g.add((rb, RDF.type, NS.ReviewTierB))
        g.add((rb, RDF.type, NS.ReviewTierC))
        rc = NS[f"rev_cycle_c_{i:02d}"]
        g.add((rc, RDF.type, NS.ReviewTierC))
        g.add((rc, RDF.type, NS.ReviewTierA))

    # 5. Orders & Reviews
    for i in range(1, 11):
        ord_uri = NS[f"order_{i:02d}"]
        g.add((ord_uri, RDF.type, NS.Order))
        g.add((ord_uri, NS.orderTotalAmount, Literal(f"{150.0 + i*25:.2f}", datatype=XSD_DECIMAL)))
        g.add((ord_uri, NS.placedByCustomer, NS[f"cust_reg_{i+8:02d}"]))
        g.add((ord_uri, NS.includesProduct, NS[f"phone_{min(i, 6):02d}"]))
        g.add((ord_uri, NS.primaryContactCustomer, NS[f"cust_reg_{i+8:02d}"]))
        g.add((ord_uri, NS.trackingCode, Literal(f"TRK-ECOMM-{i:06d}", datatype=XSD_STRING)))

    for i in range(1, 9):
        rev = NS[f"review_{i:02d}"]
        g.add((rev, RDF.type, NS.ProductReview))
        g.add((rev, NS.reviewRating, Literal(4 + (i % 2), datatype=XSD_INTEGER)))
        g.add((rev, NS.reviewText, Literal(f"Superb quality and rapid shipment #{i}", datatype=XSD_STRING)))
        g.add((rev, NS.reviewsProduct, NS[f"laptop_{min(i, 6):02d}"]))

    # 6. Property Characteristics
    # Transitive: isSubCategoryOf (2 disjoint trees, 100% closed)
    cat_t = [NS[f"cat_tech_{i}"] for i in range(1, 4)]
    cat_a = [NS[f"cat_app_{i}"] for i in range(1, 4)]
    for c in cat_t + cat_a:
        g.add((c, RDF.type, NS.ProductCategory))
    g.add((cat_t[0], NS.isSubCategoryOf, cat_t[1]))
    g.add((cat_t[1], NS.isSubCategoryOf, cat_t[2]))
    g.add((cat_t[0], NS.isSubCategoryOf, cat_t[2]))
    g.add((cat_a[0], NS.isSubCategoryOf, cat_a[1]))
    g.add((cat_a[1], NS.isSubCategoryOf, cat_a[2]))
    g.add((cat_a[0], NS.isSubCategoryOf, cat_a[2]))

    # Symmetric: frequentlyBoughtTogether (100% reciprocal pairs)
    for i in range(1, 5):
        p1 = NS[f"phone_{i:02d}"]
        p2 = NS[f"shoes_{i:02d}"]
        g.add((p1, NS.frequentlyBoughtTogether, p2))
        g.add((p2, NS.frequentlyBoughtTogether, p1))

    # Near-transitive noise: crossPromotedWith (rho_trans = 0.50)
    g.add((cat_t[0], NS.crossPromotedWith, cat_t[1]))
    g.add((cat_t[1], NS.crossPromotedWith, cat_t[2]))
    g.add((cat_a[0], NS.crossPromotedWith, cat_a[1]))
    g.add((cat_a[1], NS.crossPromotedWith, cat_a[2]))
    g.add((cat_a[0], NS.crossPromotedWith, cat_a[2]))

    # Near-symmetric noise: recommendedWith (rho_sym = 0.67)
    g.add((NS["phone_01"], NS.recommendedWith, NS["laptop_01"]))
    g.add((NS["laptop_01"], NS.recommendedWith, NS["phone_01"]))
    g.add((NS["phone_02"], NS.recommendedWith, NS["laptop_02"]))

    # 7. Untyped Entity Clusters (3 clusters, 8 entities each)
    for i in range(1, 9):
        sh = NS[f"shipment_{i:02d}"]
        g.add((NS[f"order_{min(i, 8):02d}"], NS.orderHasShipment, sh))
        g.add((sh, NS.trackingNumber, Literal(f"TRACK-FEDEX-900{i}", datatype=XSD_STRING)))
        g.add((sh, NS.shippingCarrier, Literal("FederalExpress", datatype=XSD_STRING)))
        g.add((sh, NS.shippingStatus, Literal("InTransit", datatype=XSD_STRING)))

    for i in range(1, 9):
        pr = NS[f"promo_{i:02d}"]
        g.add((NS[f"order_{min(i, 8):02d}"], NS.appliedPromotion, pr))
        g.add((pr, NS.couponCode, Literal(f"DISCOUNT{i*5}", datatype=XSD_STRING)))
        g.add((pr, NS.discountPercentage, Literal(5 + i * 2, datatype=XSD_INTEGER)))
        g.add((pr, NS.promotionTitle, Literal(f"Seasonal Promotion {i}", datatype=XSD_STRING)))

    for i in range(1, 9):
        sp = NS[f"spec_{i:02d}"]
        g.add((NS[f"phone_{min(i, 6):02d}"], NS.hasSpecification, sp))
        g.add((sp, NS.dimensionMeasurement, Literal(f"150x75x8.{i} mm", datatype=XSD_STRING)))
        g.add((sp, NS.technicalWeight, Literal(f"18{i} grams", datatype=XSD_STRING)))
        g.add((sp, NS.warrantyPeriod, Literal("24 Months", datatype=XSD_STRING)))

    return g


# ==============================================================================
# Domain 2: Hospital / Biomedical
# ==============================================================================
def build_hospital_graph() -> Graph:
    g = Graph()
    NS = Namespace("http://example.org/hospital#")
    g.bind("", NS)
    g.bind("xsd", XSD)

    # 1. Staff / Physician Hierarchy (5 levels deep)
    # Person (44) -> HealthcareStaff (22) -> Physician (14) -> SpecialistPhysician (8) -> Cardiologist (4) / Neurologist (4)
    for i in range(1, 5):
        d = NS[f"doc_cardio_{i:02d}"]
        g.add((d, RDF.type, NS.Cardiologist))
        g.add((d, RDF.type, NS.SpecialistPhysician))
        g.add((d, RDF.type, NS.Physician))
        g.add((d, RDF.type, NS.HealthcareStaff))
        g.add((d, RDF.type, NS.Person))
        g.add((d, NS.physicianName, Literal(f"Dr. Eleanor Vance {i}", datatype=XSD_STRING)))
        g.add((d, NS.licenseId, Literal(f"MED-CARDIO-{i:04d}", datatype=XSD_STRING)))
        g.add((d, NS.yearsOfExperience, Literal(12 + i, datatype=XSD_INTEGER)))

    for i in range(1, 5):
        d = NS[f"doc_neuro_{i:02d}"]
        g.add((d, RDF.type, NS.Neurologist))
        g.add((d, RDF.type, NS.SpecialistPhysician))
        g.add((d, RDF.type, NS.Physician))
        g.add((d, RDF.type, NS.HealthcareStaff))
        g.add((d, RDF.type, NS.Person))
        g.add((d, NS.physicianName, Literal(f"Dr. Marcus Brody {i}", datatype=XSD_STRING)))
        g.add((d, NS.licenseId, Literal(f"MED-NEURO-{i:04d}", datatype=XSD_STRING)))

    for i in range(1, 7):
        d = NS[f"doc_gp_{i:02d}"]
        g.add((d, RDF.type, NS.GeneralPractitioner))
        g.add((d, RDF.type, NS.Physician))
        g.add((d, RDF.type, NS.HealthcareStaff))
        g.add((d, RDF.type, NS.Person))
        g.add((d, NS.physicianName, Literal(f"Dr. Sarah Jenkins {i}", datatype=XSD_STRING)))

    for i in range(1, 9):
        n = NS[f"nurse_{i:02d}"]
        g.add((n, RDF.type, NS.RegisteredNurse))
        g.add((n, RDF.type, NS.HealthcareStaff))
        g.add((n, RDF.type, NS.Person))
        g.add((n, NS.staffName, Literal(f"Nurse Michael Chen {i}", datatype=XSD_STRING)))

    # 2. Patient Hierarchy (4 levels deep)
    # Person -> Patient (22) -> Inpatient (10) / Outpatient (12) -> Leaf classes
    # Inpatients (Disjoint with Outpatient)
    for i in range(1, 6):
        p = NS[f"pat_icu_{i:02d}"]
        g.add((p, RDF.type, NS.ICUPatient))
        g.add((p, RDF.type, NS.Inpatient))
        g.add((p, RDF.type, NS.Patient))
        g.add((p, RDF.type, NS.Person))
        g.add((p, NS.patientName, Literal(f"ICU Patient {i}", datatype=XSD_STRING)))
        g.add((p, NS.admissionDate, Literal(f"2026-10-{10+i:02d}", datatype=XSD_STRING)))
        g.add((p, NS.bedNumber, Literal(f"ICU-BED-{i:02d}", datatype=XSD_STRING)))
        g.add((p, NS.acuityScore, Literal(8 + (i % 3), datatype=XSD_INTEGER)))
        g.add((p, NS.bloodPressureSystolic, Literal(120 + i*2, datatype=XSD_INTEGER)))

    for i in range(1, 6):
        p = NS[f"pat_surg_{i:02d}"]
        g.add((p, RDF.type, NS.SurgicalPatient))
        g.add((p, RDF.type, NS.Inpatient))
        g.add((p, RDF.type, NS.Patient))
        g.add((p, RDF.type, NS.Person))
        g.add((p, NS.patientName, Literal(f"Surgical Patient {i}", datatype=XSD_STRING)))
        g.add((p, NS.admissionDate, Literal(f"2026-10-{12+i:02d}", datatype=XSD_STRING)))
        g.add((p, NS.bedNumber, Literal(f"SURG-BED-{i:02d}", datatype=XSD_STRING)))

    # Outpatients (Disjoint with Inpatient)
    for i in range(1, 7):
        p = NS[f"pat_er_{i:02d}"]
        g.add((p, RDF.type, NS.EmergencyPatient))
        g.add((p, RDF.type, NS.Outpatient))
        g.add((p, RDF.type, NS.Patient))
        g.add((p, RDF.type, NS.Person))
        g.add((p, NS.patientName, Literal(f"Emergency Patient {i}", datatype=XSD_STRING)))
        g.add((p, NS.triageUrgency, Literal("High", datatype=XSD_STRING)))

    for i in range(1, 7):
        p = NS[f"pat_clinic_{i:02d}"]
        g.add((p, RDF.type, NS.ClinicPatient))
        g.add((p, RDF.type, NS.Outpatient))
        g.add((p, RDF.type, NS.Patient))
        g.add((p, RDF.type, NS.Person))
        g.add((p, NS.patientName, Literal(f"Outpatient Clinic Patient {i}", datatype=XSD_STRING)))
        g.add((p, NS.appointmentSlot, Literal(f"Slot-{i:02d}", datatype=XSD_STRING)))

    # Injected Disjointness Violation Instance
    violator = NS["noisy_patient_transfer"]
    g.add((violator, RDF.type, NS.ICUPatient))
    g.add((violator, RDF.type, NS.ClinicPatient))
    g.add((violator, NS.patientName, Literal("Cross-Admitted Ambulatory ICU Patient", datatype=XSD_STRING)))
    g.add((violator, NS.admissionDate, Literal("2026-10-15", datatype=XSD_STRING)))

    # 3. Equivalent Classes (Tarjan SCC 2-cycle)
    # Dedicated equivalent concept pair: LicensedPhysician and MedicalDoctor
    for i in range(1, 11):
        md = NS[f"med_doc_{i:02d}"]
        g.add((md, RDF.type, NS.LicensedPhysician))
        g.add((md, RDF.type, NS.MedicalDoctor))
        g.add((md, NS.physicianRegistryCode, Literal(f"REG-DOC-{i:04d}", datatype=XSD_STRING)))

    # 4. MFAS Directed Cycle
    for i in range(1, 6):
        ta = NS[f"triage_a_{i:02d}"]
        g.add((ta, RDF.type, NS.TriageLevelA))
        g.add((ta, RDF.type, NS.TriageLevelB))
        tb = NS[f"triage_b_{i:02d}"]
        g.add((tb, RDF.type, NS.TriageLevelB))
        g.add((tb, RDF.type, NS.TriageLevelC))
        tc = NS[f"triage_c_{i:02d}"]
        g.add((tc, RDF.type, NS.TriageLevelC))
        g.add((tc, RDF.type, NS.TriageLevelA))

    # 5. Diagnoses, Treatments, Medications
    for i in range(1, 10):
        diag = NS[f"diag_{i:02d}"]
        g.add((diag, RDF.type, NS.MedicalDiagnosis))
        g.add((diag, NS.icd10Code, Literal(f"I2{i}.0", datatype=XSD_STRING)))
        g.add((diag, NS.diagnosisLabel, Literal(f"Cardiovascular Condition Grade {i}", datatype=XSD_STRING)))
        g.add((diag, NS.diagnosedByPhysician, NS[f"doc_cardio_{min(i, 4):02d}"]))
        g.add((diag, NS.severityIndex, Literal(i * 10, datatype=XSD_INTEGER)))

    for i in range(1, 10):
        trt = NS[f"treat_{i:02d}"]
        g.add((trt, RDF.type, NS.ClinicalTreatment))
        g.add((trt, NS.treatmentType, Literal("TherapeuticIntervention", datatype=XSD_STRING)))
        g.add((trt, NS.assignedAttendingDoctor, NS[f"doc_cardio_{min(i, 4):02d}"]))
        g.add((trt, NS.prescribedForDiagnosis, NS[f"diag_{i:02d}"]))

    for i in range(1, 10):
        med = NS[f"med_{i:02d}"]
        g.add((med, RDF.type, NS.PrescriptionDrug))
        g.add((med, NS.drugGenericName, Literal(f"CardioStatin-{i*10}mg", datatype=XSD_STRING)))
        g.add((med, NS.fdaApprovalNumber, Literal(f"FDA-{i:05d}", datatype=XSD_STRING)))

    # 6. Property Characteristics
    # Transitive: subDepartmentOf (2 disjoint trees, 100% closed)
    dept_a = [NS[f"dept_med_{i}"] for i in range(1, 4)]
    dept_b = [NS[f"dept_surg_{i}"] for i in range(1, 4)]
    for d in dept_a + dept_b:
        g.add((d, RDF.type, NS.HospitalDepartment))
    g.add((dept_a[0], NS.subDepartmentOf, dept_a[1]))
    g.add((dept_a[1], NS.subDepartmentOf, dept_a[2]))
    g.add((dept_a[0], NS.subDepartmentOf, dept_a[2]))
    g.add((dept_b[0], NS.subDepartmentOf, dept_b[1]))
    g.add((dept_b[1], NS.subDepartmentOf, dept_b[2]))
    g.add((dept_b[0], NS.subDepartmentOf, dept_b[2]))

    # Symmetric: consultsWith (100% reciprocal pairs)
    for i in range(1, 5):
        d1 = NS[f"doc_cardio_{i:02d}"]
        d2 = NS[f"doc_neuro_{i:02d}"]
        g.add((d1, NS.consultsWith, d2))
        g.add((d2, NS.consultsWith, d1))

    # Near-transitive noise: transferredToWard (rho_trans = 0.50)
    w = [NS[f"ward_{i}"] for i in range(1, 7)]
    for x in w: g.add((x, RDF.type, NS.HospitalWard))
    g.add((w[0], NS.transferredToWard, w[1]))
    g.add((w[1], NS.transferredToWard, w[2]))
    g.add((w[3], NS.transferredToWard, w[4]))
    g.add((w[4], NS.transferredToWard, w[5]))
    g.add((w[3], NS.transferredToWard, w[5]))

    # Near-symmetric noise: referredPatientTo (rho_sym = 0.67)
    g.add((NS["doc_cardio_01"], NS.referredPatientTo, NS["doc_gp_01"]))
    g.add((NS["doc_gp_01"], NS.referredPatientTo, NS["doc_cardio_01"]))
    g.add((NS["doc_cardio_02"], NS.referredPatientTo, NS["doc_gp_02"]))

    # 7. Untyped Entity Clusters (3 clusters, 8 entities each)
    for i in range(1, 9):
        lr = NS[f"lab_res_{i:02d}"]
        g.add((NS[f"pat_icu_{min(i, 5):02d}"], NS.patientLabResult, lr))
        g.add((lr, NS.testMetricName, Literal("SerumCreatinineLevel", datatype=XSD_STRING)))
        g.add((lr, NS.labMeasurementValue, Literal(f"1.{i} mg/dL", datatype=XSD_STRING)))
        g.add((lr, NS.referenceRangeNormal, Literal("0.7 - 1.3 mg/dL", datatype=XSD_STRING)))

    for i in range(1, 9):
        dos = NS[f"dosage_{i:02d}"]
        g.add((NS[f"treat_{i:02d}"], NS.treatmentPrescriptionDosage, dos))
        g.add((dos, NS.dosageQuantity, Literal(f"{i*5} mg", datatype=XSD_STRING)))
        g.add((dos, NS.intakeFrequency, Literal("TwiceDailyAfterMeals", datatype=XSD_STRING)))
        g.add((dos, NS.routeAdministration, Literal("OralCapsule", datatype=XSD_STRING)))

    for i in range(1, 9):
        pol = NS[f"policy_{i:02d}"]
        g.add((NS[f"pat_icu_{min(i, 5):02d}"], NS.patientInsurancePolicy, pol))
        g.add((pol, NS.insuranceProviderName, Literal(f"National Blue Health #{i}", datatype=XSD_STRING)))
        g.add((pol, NS.policyCoverageLimit, Literal(f"{500000 + i*50000}", datatype=XSD_INTEGER)))
        g.add((pol, NS.policyContractNumber, Literal(f"POL-MED-{i:06d}", datatype=XSD_STRING)))

    return g


# ==============================================================================
# Domain 3: Enterprise Organization
# ==============================================================================
def build_enterprise_graph() -> Graph:
    g = Graph()
    NS = Namespace("http://example.org/enterprise#")
    g.bind("", NS)
    g.bind("xsd", XSD)

    # 1. Employee Hierarchy (5 levels deep)
    # Person (42) -> CorporateEmployee (30) -> FullTimeEmployee (18) -> SeniorFullTimeEmployee (10) -> ExecutiveDirector (4)
    for i in range(1, 5):
        e = NS[f"emp_exec_{i:02d}"]
        g.add((e, RDF.type, NS.ExecutiveDirector))
        g.add((e, RDF.type, NS.SeniorFullTimeEmployee))
        g.add((e, RDF.type, NS.FullTimeEmployee))
        g.add((e, RDF.type, NS.CorporateEmployee))
        g.add((e, RDF.type, NS.Person))
        g.add((e, NS.fullName, Literal(f"Director Alexander Vance {i}", datatype=XSD_STRING)))
        g.add((e, NS.annualSalary, Literal(f"{180000.0 + i*15000:.2f}", datatype=XSD_DECIMAL)))
        g.add((e, NS.employeeCorporateId, Literal(f"CORP-EXEC-{i:04d}", datatype=XSD_STRING)))
        g.add((e, NS.officeRoomNumber, Literal(f"EXEC-SUITE-{i:02d}", datatype=XSD_STRING)))

    for i in range(5, 11):
        e = NS[f"emp_sr_{i:02d}"]
        g.add((e, RDF.type, NS.SeniorFullTimeEmployee))
        g.add((e, RDF.type, NS.FullTimeEmployee))
        g.add((e, RDF.type, NS.CorporateEmployee))
        g.add((e, RDF.type, NS.Person))
        g.add((e, NS.fullName, Literal(f"Senior Staff Engineer {i}", datatype=XSD_STRING)))
        g.add((e, NS.annualSalary, Literal(f"{130000.0 + i*8000:.2f}", datatype=XSD_DECIMAL)))
        g.add((e, NS.employeeCorporateId, Literal(f"CORP-ENG-{i:04d}", datatype=XSD_STRING)))
        g.add((e, NS.officeRoomNumber, Literal(f"ENG-LAB-{i:02d}", datatype=XSD_STRING)))

    for i in range(1, 9):
        e = NS[f"emp_jr_{i:02d}"]
        g.add((e, RDF.type, NS.JuniorFullTimeEmployee))
        g.add((e, RDF.type, NS.FullTimeEmployee))
        g.add((e, RDF.type, NS.CorporateEmployee))
        g.add((e, RDF.type, NS.Person))
        g.add((e, NS.fullName, Literal(f"Associate Analyst {i}", datatype=XSD_STRING)))
        g.add((e, NS.annualSalary, Literal(f"{75000.0 + i*4000:.2f}", datatype=XSD_DECIMAL)))
        g.add((e, NS.employeeCorporateId, Literal(f"CORP-JR-{i:04d}", datatype=XSD_STRING)))

    # ContractWorker (Disjoint with FullTimeEmployee)
    for i in range(1, 7):
        e = NS[f"cont_ext_{i:02d}"]
        g.add((e, RDF.type, NS.ExternalConsultant))
        g.add((e, RDF.type, NS.ContractWorker))
        g.add((e, RDF.type, NS.CorporateEmployee))
        g.add((e, RDF.type, NS.Person))
        g.add((e, NS.fullName, Literal(f"Strategy Consultant {i}", datatype=XSD_STRING)))
        g.add((e, NS.hourlyBillingRate, Literal(f"{120.0 + i*10:.2f}", datatype=XSD_DECIMAL)))
        g.add((e, NS.contractAgencyName, Literal(f"Global Consulting Group #{i}", datatype=XSD_STRING)))

    for i in range(1, 7):
        e = NS[f"cont_free_{i:02d}"]
        g.add((e, RDF.type, NS.FreelanceContractor))
        g.add((e, RDF.type, NS.ContractWorker))
        g.add((e, RDF.type, NS.CorporateEmployee))
        g.add((e, RDF.type, NS.Person))
        g.add((e, NS.fullName, Literal(f"Technical Contractor {i}", datatype=XSD_STRING)))
        g.add((e, NS.hourlyBillingRate, Literal(f"{85.0 + i*5:.2f}", datatype=XSD_DECIMAL)))

    # Injected Disjointness Violation Instance
    violator = NS["noisy_corporate_worker"]
    g.add((violator, RDF.type, NS.ExecutiveDirector))
    g.add((violator, RDF.type, NS.ExternalConsultant))
    g.add((violator, NS.fullName, Literal("Dual Contract-Fulltime Advisory Officer", datatype=XSD_STRING)))
    g.add((violator, NS.annualSalary, Literal("195000.00", datatype=XSD_DECIMAL)))

    # 2. Asset Hierarchy (4 levels deep)
    # EnterpriseAsset (24) -> HardwareAsset (12) / FacilityAsset (12) -> ComputingDevice (12) -> Leaf classes
    for i in range(1, 7):
        a = NS[f"srv_{i:02d}"]
        g.add((a, RDF.type, NS.ServerAsset))
        g.add((a, RDF.type, NS.ComputingDevice))
        g.add((a, RDF.type, NS.HardwareAsset))
        g.add((a, RDF.type, NS.EnterpriseAsset))
        g.add((a, NS.assetHostname, Literal(f"srv-prod-{i:02d}.corp.internal", datatype=XSD_STRING)))
        g.add((a, NS.assetDepreciationValue, Literal(f"{12000.0 - i*1000:.2f}", datatype=XSD_DECIMAL)))

    for i in range(1, 7):
        a = NS[f"ws_{i:02d}"]
        g.add((a, RDF.type, NS.WorkstationAsset))
        g.add((a, RDF.type, NS.ComputingDevice))
        g.add((a, RDF.type, NS.HardwareAsset))
        g.add((a, RDF.type, NS.EnterpriseAsset))
        g.add((a, NS.assetHostname, Literal(f"ws-dev-{i:02d}.corp.internal", datatype=XSD_STRING)))

    for i in range(1, 7):
        a = NS[f"bldg_{i:02d}"]
        g.add((a, RDF.type, NS.OfficeFacility))
        g.add((a, RDF.type, NS.FacilityAsset))
        g.add((a, RDF.type, NS.EnterpriseAsset))
        g.add((a, NS.facilityLocationCode, Literal(f"CAMPUS-BLDG-{i:02d}", datatype=XSD_STRING)))

    for i in range(1, 7):
        a = NS[f"dc_{i:02d}"]
        g.add((a, RDF.type, NS.DatacenterFacility))
        g.add((a, RDF.type, NS.FacilityAsset))
        g.add((a, RDF.type, NS.EnterpriseAsset))
        g.add((a, NS.facilityLocationCode, Literal(f"DC-VAULT-{i:02d}", datatype=XSD_STRING)))

    # 3. Equivalent Classes (Tarjan SCC 2-cycle)
    for i in range(1, 11):
        sc = NS[f"staff_comp_{i:02d}"]
        g.add((sc, RDF.type, NS.StaffMember))
        g.add((sc, RDF.type, NS.CompanyEmployee))
        g.add((sc, NS.payrollId, Literal(f"PAYROLL-{i:04d}", datatype=XSD_STRING)))

    # 4. MFAS Directed Cycle
    for i in range(1, 6):
        pa = NS[f"proj_milestone_a_{i:02d}"]
        g.add((pa, RDF.type, NS.ProjectMilestoneA))
        g.add((pa, RDF.type, NS.ProjectMilestoneB))
        pb = NS[f"proj_milestone_b_{i:02d}"]
        g.add((pb, RDF.type, NS.ProjectMilestoneB))
        g.add((pb, RDF.type, NS.ProjectMilestoneC))
        pc = NS[f"proj_milestone_c_{i:02d}"]
        g.add((pc, RDF.type, NS.ProjectMilestoneC))
        g.add((pc, RDF.type, NS.ProjectMilestoneA))

    # 5. Projects & Budgets
    for i in range(1, 11):
        prj = NS[f"proj_{i:02d}"]
        g.add((prj, RDF.type, NS.BusinessProject))
        g.add((prj, NS.projectName, Literal(f"Enterprise Transformation Phase {i}", datatype=XSD_STRING)))
        g.add((prj, NS.assignedProjectLead, NS[f"emp_exec_{min(i, 4):02d}"]))
        g.add((prj, NS.projectStartDate, Literal(f"2026-0{min(i, 9):02d}-01", datatype=XSD_STRING)))

    for i in range(1, 11):
        bud = NS[f"budget_{i:02d}"]
        g.add((bud, RDF.type, NS.FiscalBudget))
        g.add((bud, NS.allocatedCapitalAmount, Literal(f"{250000.0 + i*50000:.2f}", datatype=XSD_DECIMAL)))
        g.add((bud, NS.fiscalYearQuarter, Literal(f"2026-Q{(i%4)+1}", datatype=XSD_STRING)))

    # 6. Property Characteristics
    # Transitive: subDivisionOf (2 disjoint trees, 100% closed)
    div_a = [NS[f"div_tech_{i}"] for i in range(1, 4)]
    div_b = [NS[f"div_ops_{i}"] for i in range(1, 4)]
    for d in div_a + div_b:
        g.add((d, RDF.type, NS.EnterpriseDepartment))
    g.add((div_a[0], NS.subDivisionOf, div_a[1]))
    g.add((div_a[1], NS.subDivisionOf, div_a[2]))
    g.add((div_a[0], NS.subDivisionOf, div_a[2]))
    g.add((div_b[0], NS.subDivisionOf, div_b[1]))
    g.add((div_b[1], NS.subDivisionOf, div_b[2]))
    g.add((div_b[0], NS.subDivisionOf, div_b[2]))

    # Symmetric: collaboratesWith (100% reciprocal pairs)
    for i in range(1, 5):
        e1 = NS[f"emp_exec_{i:02d}"]
        e2 = NS[f"emp_sr_{i+4:02d}"]
        g.add((e1, NS.collaboratesWith, e2))
        g.add((e2, NS.collaboratesWith, e1))

    # Near-transitive noise: advises (rho_trans = 0.50)
    g.add((div_a[0], NS.advises, div_a[1]))
    g.add((div_a[1], NS.advises, div_a[2]))
    g.add((div_b[0], NS.advises, div_b[1]))
    g.add((div_b[1], NS.advises, div_b[2]))
    g.add((div_b[0], NS.advises, div_b[2]))

    # Near-symmetric noise: mentors (rho_sym = 0.67)
    g.add((NS["emp_exec_01"], NS.mentors, NS["emp_jr_01"]))
    g.add((NS["emp_jr_01"], NS.mentors, NS["emp_exec_01"]))
    g.add((NS["emp_exec_02"], NS.mentors, NS["emp_jr_02"]))

    # 7. Untyped Entity Clusters (3 clusters, 8 entities each)
    for i in range(1, 9):
        exp = NS[f"expense_{i:02d}"]
        g.add((NS[f"emp_jr_{i:02d}"], NS.submittedExpenseReport, exp))
        g.add((exp, NS.reimbursementAmount, Literal(f"{350.0 + i*45:.2f}", datatype=XSD_DECIMAL)))
        g.add((exp, NS.expenseCategoryCode, Literal("TRAVEL_LODGING", datatype=XSD_STRING)))
        g.add((exp, NS.approvalStatusCode, Literal("APPROVED", datatype=XSD_STRING)))

    for i in range(1, 9):
        lic = NS[f"lic_{i:02d}"]
        g.add((NS[f"srv_{min(i, 6):02d}"], NS.assignedSoftwareLicense, lic))
        g.add((lic, NS.licenseKeyIdentifier, Literal(f"LIC-KEY-ENTERPRISE-{i:05d}", datatype=XSD_STRING)))
        g.add((lic, NS.expirationDatePeriod, Literal("2028-12-31", datatype=XSD_STRING)))
        g.add((lic, NS.vendorEntityName, Literal(f"OracleEnterpriseCorp #{i}", datatype=XSD_STRING)))

    for i in range(1, 9):
        rev = NS[f"perf_rev_{i:02d}"]
        g.add((NS[f"emp_jr_{i:02d}"], NS.employeePerformanceReview, rev))
        g.add((rev, NS.reviewRatingScore, Literal(4 + (i % 2), datatype=XSD_INTEGER)))
        g.add((rev, NS.performanceEvaluationPeriod, Literal("FY2026-H1", datatype=XSD_STRING)))
        g.add((rev, NS.reviewerFeedbackNotes, Literal("Consistently exceeds core project deliverables", datatype=XSD_STRING)))

    return g


# ==============================================================================
# Domain 4: Banking / Financial
# ==============================================================================
def build_banking_graph() -> Graph:
    g = Graph()
    NS = Namespace("http://example.org/banking#")
    g.bind("", NS)
    g.bind("xsd", XSD)

    # 1. Payment Instrument Hierarchy (4 levels deep)
    # PaymentInstrument (24) -> BankPaymentCard (16) -> CreditCard (9) -> PlatinumCreditCard (4)
    for i in range(1, 5):
        c = NS[f"card_plat_{i:02d}"]
        g.add((c, RDF.type, NS.PlatinumCreditCard))
        g.add((c, RDF.type, NS.CreditCard))
        g.add((c, RDF.type, NS.BankPaymentCard))
        g.add((c, RDF.type, NS.PaymentInstrument))
        g.add((c, NS.cardCreditLimit, Literal(f"{25000.0 + i*5000:.2f}", datatype=XSD_DECIMAL)))
        g.add((c, NS.cardMaskedPan, Literal(f"4111-XXXX-XXXX-00{i:02d}", datatype=XSD_STRING)))

    for i in range(5, 10):
        c = NS[f"card_gold_{i:02d}"]
        g.add((c, RDF.type, NS.GoldCreditCard))
        g.add((c, RDF.type, NS.CreditCard))
        g.add((c, RDF.type, NS.BankPaymentCard))
        g.add((c, RDF.type, NS.PaymentInstrument))
        g.add((c, NS.cardCreditLimit, Literal(f"{10000.0 + i*2000:.2f}", datatype=XSD_DECIMAL)))
        g.add((c, NS.cardMaskedPan, Literal(f"4222-XXXX-XXXX-00{i:02d}", datatype=XSD_STRING)))

    for i in range(1, 8):
        c = NS[f"card_debit_{i:02d}"]
        g.add((c, RDF.type, NS.ContactlessDebitCard))
        g.add((c, RDF.type, NS.DebitCard))
        g.add((c, RDF.type, NS.BankPaymentCard))
        g.add((c, RDF.type, NS.PaymentInstrument))
        g.add((c, NS.dailyAtmWithdrawalLimit, Literal(f"{1000.0 + i*200:.2f}", datatype=XSD_DECIMAL)))
        g.add((c, NS.cardMaskedPan, Literal(f"4333-XXXX-XXXX-00{i:02d}", datatype=XSD_STRING)))

    # Non-card PaymentInstruments to keep BankPaymentCard (16) smaller than PaymentInstrument (24)
    for i in range(1, 9):
        p = NS[f"pay_inst_other_{i:02d}"]
        g.add((p, RDF.type, NS.PaymentInstrument))
        g.add((p, NS.instrumentDescription, Literal(f"Digital Wire Direct Routing {i}", datatype=XSD_STRING)))

    # 2. Account Hierarchy (4 levels deep)
    # FinancialAccount (42) -> DepositoryAccount (24) / CreditAccount (18) -> SubClasses -> Leaf classes
    # DepositoryAccount (Disjoint with CreditAccount / LoanAccount)
    for i in range(1, 7):
        acc = NS[f"acc_prem_{i:02d}"]
        g.add((acc, RDF.type, NS.PremiumCheckingAccount))
        g.add((acc, RDF.type, NS.CheckingAccount))
        g.add((acc, RDF.type, NS.DepositoryAccount))
        g.add((acc, RDF.type, NS.FinancialAccount))
        g.add((acc, NS.accountBalanceCurrent, Literal(f"{25000.0 + i*3500:.2f}", datatype=XSD_DECIMAL)))
        g.add((acc, NS.interestRateYield, Literal("0.025", datatype=XSD_DECIMAL)))
        g.add((acc, NS.ibanIdentifierCode, Literal(f"IBAN-CHECK-PREM-{i:06d}", datatype=XSD_STRING)))
        g.add((acc, NS.overdraftLimitAmount, Literal("5000.00", datatype=XSD_DECIMAL)))

    for i in range(1, 9):
        acc = NS[f"acc_stud_{i:02d}"]
        g.add((acc, RDF.type, NS.StudentCheckingAccount))
        g.add((acc, RDF.type, NS.CheckingAccount))
        g.add((acc, RDF.type, NS.DepositoryAccount))
        g.add((acc, RDF.type, NS.FinancialAccount))
        g.add((acc, NS.accountBalanceCurrent, Literal(f"{1200.0 + i*150:.2f}", datatype=XSD_DECIMAL)))
        g.add((acc, NS.interestRateYield, Literal("0.005", datatype=XSD_DECIMAL)))
        g.add((acc, NS.ibanIdentifierCode, Literal(f"IBAN-CHECK-STUD-{i:06d}", datatype=XSD_STRING)))

    for i in range(1, 11):
        acc = NS[f"acc_hysa_{i:02d}"]
        g.add((acc, RDF.type, NS.HighYieldSavingsAccount))
        g.add((acc, RDF.type, NS.SavingsAccount))
        g.add((acc, RDF.type, NS.DepositoryAccount))
        g.add((acc, RDF.type, NS.FinancialAccount))
        g.add((acc, NS.accountBalanceCurrent, Literal(f"{50000.0 + i*10000:.2f}", datatype=XSD_DECIMAL)))
        g.add((acc, NS.interestRateYield, Literal("0.048", datatype=XSD_DECIMAL)))
        g.add((acc, NS.ibanIdentifierCode, Literal(f"IBAN-SAVE-HYSA-{i:06d}", datatype=XSD_STRING)))

    # CreditAccount / LoanAccount (Disjoint with DepositoryAccount)
    for i in range(1, 10):
        acc = NS[f"loan_mort_{i:02d}"]
        g.add((acc, RDF.type, NS.MortgageLoanAccount))
        g.add((acc, RDF.type, NS.LoanAccount))
        g.add((acc, RDF.type, NS.CreditAccount))
        g.add((acc, RDF.type, NS.FinancialAccount))
        g.add((acc, NS.principalLoanAmount, Literal(f"{450000.0 + i*30000:.2f}", datatype=XSD_DECIMAL)))
        g.add((acc, NS.loanInterestRate, Literal("0.062", datatype=XSD_DECIMAL)))
        g.add((acc, NS.loanMaturityTermMonths, Literal(360, datatype=XSD_INTEGER)))

    for i in range(1, 10):
        acc = NS[f"loan_auto_{i:02d}"]
        g.add((acc, RDF.type, NS.AutoLoanAccount))
        g.add((acc, RDF.type, NS.LoanAccount))
        g.add((acc, RDF.type, NS.CreditAccount))
        g.add((acc, RDF.type, NS.FinancialAccount))
        g.add((acc, NS.principalLoanAmount, Literal(f"{35000.0 + i*4000:.2f}", datatype=XSD_DECIMAL)))
        g.add((acc, NS.loanInterestRate, Literal("0.054", datatype=XSD_DECIMAL)))
        g.add((acc, NS.loanMaturityTermMonths, Literal(60, datatype=XSD_INTEGER)))

    # Injected Disjointness Violation Instance
    violator = NS["noisy_depository_mortgage"]
    g.add((violator, RDF.type, NS.PremiumCheckingAccount))
    g.add((violator, RDF.type, NS.MortgageLoanAccount))
    g.add((violator, NS.accountBalanceCurrent, Literal("150000.00", datatype=XSD_DECIMAL)))

    # 3. Equivalent Classes (Tarjan SCC 2-cycle)
    for i in range(1, 11):
        ac = NS[f"acc_holder_{i:02d}"]
        g.add((ac, RDF.type, NS.AccountHolder))
        g.add((ac, RDF.type, NS.BankClient))
        g.add((ac, NS.clientTaxIdentifier, Literal(f"TAX-ID-CLIENT-{i:04d}", datatype=XSD_STRING)))

    # 4. MFAS Directed Cycle
    for i in range(1, 6):
        ra = NS[f"risk_tier_a_{i:02d}"]
        g.add((ra, RDF.type, NS.RiskRatingTierA))
        g.add((ra, RDF.type, NS.RiskRatingTierB))
        rb = NS[f"risk_tier_b_{i:02d}"]
        g.add((rb, RDF.type, NS.RiskRatingTierB))
        g.add((rb, RDF.type, NS.RiskRatingTierC))
        rc = NS[f"risk_tier_c_{i:02d}"]
        g.add((rc, RDF.type, NS.RiskRatingTierC))
        g.add((rc, RDF.type, NS.RiskRatingTierA))

    # 5. Customers & Transactions
    for i in range(1, 16):
        cust = NS[f"bank_cust_{i:02d}"]
        g.add((cust, RDF.type, NS.FinancialCustomer))
        g.add((cust, NS.customerLegalName, Literal(f"Banking Customer {i}", datatype=XSD_STRING)))
        g.add((cust, NS.creditScoreFico, Literal(720 + (i * 5), datatype=XSD_INTEGER)))

    for i in range(1, 13):
        txn = NS[f"txn_{i:02d}"]
        g.add((txn, RDF.type, NS.FinancialTransaction))
        g.add((txn, NS.transactionAmountValue, Literal(f"{120.0 + i*35:.2f}", datatype=XSD_DECIMAL)))
        g.add((txn, NS.settlementTimestamp, Literal(f"2026-10-14T10:{i:02d}:00Z", datatype=XSD_STRING)))
        g.add((txn, NS.originatingAccount, NS[f"acc_prem_{min(i, 6):02d}"]))

    # Functional property: accountPrimaryOwner (Account -> Customer)
    for i in range(1, 7):
        g.add((NS[f"acc_prem_{i:02d}"], NS.accountPrimaryOwner, NS[f"bank_cust_{i:02d}"]))
        g.add((NS[f"acc_stud_{i:02d}"], NS.accountPrimaryOwner, NS[f"bank_cust_{i+7:02d}"]))

    # 6. Property Characteristics
    # Transitive: parentBranchOf (2 disjoint trees, 100% closed)
    br_east = [NS[f"branch_east_{i}"] for i in range(1, 4)]
    br_west = [NS[f"branch_west_{i}"] for i in range(1, 4)]
    for b in br_east + br_west:
        g.add((b, RDF.type, NS.BankBranch))
    g.add((br_east[0], NS.parentBranchOf, br_east[1]))
    g.add((br_east[1], NS.parentBranchOf, br_east[2]))
    g.add((br_east[0], NS.parentBranchOf, br_east[2]))
    g.add((br_west[0], NS.parentBranchOf, br_west[1]))
    g.add((br_west[1], NS.parentBranchOf, br_west[2]))
    g.add((br_west[0], NS.parentBranchOf, br_west[2]))

    # Symmetric: jointAccountWith (100% reciprocal pairs)
    for i in range(1, 5):
        c1 = NS[f"bank_cust_{i:02d}"]
        c2 = NS[f"bank_cust_{i+5:02d}"]
        g.add((c1, NS.jointAccountWith, c2))
        g.add((c2, NS.jointAccountWith, c1))

    # Near-transitive noise: wireTransferredTo (rho_trans = 0.50)
    g.add((br_east[0], NS.wireTransferredTo, br_east[1]))
    g.add((br_east[1], NS.wireTransferredTo, br_east[2]))
    g.add((br_west[0], NS.wireTransferredTo, br_west[1]))
    g.add((br_west[1], NS.wireTransferredTo, br_west[2]))
    g.add((br_west[0], NS.wireTransferredTo, br_west[2]))

    # Near-symmetric noise: coSignerWith (rho_sym = 0.67)
    g.add((NS["bank_cust_01"], NS.coSignerWith, NS["bank_cust_02"]))
    g.add((NS["bank_cust_02"], NS.coSignerWith, NS["bank_cust_01"]))
    g.add((NS["bank_cust_03"], NS.coSignerWith, NS["bank_cust_04"]))

    # 7. Untyped Entity Clusters (3 clusters, 8 entities each)
    for i in range(1, 9):
        tok = NS[f"token_{i:02d}"]
        g.add((NS[f"bank_cust_{min(i, 8):02d}"], NS.customerSecurityToken, tok))
        g.add((tok, NS.tokenSerialNumber, Literal(f"HW-TOKEN-RSA-900{i}", datatype=XSD_STRING)))
        g.add((tok, NS.securityAlgorithmType, Literal("TOTP-SHA256", datatype=XSD_STRING)))
        g.add((tok, NS.tokenExpirationTimestamp, Literal("2029-12-31T23:59:59Z", datatype=XSD_STRING)))

    for i in range(1, 9):
        col = NS[f"collateral_{i:02d}"]
        g.add((NS[f"loan_mort_{min(i, 7):02d}"], NS.securedByCollateral, col))
        g.add((col, NS.appraisedCollateralValue, Literal(f"{550000.0 + i*25000:.2f}", datatype=XSD_DECIMAL)))
        g.add((col, NS.collateralAssetType, Literal("ResidentialRealEstateProperty", datatype=XSD_STRING)))
        g.add((col, NS.pledgeDocumentId, Literal(f"DOC-PLEDGE-DEED-{i:05d}", datatype=XSD_STRING)))

    for i in range(1, 9):
        fee = NS[f"fee_sched_{i:02d}"]
        g.add((NS[f"acc_prem_{min(i, 6):02d}"], NS.governedByFeeSchedule, fee))
        g.add((fee, NS.monthlyMaintenanceFee, Literal(f"{15.0 + i*2:.2f}", datatype=XSD_DECIMAL)))
        g.add((fee, NS.penaltyChargeRate, Literal("0.05", datatype=XSD_DECIMAL)))
        g.add((fee, NS.feeScheduleVersion, Literal(f"v2026.{i}", datatype=XSD_STRING)))

    return g


# ==============================================================================
# Main Generation Function
# ==============================================================================
def main():
    benchmarks = [
        ("input/ecommerce_abox.ttl", build_ecommerce_graph),
        ("input/hospital_abox.ttl", build_hospital_graph),
        ("input/enterprise_abox.ttl", build_enterprise_graph),
        ("input/banking_abox.ttl", build_banking_graph),
    ]

    project_root = "/home/miskat/ABOX2TBOX"
    os.makedirs(os.path.join(project_root, "input"), exist_ok=True)

    summary = []
    for rel_path, builder_fn in benchmarks:
        full_path = os.path.join(project_root, rel_path)
        g = builder_fn()
        g.serialize(destination=full_path, format="turtle")
        triple_count = len(g)
        
        # Verify stats
        classes = set(g.objects(None, RDF.type))
        subjects = set(g.subjects())
        typed = set(g.subjects(RDF.type, None))
        untyped = subjects - typed
        
        # Untyped cluster count
        cs_map = defaultdict(list)
        for u in untyped:
            out_preds = sorted(set(g.predicates(u, None)))
            in_preds = sorted(set(g.predicates(None, u)))
            sig = (tuple(str(p) for p in out_preds), tuple(str(p) for p in in_preds))
            cs_map[sig].append(u)
            
        summary.append({
            "path": full_path,
            "rel_path": rel_path,
            "triples": triple_count,
            "classes": len(classes),
            "subjects": len(subjects),
            "untyped": len(untyped),
            "clusters": len(cs_map),
        })
        print(f"✔ Generated {rel_path}: {triple_count} triples, {len(classes)} explicit classes, {len(cs_map)} untyped clusters ({len(untyped)} instances).")

    print("\n" + "="*72)
    print("SUMMARY OF GENERATED BENCHMARK DATASETS")
    print("="*72)
    for s in summary:
        print(f"  • {s['rel_path']}:")
        print(f"      - Triples: {s['triples']} (Target: 500 – 1500)")
        print(f"      - Explicit Classes: {s['classes']}")
        print(f"      - Total Subjects: {s['subjects']}")
        print(f"      - Untyped Clusters: {s['clusters']} (24 entities)")
        assert 500 <= s['triples'] <= 1500, f"Triple count out of bounds: {s['triples']}"
        assert s['classes'] >= 15, f"Explicit class count below 15: {s['classes']}"
        assert s['clusters'] >= 3, f"Untyped clusters below 3: {s['clusters']}"
    print("\nAll dataset volume and taxonomy criteria satisfied successfully!")

if __name__ == "__main__":
    main()
