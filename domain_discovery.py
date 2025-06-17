#!/usr/bin/env python3
"""
Domain Discovery Module
Provides multiple strategies for discovering internet domain names for organizations.
"""

import re
import socket
import requests
from bs4 import BeautifulSoup

# HTTP headers for web requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def is_valid_domain(domain):
    """Validate domain name format using regex"""
    if not domain:
        return False
        
    # Define a regular expression pattern for domain validation
    domain_pattern = re.compile(
        r'^(?!:\/\/)(?!www\.)(?!http:\/\/)(?!https:\/\/)'  # Exclude URLs and www
        r'((?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,})$'
    )
    
    return bool(domain_pattern.match(domain))

def is_domain_exists(domain):
    """Check if domain exists via DNS lookup"""
    try:
        socket.gethostbyname(domain)
        return True
    except socket.error:
        return False

def search_domain_web(victim):
    """Search for domain using web search (Google)"""
    try:
        search_query = f"{victim} official website domain"
        search_url = f"https://www.google.com/search?q={search_query}"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for domain patterns in search results
        domain_pattern = r'https?://(?:www\.)?([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}'
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            match = re.search(domain_pattern, href)
            if match:
                full_url = match.group(0)
                domain = full_url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
                if victim.lower().replace(' ', '') in domain.lower() or domain.lower() in victim.lower().replace(' ', ''):
                    return domain
        
        return None
    except Exception as e:
        print(f"Web search failed: {e}")
        return None

def discover_domain_llm(victim, client, model='llama-3.3-70b-versatile'):
    """Discover domain using LLM with enhanced prompting"""
    try:
        messages = [
            {'role': 'system', 'content': 'You are a domain name expert. Provide only the primary domain name (e.g., example.com) without www, protocols, or paths.'},
            {'role': 'user', 'content': f'What is the primary internet domain name for the organization "{victim}"? Return only the domain name (like company.com), nothing else.'}
        ]
        domain_response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=20,
            n=1,
            temperature=0.1
        )
        domain_name = domain_response.choices[0].message.content.strip()
        
        # Clean up the response
        domain_name = domain_name.replace('www.', '').replace('http://', '').replace('https://', '').split('/')[0].split()[0]
        
        return domain_name if domain_name else None
            
    except Exception as e:
        print(f"LLM domain discovery failed: {e}")
        return None

def discover_domain_patterns(victim):
    """Try common domain name patterns based on company name"""
    try:
        company_name = victim.lower().replace(' ', '').replace(',', '').replace('.', '').replace('-', '')
        common_patterns = [
            f"{company_name}.com",
            f"{company_name}.org",
            f"{company_name}.net",
            f"{company_name}inc.com",
            f"{company_name}corp.com",
            f"{company_name}llc.com",
            f"{company_name}group.com",
            f"{company_name}company.com"
        ]
        
        for pattern in common_patterns:
            if is_valid_domain(pattern) and is_domain_exists(pattern):
                return pattern
                
        return None
                
    except Exception as e:
        print(f"Pattern matching failed: {e}")
        return None

def discover_domain_llm_alternatives(victim, client, model='llama-3.3-70b-versatile'):
    """Ask LLM for multiple domain suggestions"""
    try:
        messages = [
            {'role': 'system', 'content': 'You are a domain name expert. Provide 3 possible domain names for this organization, one per line, domain only.'},
            {'role': 'user', 'content': f'What are 3 possible domain names for "{victim}"? List only domain names like company.com, one per line.'}
        ]
        alternatives_response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=50,
            n=1,
            temperature=0.3
        )
        
        alternatives = alternatives_response.choices[0].message.content.strip().split('\n')
        
        for alt_domain in alternatives:
            alt_domain = alt_domain.strip().replace('www.', '').replace('http://', '').replace('https://', '').split('/')[0].split()[0]
            if is_valid_domain(alt_domain) and is_domain_exists(alt_domain):
                return alt_domain
                
        return None
                
    except Exception as e:
        print(f"Alternative domain discovery failed: {e}")
        return None

def discover_domain(victim, client=None, model='llama-3.3-70b-versatile', enable_web_search=False, verbose=True):
    """
    Discover domain using multiple strategies in fallback order.
    
    Args:
        victim (str): Organization name
        client: LLM client (optional, for LLM-based strategies)
        model (str): LLM model to use
        enable_web_search (bool): Whether to enable web search (may hit rate limits)
        verbose (bool): Whether to print progress messages
    
    Returns:
        str: Discovered domain name or empty string if none found
    """
    
    if verbose:
        print(f"Discovering domain for: {victim}")
    
    # Strategy 1: Enhanced LLM prompting
    if client:
        domain_name = discover_domain_llm(victim, client, model)
        if domain_name and is_valid_domain(domain_name) and is_domain_exists(domain_name):
            if verbose:
                print(f"LLM domain validated: {domain_name}")
            return domain_name
        elif verbose and domain_name:
            print(f"LLM suggested invalid/non-existent domain: {domain_name}")
    
    # Strategy 2: Try common domain patterns
    domain_name = discover_domain_patterns(victim)
    if domain_name:
        if verbose:
            print(f"Pattern match found: {domain_name}")
        return domain_name
    
    # Strategy 3: Web search (optional)
    if enable_web_search:
        domain_name = search_domain_web(victim)
        if domain_name and is_valid_domain(domain_name) and is_domain_exists(domain_name):
            if verbose:
                print(f"Web search found: {domain_name}")
            return domain_name
    
    # Strategy 4: Ask LLM for alternative suggestions
    if client:
        domain_name = discover_domain_llm_alternatives(victim, client, model)
        if domain_name:
            if verbose:
                print(f"Alternative domain found: {domain_name}")
            return domain_name
    
    if verbose:
        print(f"No valid domain found for {victim}")
    return ""

def main():
    """Command line interface for testing domain discovery"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Discover domain name for an organization')
    parser.add_argument('organization', help='Organization name to find domain for')
    parser.add_argument('--web-search', action='store_true', help='Enable web search (may hit rate limits)')
    parser.add_argument('--quiet', action='store_true', help='Reduce output verbosity')
    
    args = parser.parse_args()
    
    # Test without LLM client
    domain = discover_domain(
        args.organization, 
        client=None,
        enable_web_search=args.web_search,
        verbose=not args.quiet
    )
    
    if domain:
        print(f"Found domain: {domain}")
    else:
        print("No domain found")

if __name__ == '__main__':
    main()