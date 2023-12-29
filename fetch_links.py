import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def get_domain(url):
    # Extract the domain from a given URL
    return urlparse(url).netloc

def get_all_links_in_domain(url, visited=set(), base_domain=None, max_links=None):
    try:
        # Fetch the HTML content of the webpage
        response = requests.get(url)
        response.raise_for_status()  # Check for any errors in the HTTP request

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract all hyperlinks from the webpage
        links = [a['href'] for a in soup.find_all('a', href=True)]

        # Convert relative URLs to absolute URLs
        links = [urljoin(url, link) for link in links]

        # Extract the base domain if not provided
        if base_domain is None:
            base_domain = get_domain(url)

        # Filter links to include only those within the same domain
        links = [link for link in links if get_domain(link) == base_domain]

        # Limit the number of links returned
        if max_links is not None:
            links = links[:max_links]

        return links

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []

def google_search_links(search_term, num_links=10):
    try:
        # Construct the Google search URL
        google_search_url = f"https://www.google.com/search?q={search_term}"

        # Fetch the HTML content of the search results page
        response = requests.get(google_search_url)
        response.raise_for_status()  # Check for any errors in the HTTP request

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract search result links from the webpage
        links = [a['href'] for a in soup.find_all('a', href=True) if '/url?q=' in a['href']]
        links = [link.replace("/url?q=", "") for link in links]

        # Return the specified number of search result links
        return links

    except requests.exceptions.RequestException as e:
        print(f"Error performing Google search for '{search_term}': {e}")
        return []


# Example usage:
if __name__ == "__main__":
    # input_url = 'https://www.rephrase.ai/'
    # input_depth = 2
    # max_links = 5
    # all_links = get_all_links_in_domain(input_url, input_depth, max_links=max_links)

    # all_links = list(set(all_links))

    # print("\nList of all hyperlinks:")
    # for link in all_links:
    #     print(link)

    search_term = 'Rephrase.ai location'
    num_links = 10
    
    search_links = google_search_links(search_term, num_links)

    print(f"\nTop {num_links} search result links for '{search_term}':")
    for link in search_links:
        print(link)
