"""
Exa.ai Multi-Angle Deep Research & Verification Script for GEO 2026
Author: Raphael Rechberger
Project: Heartweb Claude Desktop SEO Workflow
"""

import os
import json
import dotenv
from exa_py import Exa

# Load environment
dotenv.load_dotenv(r"C:\Users\offic\AppData\Local\hermes\.env")
api_key = os.getenv("EXA_API_KEY")

if not api_key:
    raise ValueError("EXA_API_KEY not found in environment!")

exa = Exa(api_key=api_key)

research_tasks = [
    {
        "category": "Google AI Overviews 2026 Ranking & Passage Factors",
        "queries": [
            "Google AI Overviews ranking factors 2026 citation inclusion criteria study",
            "Google AI Overviews passage extraction length definition block semantic completeness",
            "percentage AI Overview citations top 10 organic rankings study 2025 2026"
        ]
    },
    {
        "category": "Perplexity AI RAG & Citation Architecture 2026",
        "queries": [
            "How Perplexity AI selects sources citations RAG pipeline reranker 2025 2026",
            "Perplexity SEO ranking signals citation rate domain authority freshness 2026"
        ]
    },
    {
        "category": "Claude Web Search & SearchGPT / ChatGPT Search Mechanics",
        "queries": [
            "How to get cited by Claude web search ClaudeBot Claude-SearchBot Brave Search 2026",
            "SearchGPT ChatGPT search citation ranking factors OAI-SearchBot 2025 2026"
        ]
    },
    {
        "category": "Schema.org, Semantic Triples & Entity Graph Grounding (Wikidata)",
        "queries": [
            "Schema.org about mentions sameAs Wikidata Generative Engine Optimization LLM",
            "Semantic triples subject predicate object Knowledge Graph RAG retrieval"
        ]
    },
    {
        "category": "Princeton GEO Study & Information Gain Metrics",
        "queries": [
            "Princeton GEO Generative Engine Optimization Aggarwal visibility statistics 40 percent",
            "Information Gain SEO Google patent AI search citation score"
        ]
    }
]

all_results = {}

for task in research_tasks:
    category = task["category"]
    print(f"=== Researching: {category} ===")
    all_results[category] = []
    
    for query in task["queries"]:
        print(f"  -> Query: {query}")
        try:
            res = exa.search_and_contents(
                query,
                type="auto",
                num_results=4,
                text={"max_characters": 2500},
                highlights={"num_sentences": 3, "highlights_per_url": 2}
            )
            
            items = []
            for item in res.results:
                items.append({
                    "title": item.title,
                    "url": item.url,
                    "published_date": getattr(item, "published_date", None),
                    "highlights": getattr(item, "highlights", []),
                    "text": item.text[:2000] if item.text else ""
                })
            
            all_results[category].append({
                "query": query,
                "results": items
            })
        except Exception as e:
            print(f"    Error querying '{query}': {e}")
            all_results[category].append({
                "query": query,
                "error": str(e)
            })

# Save raw output
output_path = r"C:\Users\offic\Documents\Projekte\Hermes\04_projects\active\Heartweb-Claude-Desktop-SEO-Workflow\03_research\exa_geo_research_raw.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)

print(f"\n[SUCCESS] Raw research saved to: {output_path}")
