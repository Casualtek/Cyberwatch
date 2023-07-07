#!/usr/bin/python3
import openai
import json
import sys
import os
from datetime import datetime, timedelta

openai.api_key = os.environ['OPENAI_API_KEY']

def load_articles_from_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            articles = json.load(f)
            return articles
    else:
        return []

def ask_chatgpt(news_count,most_hit_region,most_hit_country):
    messages = [
        {'role': 'system', 'content': 'Tu es un journaliste spécialisé en cybersécurité. Tu prépares une revue de presse portant sur les cyberattaques rapportées dans la presse au cours du mois dernier.'},
        {'role': 'user', 'content': f'Rédige le texte d\'introduction de la revue de presse pour le mois dernier, sachant que nous avons observé {news_count} cyberattaques évoquées dans les médias à travers le monde. Précise que la région la plus représentée est {most_hit_region} et que le pays le plus affecté est {most_hit_country["country"]} avec {most_hit_country["count"]} cas constatés. Pense à rappeler que les cyberattaques en DDoS et les défigurations de sites Web ne sont pas traitées.'}
    ]
    
    print(f'Obtaining introduction.')
    completion = openai.ChatCompletion.create(
        model='gpt-4',
        messages=messages,
        max_tokens=180,
        n=1,
        temperature=0.2,
    )
    summary = completion.choices[0].message.content
    print(summary)

    messages.append({'role': 'assistant', 'content': summary})
    messages.append({'role': 'user', 'content': 'Rédige un titre pour ce texte.'})

    print(f'Obtaining title.')
    completion = openai.ChatCompletion.create(
        model='gpt-4',
        messages=messages,
        max_tokens=30,
        n=1,
        temperature=0.2,
    )
    victim = completion.choices[0].message.content
    print(victim)

    output = {
        'introduction': summary,
        'title' : victim
        }

    return output

def most_seen_country(items):
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    most_seen = max(counts, key=counts.get)
    
    output = {
        'country': most_seen,
        'count'  : counts[most_seen]
    }

    return output

def count_by_region(codes):
    country_to_region = {
        "AUS": "APAC","CXR": "APAC","CCK": "APAC","HMD": "APAC","NZL": "APAC","NFK": "APAC","KAZ": "APAC","KGZ": "APAC","TJK": "APAC","TKM": "APAC","UZB": "APAC","CHN": "APAC","HKG": "APAC","JPN": "APAC","PRK": "APAC","KOR": "APAC","MAC": "APAC","MNG": "APAC","TWN": "APAC","BLR": "Europe","BGR": "Europe","CZE": "Europe","HUN": "Europe","MDA": "Europe","POL": "Europe","ROU": "Europe","RUS": "Europe","SVK": "Europe","UKR": "Europe","AIA": "LATAM","ATG": "LATAM","ARG": "LATAM","ABW": "LATAM","BHS": "LATAM","BRB": "LATAM","BLZ": "LATAM","BOL": "LATAM","BES": "LATAM","BVT": "LATAM","BRA": "LATAM","CYM": "LATAM","CHL": "LATAM","COL": "LATAM","CRI": "LATAM","CUB": "LATAM","CUW": "LATAM","DMA": "LATAM","DOM": "LATAM","ECU": "LATAM","SLV": "LATAM","FLK": "LATAM","GUF": "LATAM","GRD": "LATAM","GLP": "LATAM","GTM": "LATAM","GUY": "LATAM","HTI": "LATAM","HND": "LATAM","JAM": "LATAM","MTQ": "LATAM","MEX": "LATAM","MSR": "LATAM","NIC": "LATAM","PAN": "LATAM","PRY": "LATAM","PER": "LATAM","PRI": "LATAM","BLM": "LATAM","KNA": "LATAM","LCA": "LATAM","MAF": "LATAM","VCT": "LATAM","SXM": "LATAM","SGS": "LATAM","SUR": "LATAM","TTO": "LATAM","TCA": "LATAM","URY": "LATAM","VEN": "LATAM","VGB": "LATAM","VIR": "LATAM","FJI": "APAC","NCL": "APAC","PNG": "APAC","SLB": "APAC","VUT": "APAC","GUM": "APAC","KIR": "APAC","MHL": "APAC","FSM": "APAC","NRU": "APAC","MNP": "APAC","PLW": "APAC","UMI": "APAC","DZA": "MEA","EGY": "MEA","LBY": "MEA","MAR": "MEA","SDN": "MEA","TUN": "MEA","ESH": "MEA","BMU": "Northern America","CAN": "Northern America","GRL": "Northern America","SPM": "Northern America","USA": "Northern America","ALA": "Europe","DNK": "Europe","EST": "Europe","FRO": "Europe","FIN": "Europe","GGY": "Europe","ISL": "Europe","IRL": "Europe","IMN": "Europe","JEY": "Europe","LVA": "Europe","LTU": "Europe","NOR": "Europe","SJM": "Europe","SWE": "Europe","GBR": "Europe","ASM": "APAC","COK": "APAC","PYF": "APAC","NIU": "APAC","PCN": "APAC","WSM": "APAC","TKL": "APAC","TON": "APAC","TUV": "APAC","WLF": "APAC","BRN": "APAC","KHM": "APAC","IDN": "APAC","LAO": "APAC","MYS": "APAC","MMR": "APAC","PHL": "APAC","SGP": "APAC","THA": "APAC","TLS": "APAC","VNM": "APAC","AFG": "APAC","BGD": "APAC","BTN": "APAC","IND": "APAC","IRN": "APAC","MDV": "APAC","NPL": "APAC","PAK": "APAC","LKA": "APAC","ALB": "Europe","AND": "Europe","BIH": "Europe","HRV": "Europe","GIB": "Europe","GRC": "Europe","VAT": "Europe","ITA": "Europe","MLT": "Europe","MNE": "Europe","MKD": "Europe","PRT": "Europe","SMR": "Europe","SRB": "Europe","SVN": "Europe","ESP": "Europe","AGO": "MEA","BEN": "MEA","BWA": "MEA","IOT": "MEA","BFA": "MEA","BDI": "MEA","CPV": "MEA","CMR": "MEA","CAF": "MEA","TCD": "MEA","COM": "MEA","COG": "MEA","COD": "MEA","CIV": "MEA","DJI": "MEA","GNQ": "MEA","ERI": "MEA","SWZ": "MEA","ETH": "MEA","ATF": "MEA","GAB": "MEA","GMB": "MEA","GHA": "MEA","GIN": "MEA","GNB": "MEA","KEN": "MEA","LSO": "MEA","LBR": "MEA","MDG": "MEA","MWI": "MEA","MLI": "MEA","MRT": "MEA","MUS": "MEA","MYT": "MEA","MOZ": "MEA","NAM": "MEA","NER": "MEA","NGA": "MEA","REU": "MEA","RWA": "MEA","SHN": "MEA","STP": "MEA","SEN": "MEA","SYC": "MEA","SLE": "MEA","SOM": "MEA","ZAF": "MEA","SSD": "MEA","TZA": "MEA","TGO": "MEA","UGA": "MEA","ZMB": "MEA","ZWE": "MEA","ARM": "MEA","AZE": "MEA","BHR": "MEA","CYP": "MEA","GEO": "MEA","IRQ": "MEA","ISR": "MEA","JOR": "MEA","KWT": "MEA","LBN": "MEA","OMN": "MEA","PSE": "MEA","QAT": "MEA","SAU": "MEA","SYR": "MEA","TUR": "MEA","ARE": "MEA","YEM": "MEA","AUT": "Europe","BEL": "Europe","FRA": "Europe","DEU": "Europe","LIE": "Europe","LUX": "Europe","MCO": "Europe","NLD": "Europe","CHE": "Europe"
    }
    region_counts = {"Northern America": 0, "LATAM": 0, "APAC": 0, "Europe": 0, "MEA": 0}
    for code in codes:
        region = country_to_region.get(code)
        if region is not None:
            region_counts[region] += 1
    return region_counts

def main(json_file):
    stories = load_articles_from_json(json_file)
    stories.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'))
    
    last_month       = datetime.now() - timedelta(days=15)
    last_month       = last_month.replace(day=1)
    last_month_items = [item for item in stories if datetime.strptime(item['date'], '%Y-%m-%d').month == last_month.month]
    last_month_items.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'))
    news_count       = len(last_month_items)

    #affected regions
    countries_all    = [item['country'] for item in last_month_items]
    regions_hits     = count_by_region(countries_all)
    most_hit_country = most_seen_country(countries_all)
    most_hit_region  = max(regions_hits, key=lambda region: regions_hits[region])
    
    news_report = ask_chatgpt(news_count,most_hit_region,most_hit_country)
    
    html = f'<html>\n<head>\n<title>{news_report["title"]}</title>\n</head>\n<body>\n'
    html += f'<p>{news_report["introduction"]}</p>\n'
    html_list = '<ul>\n'
    for item in last_month_items:
        date = datetime.strptime(item['date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        html_list += f'<li>{date} - <b>{item["victim"]}</b> ({item["country"]})<br/>{item["summary"]} (<a href="{item["url"]}">source</a>)</li>\n'
    html_list += '</ul>\n'
    html += html_list
    html += '<i>Revue de presse réalisée en partie avec ChatGPT. <a href="https://www.lemagit.fr/actualites/365535799/Cyberhebdo-LeMagIT-met-lIA-au-service-de-linformation-de-ses-lecteurs">Les explications sont à lire ici</a>.</i>'
    html += '</body>\n</html>'
    
    with open(f'./meteocyber/{last_month.year}-{last_month.month}.html', 'w') as html_file:
        html_file.write(html)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <filename.json>")
        sys.exit(1)
    main(sys.argv[1])
