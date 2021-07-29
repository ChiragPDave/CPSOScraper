#import all necessary packages
import requests
import bs4
import time
import pandas as pd
import csv
import os
import re
import lxml
import datetime
import random
import sys

def get_sitemap():
    #gets the sitemap and full list of links of MD profiles
    sitemap1 = 'https://doctors.cpso.on.ca/sitemaps/sitemap-1.txt'
    sitemap2 = 'https://doctors.cpso.on.ca/sitemaps/sitemap-2.txt'

    sitemap1_request = requests.get(sitemap1)
    print(f'Sitemap 1 result: {sitemap1_request}')

    time.sleep(10)

    sitemap2_request = requests.get(sitemap2)
    print(f'Sitemap 2 result: {sitemap2_request}')
    
    text1_str = sitemap1_request.text
    text2_str = sitemap2_request.text
    
    md_urls1 = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text1_str)
    md_urls2 = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text2_str)
    md_urls = md_urls1 + md_urls2
    
    return(md_urls)
    
def sitemap_csv(filename, md_urls):
    #Obtains the links from the sitemap and writes it into a CSV file
    links_csv_file = str(datetime.date.today()) + ' '+ filename
    df = pd.DataFrame(md_urls, columns=['Link'])
    df.to_csv(links_csv_file, mode = 'a')
    
def get_mdpage_text(x, md_urls):
    #Obtains the text from the specific MD page's site
    time.sleep(10)
    mdpage_request = requests.get(md_urls[x])
    mdpage_request
    mdpage_text = bs4.BeautifulSoup(mdpage_request.text, 'lxml')
    print(f'Result of {md_urls[x]}: {mdpage_request}')
    if str(mdpage_request) != '<Response [200]>':
        exit()
        print('Code Terminated')
    else:
        return(mdpage_text)
        
def cleanhtml(raw_html):
    #Cleans HTML tags from a string
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, ' ', raw_html)
    return cleantext

def md_name_cpso(mdpage_text, md_master_dict):
    #Obtain the Full name and CPSO Number
    try:
        md_name_num = mdpage_text.select('.name_cpso_num')[0].text.split()

        if len(md_name_num) > 4:
            md_master_dict['MD Last Name'] = md_name_num[0].replace(',','')
            md_master_dict['MD First Name'] = md_name_num[1]
            middle_list = md_name_num[2:-2]
            md_master_dict['MD Middle Name'] = ' '.join(middle_list)
        elif len(md_name_num) == 3:
            md_master_dict['MD Last Name'] = md_name_num[0].replace(',','')
            md_master_dict['MD First Name'] = md_name_num[1]
            md_master_dict['MD Middle Name'] = ''

        md_master_dict['CPSO Number'] = md_name_num[-1]
    
    except:
        pass

def md_reg_status(mdpage_text, md_master_dict):
    #Obtain the MD Registration Status
    try:
        md_status = mdpage_text.select('.doctor-info')[0].text.split()
        acceptable_status = ['Active','Expired','Active:','Expired:']
        for x in range(len(md_status)):
            for y in range(len(acceptable_status)):
                if md_status[x] in acceptable_status[y]:
                    md_master_dict['Membership Status'] = acceptable_status[y].replace(':','')
    except:
        md_master_dict['Membership Status'] = 'None'
        
def md_status_date(mdpage_text, md_master_dict):
    #Obtain the MD Membership Status as of date
    try:
        md_status_date = mdpage_text.select('.doctor-info')[0].text
        date_pattern = re.compile(r'(\d+) (\w+) (\d+)')
        date_find = re.search(date_pattern, md_status_date)
        md_mem_date = datetime.datetime.strptime(date_find.group(), '%d %b %Y').date()
        md_master_dict['Membership Status as of'] = str(md_mem_date)
    except:
        md_master_dict['Membership Status as of'] = 'None'
        
def md_reg_class_date(mdpage_text, md_master_dict):
    #Obtain the MD Registration class and registration class date
    
    #Obtain the registration class
    try:
        md_reg_class = mdpage_text.select('.doctor-info')[1].text
        md_reg_class_status = md_reg_class.split()
        acceptable_status = ['None','Independent']

        for x in range(len(md_reg_class_status)):
            for y in range(len(acceptable_status)):
                if md_reg_class_status[x] in acceptable_status[y]:
                    md_master_dict['Registration Class'] = acceptable_status[y]
    except:
        md_master_dict['Registration Class'] = 'None'

    #Obtain the registration class date
    try:
        date_pattern = re.compile(r'(\d+) (\w+) (\d+)')
        date_find = re.search(date_pattern, md_reg_class)
        md_reg_date = datetime.datetime.strptime(date_find.group(), '%d %b %Y').date()
        md_master_dict['Registration Status as of'] = str(md_reg_date)
    except:
        md_master_dict['Registration Status as of'] = 'None'

def md_gender_lang_edu(mdpage_text, md_master_dict):
    #Obtain the Gender, Languages Spoken, and Medical School Education/Year of Graduation
    
    #Obtain the Gender
    try:
        md_summary = mdpage_text.select('.info')[0].text
        gender_pattern = re.compile(r'Gender:(\s+)(\w+)')
        gender_find = re.findall(gender_pattern, md_summary)
        md_master_dict['Gender'] = gender_find[0][1]

    except:
        md_master_dict['Gender'] = 'None'
    
    #Obtain the Languages Spoken
    try:
        languages_pattern = re.compile(r'Spoken:(\s+)(.+)')
        languages_find = re.findall(languages_pattern, md_summary)
        md_master_dict['Languages Spoken'] = languages_find[0][1].replace('\r','')

    except:
        md_master_dict['Languages Spoken'] = 'None'

    #Obtain the Medical School Education and Year of Graduation
    try:
        education_pattern = re.compile(r'Education:(.*)')
        education_find = re.findall(education_pattern, md_summary)
        education_split = education_find[0].split(',')
        md_master_dict['Medical School Education'] = education_split[0]
        md_master_dict['Medical School Year of Graduation'] = education_split[1].strip()

    except:
        md_master_dict['Medical School Education'] = 'None'
        md_master_dict['Medical School Year of Graduation'] = 'None'
        
def md_prim_prac_info(mdpage_text, md_master_dict):
    #Obtain the Primary Practice Info and split off Phone and Fax if available
    try:
        md_primary = mdpage_text.select('.practice-location')[0].select('.location_details')[0]
        practice_pattern = re.compile(r'(\S+)')
        practice_find = re.findall(practice_pattern, str(md_primary))
        practice_temp = ' '.join(practice_find)
        practice_info_temp = cleanhtml(practice_temp)
        del_pattern = r'Electoral District(.*)'
        practice_info = re.sub(del_pattern, '', practice_info_temp)
        md_master_dict['Primary Practice Information'] = practice_info.strip()

    except:
        md_master_dict['Primary Practice Information'] = 'None'
    
    #Primary practice phone number
    try:
        phone_pattern = re.compile(r'Phone: (.*)')
        phone_find = re.findall(phone_pattern, practice_info)
        primary_phone_number = phone_find[0]
        md_master_dict['Primary Practice Phone Number'] = primary_phone_number.split('  ')[0].strip()
    except:
        md_master_dict['Primary Practice Phone Number'] = 'None'
        
    #Primary practice fax number
    try:
        fax_pattern = re.compile(r'Fax: (.*)')
        fax_find = re.findall(fax_pattern, practice_info)
        primary_fax_number = fax_find[0]
        md_master_dict['Primary Practice Fax Number'] = primary_fax_number.strip()
    except:
        md_master_dict['Primary Practice Fax Number'] = 'None'
        
def md_add_prac(mdpage_text, md_master_dict):
    #Obtain MD Additional Practice Information/Locations
    try:
        md_additional_ = mdpage_text.select('.location_details')
        md_add_practice = mdpage_text.find("div", {"id":"additionallocations"})

        md_add_practice_temp = cleanhtml(str(md_add_practice))
        md_add_practice_info = md_add_practice_temp.split()
        md_master_dict['Additional Practice(s) Information'] = ' '.join(md_add_practice_info).replace('Additional Practice Location(s)', '')

    except:
        md_master_dict['Additional Practice(s) Information'] = 'None'
        
def md_corp_info(mdpage_text, md_master_dict):
    #Obtain MD Professional Corporation Information
    try:
        md_pc_info_raw = mdpage_text.find("div", {"id":"professionalcorporationinfo"})
        pc_info_temp = cleanhtml(str(md_pc_info_raw))
        md_pc_info = pc_info_temp.split()
        md_master_dict['Professional Corporation Information'] = ' '.join(md_pc_info).replace('Professional Corporation Information', '')
    except:
        md_master_dict['Professional Corporation Information'] = 'None'
        
def md_hosp_priv(mdpage_text, md_master_dict):
    #Obtain MD Hospital Privileges
    try:
        hosp_priv_raw = mdpage_text.find("section", {"id":"hospital_priv"})
        hosp_priv_table = pd.read_html(str(hosp_priv_raw))
        hosp_priv_list = hosp_priv_table[0].values.tolist()
        hosp_priv_final_list = []
        
        for x in range(len(hosp_priv_list)):
            y = x + 1
            hosp_priv_temp = (f'{y}. ') + (' ('.join(hosp_priv_list[x]) + ')')
            hosp_priv_final_list.append(hosp_priv_temp)

        md_master_dict['Hospital Privilege(s)'] = ' '.join(hosp_priv_final_list)

    except:
        md_master_dict['Hospital Privilege(s)'] = 'None'
        
def md_specialty(mdpage_text, md_master_dict):
    #obtain MD Specialties
    try:
        md_specialty = mdpage_text.find("section", {"id":"specialties"})
        md_spec_table = pd.read_html(str(md_specialty))
        md_spec_list = md_spec_table[0].values.tolist()
        md_spec_temp = []
        md_spec_final_list = []
        
        for x in range(len(md_spec_list)):
            md_spec_temp_raw = md_spec_list[x]
            y = x + 1
            
            for z in range(len(md_spec_temp_raw)):
                nan_check = str(md_spec_temp_raw[z])
                if nan_check.lower() != 'nan':
                    md_spec_temp.append(md_spec_temp_raw[z])
            
            md_spec_final_list.append((f'{y}. ') + ' - '.join(md_spec_temp))
            md_spec_temp = []
        
        md_master_dict['MD Specialty'] = ' '.join(md_spec_final_list)
        
    except:
        md_master_dict['MD Specialty'] = 'None'

def md_terms_cond(mdpage_text, md_master_dict):
    #Obtain Terms and Conditions of MD practice
    try:
        md_tandc_raw = mdpage_text.find("section", {"id":"terms"}).find('p')
        md_tandc = cleanhtml(str(md_tandc_raw))
        md_master_dict['Terms and Conditions'] = md_tandc.strip()
    except:
        md_master_dict['Terms and Conditions'] = 'None'
        
def md_postgrad_train(mdpage_text, md_master_dict):
    #obtain Postgraduate Training Dates and type of Study
    try:
        md_postgrad_raw = mdpage_text.find("section", {"id":"postgrad"})
        postgrad_pattern = re.compile(r'<strong>(.*)(\s+)(.*)')
        pg_cleaned = re.findall(postgrad_pattern, str(md_postgrad_raw))
        pg_final_list = []
        
        for x in range(len(pg_cleaned)):
            pg_target = pg_cleaned[x]
            pg_start = cleanhtml(str(pg_target[0]))
            pg_end = cleanhtml(str(pg_target[-1]))
            pg_combined = pg_end + pg_start
            temp_pg_list = pg_combined.replace('\r',' ').strip()
            pg_final_list.append(temp_pg_list)
        md_master_dict['Postgraduate Training'] = ' ~ '.join(pg_final_list)
        #print (pg_final_list)
    
    except:
        md_master_dict['Postgraduate Training'] = 'None'
        
def md_reg_history(mdpage_text, md_master_dict):
    #Obtain Registration History
    try:
        md_reg_hx = mdpage_text.find("section", {"id":"reghistory"})
        md_reg_table = pd.read_html(str(md_reg_hx))
        md_reg_list = md_reg_table[0].values.tolist()
        md_reg_final_list = []
        
        for x in range(len(md_reg_list)):
            y = x + 1
            md_reg_temp = (f'{y}. ') + ' - '.join(md_reg_list[x])
            md_reg_final_list.append(md_reg_temp)
            md_master_dict['MD Registration History'] = ' '.join(md_reg_final_list)

    except:
        md_master_dict['MD Registration Event'] = 'None'
        
def md_dict_to_csv(data_dict, csv_file, i):
    #Write MD Dictionary Entry to master CSV
    df = pd.DataFrame.from_dict(data_dict, orient='index')
    final_df = df.transpose()
    if i != 0:
        final_df.to_csv(csv_file, mode = 'a', index = False, header = not os.path.exists(csv_file))
    else:
        final_df.to_csv(csv_file, mode = 'a', index = False)