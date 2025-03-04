import os
import requests
import xmltodict
import json

def fetch_pubmed_papers(query, max_results=5):
    """Fetches PubMed articles using an API key stored in an environment variable."""
    api_key = os.getenv("PUBMED_API_KEY")
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    # Step 1: Search for article PMIDs
    search_url = f"{base_url}esearch.fcgi?db=pubmed&term={query}&retmax={max_results}&retmode=json"
    if api_key:
        search_url += f"&api_key={api_key}"

    search_response = requests.get(search_url)
    search_data = search_response.json()

    if "esearchresult" not in search_data:
        print("Error: 'esearchresult' not found in response.")
        return []

    article_ids = search_data["esearchresult"]["idlist"]

    # Step 2: Fetch article details
    details_url = f"{base_url}efetch.fcgi?db=pubmed&id={','.join(article_ids)}&retmode=xml"
    if api_key:
        details_url += f"&api_key={api_key}"

    details_response = requests.get(details_url)
    articles = xmltodict.parse(details_response.content)

    extracted_data = []
    for article in articles["PubmedArticleSet"]["PubmedArticle"]:
        medline = article["MedlineCitation"]
        pub_info = medline["Article"]

        # Handle the Abstract text
        raw_abstract = pub_info.get("Abstract", {}).get("AbstractText", "No abstract available")
        if isinstance(raw_abstract, list):
            abstract = " ".join(
                section["#text"] for section in raw_abstract if "#text" in section
            )
        elif isinstance(raw_abstract, str):
            abstract = raw_abstract
        else:
            abstract = "No abstract available"

        # Handle the publication date
        article_date = pub_info.get("ArticleDate", {})
        publication_date = article_date.get("Year", "Unknown")

        # Handle the ELocationID, which can be a dict or a list
        e_location_data = pub_info.get("ELocationID", [])
        
        # Default
        doi = "No DOI available"

        # Case 1: ELocationID is a dict
        if isinstance(e_location_data, dict):
            # Check if it's a DOI
            if e_location_data.get("@EIdType") == "doi":
                doi = e_location_data.get("#text", "No DOI available")
        
        # Case 2: ELocationID is a list
        elif isinstance(e_location_data, list):
            for loc in e_location_data:
                # Each `loc` is typically a dict
                if isinstance(loc, dict) and loc.get("@EIdType") == "doi":
                    doi = loc.get("#text", "No DOI available")
                    break  # Stop after the first DOI found

        data = {
            "pmid": medline["PMID"]["#text"],
            "title": pub_info["ArticleTitle"],
            "abstract": abstract,
            "authors": [
                f"{a['ForeName']} {a['LastName']}"
                for a in pub_info.get("AuthorList", {}).get("Author", [])
                if isinstance(a, dict)
            ],
            "journal": pub_info["Journal"]["Title"],
            "publication_date": publication_date,
            "doi": doi,
            "pubmed_link": f"https://pubmed.ncbi.nlm.nih.gov/{medline['PMID']['#text']}/"
        }
        extracted_data.append(data)

    # Save results to JSON file
    with open("pubmed_articles_clean.json", "w") as f:
        json.dump(extracted_data, f, indent=4)

    return extracted_data

# Example usage:
if __name__ == "__main__":
    papers = fetch_pubmed_papers("diabetes treatment", max_results=50)
    print(json.dumps(papers, indent=2))
