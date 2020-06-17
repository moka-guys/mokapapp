mock_panel = {
	"id": 25,
	"hash_id": "58346b8b8f62036225ca8a7d",
	"name": "Congenital disorders of glycosylation",
	"disease_group": "Metabolic disorders",
	"disease_sub_group": "Specific metabolic abnormalities",
	"status": "public",
	"version": "1.26",
	"version_created": "2019-06-20T15:14:58.411762Z",
	"relevant_disorders": [
	"Congential disorders of glycosylation"
	],
	"stats": {
	"number_of_genes": 100,
	"number_of_regions": 0,
	"number_of_strs": 0
	},
	"types": [
	{
		"name": "Rare Disease 100K",
		"slug": "rare-disease-100k",
		"description": "Rare Disease 100K"
	}
	]
}

mock_json = '[{"moka_hash": "595ce30f8f62036352471f39_Amber", "name": "Adult solid tumours cancer susceptibility (Panel App Amber v1.6)","version": "1.6","genes": [["HGNC:25070", "ACD"], ["HGNC:358", "AIP"], ["HGNC:1097", "BRAF"], ["HGNC:16627", "CHEK2"], ["HGNC:26169", "CTC1"], ["HGNC:2890", "DKC1"], ["HGNC:3433", "ERCC1"], ["HGNC:3512", "EXT1"], ["HGNC:3513", "EXT2"], ["HGNC:6742", "LZTR1"], ["HGNC:6840", "MAP2K1"], ["HGNC:6842", "MAP2K2"], ["HGNC:8609", "PARN"], ["HGNC:9282", "PPP1CB"], ["HGNC:10023", "RIT1"], ["HGNC:23845", "SLX4"], ["HGNC:11188", "SOS2"], ["HGNC:11824", "TINF2"]], "colour": "Amber"}, {"id": "58c7f3c78f620328d77ce70e_Amber", "name": "Amelogenesis imperfecta (Panel App Amber v1.15)", "version": "1.15", "genes": [["HGNC:33188", "AMTN"], ["HGNC:2037", "CLDN16"], ["HGNC:2040", "CLDN19"], ["HGNC:6158", "ITGB4"], ["HGNC:6493", "LAMC2"], ["HGNC:22965", "PEX26"]], "colour": "Amber"}]'

gene = {
    "id": 25,
    "hash_id": "58346b8b8f62036225ca8a7d",
    "name": "Congenital disorders of glycosylation",
    "disease_group": "Metabolic disorders",
    "disease_sub_group": "Specific metabolic abnormalities",
    "status": "public",
    "version": "1.26",
    "version_created": "2019-06-20T15:14:58.411762Z",
    "relevant_disorders": [
        "Congential disorders of glycosylation"
    ],
    "stats": {
        "number_of_genes": 100,
        "number_of_regions": 0,
        "number_of_strs": 0
    },
    "types": [
        {
            "name": "Rare Disease 100K",
            "slug": "rare-disease-100k",
            "description": "Rare Disease 100K"
        }
    ],
    "genes": [
		{
            "gene_data": {
                "hgnc_id": "HGNC:32456",
                "biotype": "protein_coding",
                "ensembl_genes": {
                    "GRch38": {
                        "90": {
                            "location": "13:52012398-52029664",
                            "ensembl_id": "ENSG00000253710"
                        }
                    },
                    "GRch37": {
                        "82": {
                            "location": "13:52586534-52603800",
                            "ensembl_id": "ENSG00000253710"
                        }
                    }
                },
                "alias_name": [
                    "GDP-Man:Man(3)GlcNAc(2)-PP-dolichol alpha-1,2-mannosyltransferase"
                ],
                "gene_symbol": "ALG11",
                "alias": [
                    "KIAA0266",
                    "CDG1P"
                ],
                "omim_gene": [
                    "613666"
                ],
                "hgnc_release": "2017-11-03T00:00:00",
                "hgnc_date_symbol_changed": "2006-03-24",
                "gene_name": "ALG11, alpha-1,2-mannosyltransferase",
                "hgnc_symbol": "ALG11"
            },
            "entity_type": "gene",
            "entity_name": "ALG11",
            "confidence_level": "3",
            "penetrance": "Complete",
            "mode_of_pathogenicity": "",
            "publications": [
                "27604308",
                "22213132"
            ],
            "evidence": [
                "Expert Review Green",
                "UKGTN",
                "Radboud University Medical Center, Nijmegen",
                "Literature",
                "Illumina TruGenome Clinical Sequencing Services",
                "Emory Genetics Laboratory"
            ],
            "phenotypes": [
                "Congenital disorder of glycosylation, type Ip 613661",
                "ALG11-CDG (Disorders of protein N-glycosylation)"
            ],
            "mode_of_inheritance": "BIALLELIC, autosomal or pseudoautosomal",
            "tags": []
        },
		{
            "gene_data": {
                "hgnc_id": "HGNC:11022",
                "biotype": "protein_coding",
                "ensembl_genes": {
                    "GRch38": {
                        "90": {
                            "location": "X:48903180-48911958",
                            "ensembl_id": "ENSG00000102100"
                        }
                    },
                    "GRch37": {
                        "82": {
                            "location": "X:48760459-48769235",
                            "ensembl_id": "ENSG00000102100"
                        }
                    }
                },
                "alias_name": None,
                "gene_symbol": "SLC35A2",
                "alias": [
                    "UGAT",
                    "UGT",
                    "UGT1",
                    "UGT2",
                    "UGTL"
                ],
                "omim_gene": [
                    "314375"
                ],
                "hgnc_release": "2017-11-03T00:00:00",
                "hgnc_date_symbol_changed": "1995-02-24",
                "gene_name": "solute carrier family 35 member A2",
                "hgnc_symbol": "SLC35A2"
            },
            "entity_type": "gene",
            "entity_name": "SLC35A2",
            "confidence_level": "2",
            "penetrance": "Complete",
            "mode_of_pathogenicity": "",
            "publications": [
                "25778940",
                "27743886",
                "23561849"
            ],
            "evidence": [
                "Expert Review Amber",
                "UKGTN",
                "Radboud University Medical Center, Nijmegen",
                "Other"
            ],
            "phenotypes": [
                "Congenital disorder of glycosylation, type IIm 300896"
            ],
            "mode_of_inheritance": "X-LINKED: hemizygous mutation in males, monoallelic mutations in females may cause disease (may be less severe, later onset than males)",
            "tags": [
                "mosaicism"
            ]
        },
        {
            "gene_data": {
                "hgnc_id": "HGNC:28287",
                "biotype": "protein_coding",
                "ensembl_genes": {
                    "GRch38": {
                        "90": {
                            "location": "1:94974407-95072945",
                            "ensembl_id": "ENSG00000172339"
                        }
                    },
                    "GRch37": {
                        "82": {
                            "location": "1:95439963-95538501",
                            "ensembl_id": "ENSG00000172339"
                        }
                    }
                },
                "alias_name": None,
                "gene_symbol": "ALG14",
                "alias": [
                    "MGC19780"
                ],
                "omim_gene": [
                    "612866"
                ],
                "hgnc_release": "2017-11-03T00:00:00",
                "hgnc_date_symbol_changed": "2005-08-09",
                "gene_name": "ALG14, UDP-N-acetylglucosaminyltransferase subunit",
                "hgnc_symbol": "ALG14"
            },
            "entity_type": "gene",
            "entity_name": "ALG14",
            "confidence_level": "1",
            "penetrance": "Complete",
            "mode_of_pathogenicity": "",
            "publications": [
                "27604308",
                "23404334"
            ],
            "evidence": [
                "Expert Review Red",
                "Literature"
            ],
            "phenotypes": [
                "?Myasthenic syndrome, congenital, 15, without tubular aggregates 616227",
                "Congenital myasthenic sydrome (Disorders of protein N-glycosylation)"
            ],
            "mode_of_inheritance": "BIALLELIC, autosomal or pseudoautosomal",
            "tags": []
        }
	]
}		