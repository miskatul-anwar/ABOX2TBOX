#!/usr/bin/env python3
"""generate_benchmarks.py - Multi-Domain Synthetic Benchmark Datasets Generator.

Generates 4 distinct real-world domain ABox Turtle datasets:
  1. input/ecommerce_abox.ttl
  2. input/hospital_abox.ttl
  3. input/enterprise_abox.ttl
  4. input/banking_abox.ttl

Each dataset fulfills all Milestone 1 criteria:
  - 500 to 1500 RDF triples.
  - Distinct namespaces and real-world domain entities.
  - Multi-level class hierarchies (Root -> SuperClass -> SubClass -> LeafClass).
  - 3 untyped entity clusters with homogeneous characteristic sets.
  - Disjointness boundaries (e.g. Physical vs Digital, Inpatient vs Outpatient, etc.).
  - Object property algebraic characteristics (Transitive, Symmetric, Functional, InverseFunctional).
  - Intentional stress-test noise (Tarjan SCC 2-cycle, MFAS directed cycle, Transitive shortcut, injected disjointness violation, near-transitive/near-symmetric noise).
"""

import os
import rdflib
from rdflib import Graph, Literal, Namespace, RDF, RDFS, XSD, URIRef
from collections import defaultdict
import networkx as nx

XSD_STRING = XSD.string
XSD_DECIMAL = XSD.decimal
XSD_INTEGER = XSD.integer
XSD_BOOLEAN = XSD.boolean

def build_ecommerce_graph() -> Graph:
    g = Graph()
    NS = Namespace("http://example.org/ecommerce#")
    g.bind("", NS)
    g.bind("xsd", XSD)

    # ---------------------------------------------------------
    # 1. Product Hierarchy (4 levels)
    # Product (Root)
    #   PhysicalProduct (Super) [DISJOINT with DigitalProduct]
    #     ConsumerElectronics (Sub)
    #       Smartphone (Leaf) - 6 insts
    #       Laptop (Leaf) - 6 insts
    #     Apparel (Sub)
    #       Footwear (Leaf) - 6 insts
    #       Outerwear (Leaf) - 6 insts
    #   DigitalProduct (Super) [DISJOINT with PhysicalProduct]
    #     SoftwareProduct (Sub)
    #       MobileApp (Leaf) - 4 insts
    #       OperatingSystem (Leaf) - 4 insts
    #     DigitalMedia (Sub)
    #       EBook (Leaf) - 4 insts
    #       AudioAlbum (Leaf) - 4 insts
    # ---------------------------------------------------------
    
    # Physical Products
    for i in range(1, 7):
        p = NS[f"phone_{i:02d}"]
        g.add((p, RDF.type, NS.Smartphone))
        g.add((p, RDF.type, NS.ConsumerElectronics))
        g.add((p, RDF.type, NS.PhysicalProduct))
        g.add((p, RDF.type, NS.Product)) # Transitive edge for reduction
        g.add((p, NS.productTitle, Literal(f"Smartphone Galaxy Model X{i}", datatype=XSD_STRING)))
        g.add((p, NS.unitPrice, Literal(f"{499.0 + i*50:.2f}", datatype=XSD_DECIMAL)))
        g.add((p, NS.skuCode, Literal(f"SKU-PH-{i:04d}", datatype=XSD_STRING)))
        g.add((p, NS.inStockUnits, Literal(10 + i * 5, datatype=XSD_INTEGER)))

    for i in range(1, 7):
        p = NS[f"laptop_{i:02d}"]
        g.add((p, RDF.type, NS.Laptop))
        g.add((p, RDF.type, NS.ConsumerElectronics))
        g.add((p, RDF.type, NS.PhysicalProduct))
        g.add((p, RDF.type, NS.Product))
        g.add((p, NS.productTitle, Literal(f"ProBook Laptop Ultra {i}", datatype=XSD_STRING)))
        g.add((p, NS.unitPrice, Literal(f"{899.0 + i*100:.2f}", datatype=XSD_DECIMAL)))
        g.add((p, NS.skuCode, Literal(f"SKU-LP-{i:04d}", datatype=XSD_STRING)))
        g.add((p, NS.inStockUnits, Literal(5 + i * 2, datatype=XSD_INTEGER)))

    for i in range(1, 7):
        p = NS[f"shoes_{i:02d}"]
        g.add((p, RDF.type, NS.Footwear))
        g.add((p, RDF.type, NS.Apparel))
        g.add((p, RDF.type, NS.PhysicalProduct))
        g.add((p, RDF.type, NS.Product))
        g.add((p, NS.productTitle, Literal(f"Runner Sport Sneaker {i}", datatype=XSD_STRING)))
        g.add((p, NS.unitPrice, Literal(f"{79.0 + i*10:.2f}", datatype=XSD_DECIMAL)))
        g.add((p, NS.skuCode, Literal(f"SKU-SH-{i:04d}", datatype=XSD_STRING)))

    for i in range(1, 7):
        p = NS[f"jacket_{i:02d}"]
        g.add((p, RDF.type, NS.Outerwear))
        g.add((p, RDF.type, NS.Apparel))
        g.add((p, RDF.type, NS.PhysicalProduct))
        g.add((p, RDF.type, NS.Product))
        g.add((p, NS.productTitle, Literal(f"Thermal Winter Jacket {i}", datatype=XSD_STRING)))
        g.add((p, NS.unitPrice, Literal(f"{129.0 + i*15:.2f}", datatype=XSD_DECIMAL)))
        g.add((p, NS.skuCode, Literal(f"SKU-JK-{i:04d}", datatype=XSD_STRING)))

    # Digital Products
    for i in range(1, 5):
        p = NS[f"app_{i:02d}"]
        g.add((p, RDF.type, NS.MobileApp))
        g.add((p, RDF.type, NS.SoftwareProduct))
        g.add((p, RDF.type, NS.DigitalProduct))
        g.add((p, RDF.type, NS.Product))
        g.add((p, NS.productTitle, Literal(f"Productivity Assistant App v{i}", datatype=XSD_STRING)))
        g.add((p, NS.unitPrice, Literal(f"{9.99 + i:.2f}", datatype=XSD_DECIMAL)))
        g.add((p, NS.downloadUrl, Literal(f"https://store.example.org/dl/app_{i}", datatype=XSD_STRING)))

    for i in range(1, 5):
        p = NS[f"os_{i:02d}"]
        g.add((p, RDF.type, NS.OperatingSystem))
        g.add((p, RDF.type, NS.SoftwareProduct))
        g.add((p, RDF.type, NS.DigitalProduct))
        g.add((p, RDF.type, NS.Product))
        g.add((p, NS.productTitle, Literal(f"CloudOS Enterprise Suite {i}", datatype=XSD_STRING)))
        g.add((p, NS.unitPrice, Literal(f"{199.99 + i*20:.2f}", datatype=XSD_DECIMAL)))
        g.add((p, NS.downloadUrl, Literal(f"https://store.example.org/dl/os_{i}", datatype=XSD_STRING)))

    for i in range(1, 5):
        p = NS[f"ebook_{i:02d}"]
        g.add((p, RDF.type, NS.EBook))
        g.add((p, RDF.type, NS.DigitalMedia))
        g.add((p, RDF.type, NS.DigitalProduct))
        g.add((p, RDF.type, NS.Product))
        g.add((p, NS.productTitle, Literal(f"Knowledge Graph Architecture Vol {i}", datatype=XSD_STRING)))
        g.add((p, NS.unitPrice, Literal(f"{14.99 + i:.2f}", datatype=XSD_DECIMAL)))

    for i in range(1, 5):
        p = NS[f"album_{i:02d}"]
        g.add((p, RDF.type, NS.AudioAlbum))
        g.add((p, RDF.type, NS.DigitalMedia))
        g.add((p, RDF.type, NS.DigitalProduct))
        g.add((p, RDF.type, NS.Product))
        g.add((p, NS.productTitle, Literal(f"Symphonic Soundtrack Session {i}", datatype=XSD_STRING)))
        g.add((p, NS.unitPrice, Literal(f"{11.99 + i:.2f}", datatype=XSD_DECIMAL)))

    # Injected Disjointness Violation Instance
    # Injected instance asserts both Smartphone (descendant of PhysicalProduct) and EBook (descendant of DigitalProduct)
    # PhysicalProduct and DigitalProduct have zero overlap across all other instances.
    violator = NS["noisy_hybrid_product"]
    g.add((violator, RDF.type, NS.Smartphone))
    g.add((violator, RDF.type, NS.EBook))
    g.add((violator, NS.productTitle, Literal("Noisy Hybrid Smart-Book E-Reader", datatype=XSD_STRING)))
    g.add((violator, NS.unitPrice, Literal("299.99", datatype=XSD_DECIMAL)))

    # ---------------------------------------------------------
    # 2. Customer & Supplier Hierarchy (4 levels)
    # Party (Root)
    #   Customer (Super)
    #     RegisteredCustomer (Sub)
    #       VIPCustomer (Sub)
    #         PlatinumVIPCustomer (Leaf) - 3 insts
    #   Supplier (Super)
    #     VerifiedSupplier (Sub)
    #       DomesticSupplier (Leaf) - 4 insts
    #       InternationalSupplier (Leaf) - 4 insts
    # ---------------------------------------------------------
    for i in range(1, 4):
        c = NS[f"cust_plat_{i:02d}"]
        g.add((c, RDF.type, NS.PlatinumVIPCustomer))
        g.add((c, RDF.type, NS.VIPCustomer))
        g.add((c, RDF.type, NS.RegisteredCustomer))
        g.add((c, RDF.type, NS.Customer))
        g.add((c, RDF.type, NS.Party))
        g.add((c, NS.customerName, Literal(f"Platinum Member {i}", datatype=XSD_STRING)))
        g.add((c, NS.primaryEmail, Literal(f"plat.{i}@domain.com", datatype=XSD_STRING)))
        g.add((c, NS.loyaltyPoints, Literal(5000 + i*1000, datatype=XSD_INTEGER)))

    for i in range(4, 8):
        c = NS[f"cust_vip_{i:02d}"]
        g.add((c, RDF.type, NS.VIPCustomer))
        g.add((c, RDF.type, NS.RegisteredCustomer))
        g.add((c, RDF.type, NS.Customer))
        g.add((c, RDF.type, NS.Party))
        g.add((c, NS.customerName, Literal(f"VIP Member {i}", datatype=XSD_STRING)))
        g.add((c, NS.primaryEmail, Literal(f"vip.{i}@domain.com", datatype=XSD_STRING)))
        g.add((c, NS.loyaltyPoints, Literal(2000 + i*200, datatype=XSD_INTEGER)))

    for i in range(8, 15):
        c = NS[f"cust_reg_{i:02d}"]
        g.add((c, RDF.type, NS.RegisteredCustomer))
        g.add((c, RDF.type, NS.Customer))
        g.add((c, RDF.type, NS.Party))
        g.add((c, NS.customerName, Literal(f"Standard Member {i}", datatype=XSD_STRING)))
        g.add((c, NS.primaryEmail, Literal(f"reg.{i}@domain.com", datatype=XSD_STRING)))

    # Suppliers
    for i in range(1, 5):
        s = NS[f"supp_dom_{i:02d}"]
        g.add((s, RDF.type, NS.DomesticSupplier))
        g.add((s, RDF.type, NS.VerifiedSupplier))
        g.add((s, RDF.type, NS.Supplier))
        g.add((s, RDF.type, NS.Party))
        g.add((s, NS.supplierName, Literal(f"Domestic Tech Logistics {i}", datatype=XSD_STRING)))
        g.add((s, NS.supplierCountry, Literal("United States", datatype=XSD_STRING)))

    for i in range(1, 5):
        s = NS[f"supp_int_{i:02d}"]
        g.add((s, RDF.type, NS.InternationalSupplier))
        g.add((s, RDF.type, NS.VerifiedSupplier))
        g.add((s, RDF.type, NS.Supplier))
        g.add((s, RDF.type, NS.Party))
        g.add((s, NS.supplierName, Literal(f"Global Freight Alliance {i}", datatype=XSD_STRING)))
        g.add((s, NS.supplierCountry, Literal(f"Country-{i}", datatype=XSD_STRING)))

    # ---------------------------------------------------------
    # 3. Equivalent Classes (Tarjan SCC 2-cycle)
    # Buyer and Purchaser have identical 10 instances
    # ---------------------------------------------------------
    for i in range(1, 11):
        bp = NS[f"buyer_purchaser_{i:02d}"]
        g.add((bp, RDF.type, NS.Buyer))
        g.add((bp, RDF.type, NS.Purchaser))
        g.add((bp, NS.accountIdentifier, Literal(f"ACC-BP-{i:03d}", datatype=XSD_STRING)))

    # ---------------------------------------------------------
    # 4. Directed cycle back-edge / MFAS Cycle
    # ReviewTierA -> ReviewTierB -> ReviewTierC -> ReviewTierA
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # 5. Orders, Categories, Reviews
    # ---------------------------------------------------------
    for i in range(1, 11):
        ord_uri = NS[f"order_{i:02d}"]
        g.add((ord_uri, RDF.type, NS.Order))
        g.add((ord_uri, NS.orderTotalAmount, Literal(f"{150.0 + i*25:.2f}", datatype=XSD_DECIMAL)))
        g.add((ord_uri, NS.placedByCustomer, NS[f"cust_reg_{i+4:02d}"]))
        g.add((ord_uri, NS.includesProduct, NS[f"phone_{min(i, 6):02d}"]))

    for i in range(1, 9):
        rev = NS[f"review_{i:02d}"]
        g.add((rev, RDF.type, NS.ProductReview))
        g.add((rev, NS.reviewRating, Literal(4 + (i % 2), datatype=XSD_INTEGER)))
        g.add((rev, NS.reviewText, Literal(f"Excellent product performance and fast delivery #{i}", datatype=XSD_STRING)))
        g.add((rev, NS.reviewsProduct, NS[f"laptop_{min(i, 6):02d}"]))

    # ---------------------------------------------------------
    # 6. Object Property Characteristics
    # Transitive: isSubCategoryOf (cat1 sub cat2 sub cat3 ...)
    # ---------------------------------------------------------
    categories = [NS[f"category_{i:02d}"] for i in range(1, 7)]
    for c in categories:
        g.add((c, RDF.type, NS.ProductCategory))
    # Chain: 1 -> 2 -> 3, with transitive edge 1 -> 3
    g.add((categories[0], NS.isSubCategoryOf, categories[1]))
    g.add((categories[1], NS.isSubCategoryOf, categories[2]))
    g.add((categories[0], NS.isSubCategoryOf, categories[2]))
    # Chain: 3 -> 4 -> 5, with transitive edge 3 -> 5
    g.add((categories[2], NS.isSubCategoryOf, categories[3]))
    g.add((categories[3], NS.isSubCategoryOf, categories[4]))
    g.add((categories[2], NS.isSubCategoryOf, categories[4]))

    # Symmetric: frequentlyBoughtTogether
    for i in range(1, 5):
        p1 = NS[f"phone_{i:02d}"]
        p2 = NS[f"shoes_{i:02d}"]
        g.add((p1, NS.frequentlyBoughtTogether, p2))
        g.add((p2, NS.frequentlyBoughtTogether, p1))

    # Functional: primaryContactPerson (Order -> Customer has functional characteristic)
    for i in range(1, 9):
        g.add((NS[f"order_{i:02d}"], NS.primaryContactCustomer, NS[f"cust_reg_{i+4:02d}"]))

    # InverseFunctional: trackingCode
    for i in range(1, 9):
        g.add((NS[f"order_{i:02d}"], NS.trackingCode, Literal(f"TRK-ECOMM-{i:06d}", datatype=XSD_STRING)))

    # Empirical property noise:
    # Near-transitive (0.15): crossPromotedWith (only 1 transitive shortcut out of 6 pairs)
    g.add((categories[0], NS.crossPromotedWith, categories[1]))
    g.add((categories[1], NS.crossPromotedWith, categories[2]))
    g.add((categories[3], NS.crossPromotedWith, categories[4]))
    g.add((categories[4], NS.crossPromotedWith, categories[5]))

    # Near-symmetric (0.50): recommendedWith (some pairs symmetric, some directed)
    g.add((NS["phone_01"], NS.recommendedWith, NS["laptop_01"]))
    g.add((NS["laptop_01"], NS.recommendedWith, NS["phone_01"]))
    g.add((NS["phone_02"], NS.recommendedWith, NS["laptop_02"]))

    # ---------------------------------------------------------
    # 7. Untyped Entity Clusters (3 distinct clusters, NO rdf:type)
    # Cluster 1: Shipment Tracking entities
    # Cluster 2: Promotion / Coupon entities
    # Cluster 3: Technical Specification entities
    # ---------------------------------------------------------
    for i in range(1, 9):
        sh = NS[f"shipment_{i:02d}"]
        # Incoming from order
        g.add((NS[f"order_{min(i, 8):02d}"], NS.orderHasShipment, sh))
        # Outgoing
        g.add((sh, NS.trackingNumber, Literal(f"TRACK-FEDEX-900{i}", datatype=XSD_STRING)))
        g.add((sh, NS.shippingCarrier, Literal("FederalExpress", datatype=XSD_STRING)))
        g.add((sh, NS.shippingStatus, Literal("InTransit", datatype=XSD_STRING)))

    for i in range(1, 9):
        pr = NS[f"promo_{i:02d}"]
        # Incoming from order
        g.add((NS[f"order_{min(i, 8):02d}"], NS.appliedPromotion, pr))
        # Outgoing
        g.add((pr, NS.couponCode, Literal(f"DISCOUNT{i*5}", datatype=XSD_STRING)))
        g.add((pr, NS.discountPercentage, Literal(5 + i * 2, datatype=XSD_INTEGER)))
        g.add((pr, NS.promotionTitle, Literal(f"Seasonal Promotion {i}", datatype=XSD_STRING)))

    for i in range(1, 9):
        sp = NS[f"spec_{i:02d}"]
        # Incoming from product
        g.add((NS[f"phone_{min(i, 6):02d}"], NS.hasSpecification, sp))
        # Outgoing
        g.add((sp, NS.dimensionMeasurement, Literal(f"150x75x8.{i} mm", datatype=XSD_STRING)))
        g.add((sp, NS.technicalWeight, Literal(f"18{i} grams", datatype=XSD_STRING)))
        g.add((sp, NS.warrantyPeriod, Literal("24 Months", datatype=XSD_STRING)))

    return g

print("E-commerce builder defined.")
