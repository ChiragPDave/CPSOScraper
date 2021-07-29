#CPSO Scraper July 2021
#Import functions for the scraper
from functions import *

#Global variables
md_urls_csv = 'cpso_links.csv'
md_master_csv = 'CPSO MD Database.csv'
md_master_dict = {}

#Obtain the full list of MD page entries
md_urls = get_sitemap()
sitemap_csv(md_urls_csv, md_urls)

#Run the scraping routine through all physician links
for x in range(len(md_urls)):
    mdpage_text = get_mdpage_text(x, md_urls)
    md_master_dict['CPSO Profile Link'] = md_urls[x]
    md_name_cpso(mdpage_text, md_master_dict)
    md_reg_status(mdpage_text, md_master_dict)
    md_status_date(mdpage_text, md_master_dict)
    md_reg_class_date(mdpage_text, md_master_dict)
    md_gender_lang_edu(mdpage_text, md_master_dict)
    md_prim_prac_info(mdpage_text, md_master_dict)
    md_add_prac(mdpage_text, md_master_dict)
    md_corp_info(mdpage_text, md_master_dict)
    md_hosp_priv(mdpage_text, md_master_dict)
    md_specialty(mdpage_text, md_master_dict)
    md_terms_cond(mdpage_text, md_master_dict)
    md_postgrad_train(mdpage_text, md_master_dict)
    md_reg_history(mdpage_text, md_master_dict)
    md_dict_to_csv(md_master_dict, md_master_csv, x)