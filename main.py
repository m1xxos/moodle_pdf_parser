import glob
import os
import time
from base64 import b64decode
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.print_page_options import PrintOptions
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from selenium.webdriver.chrome.options import Options
from time import sleep

import secrets

links = {'links': []}
options = Options()
options.add_argument('--headless')
print_options = PrintOptions()
print_options.page_ranges = ['1-2']
s = Service(secrets.CHROME_DRIVER)
driver = webdriver.Chrome(service=s, options=options)


def remove(value, deletechars):
    for c in deletechars:
        value = value.replace(c, '')
    return value


def login_to_sdo():
    driver.get(secrets.COURSE_LINK)
    WebDriverWait(driver, timeout=10).until(ec.presence_of_element_located((By.NAME, "username")))
    login = driver.find_element(By.NAME, 'username')
    login.send_keys(secrets.LOGIN)
    password = driver.find_element(By.NAME, 'password')
    password.send_keys(secrets.PASSWORD)
    enter_button = driver.find_element(By.ID, "loginbtn")
    enter_button.click()


def course_name_folder():
    course_name = driver.find_element(By.XPATH, '//*[@id="page-header"]/div/div[2]/div[1]/div/div/h1')
    if not os.path.exists('courses'):
        os.makedirs('courses')
    course_path = os.path.join('courses', course_name.text.strip())
    if not os.path.exists(course_path):
        os.makedirs(course_path)
    return course_path


def scraper(course_path):
    WebDriverWait(driver, timeout=10).until(ec.presence_of_element_located((By.CLASS_NAME, "courseindex-section")))
    sections = driver.find_elements(By.CLASS_NAME, "courseindex-section")
    j = 1
    for section in sections:
        i = 1
        time.sleep(1)
        section_name = section.find_element(By.CLASS_NAME, "courseindex-item")
        section_name = section_name.find_elements(By.TAG_NAME, "a")
        section_name = section_name[1].get_attribute("innerHTML").strip()
        if section_name == "":
            section_name = "пустота"
        if j < 10:
            jnumber = "0" + str(j)
        else:
            jnumber = j
        section_path = os.path.join(course_path, str(jnumber) + "_" + section_name.replace("", ""))

        if not os.path.exists(section_path):
            os.makedirs(section_path)

        section_elements = section.find_elements(By.TAG_NAME, 'div')
        section_elements = section_elements[1].find_element(By.TAG_NAME, 'ul')
        section_elements = section_elements.find_elements(By.TAG_NAME, 'li')
        for element in section_elements:
            WebDriverWait(driver, timeout=10).until(ec.presence_of_element_located((By.TAG_NAME, 'a')))
            try:
                section_link = element.find_element(By.TAG_NAME, 'a')
            except:
                continue
            name = section_link.get_attribute('innerHTML').strip()
            name = remove(name, '/:*?"<>\\|')
            if i < 10:
                number = "0" + str(i)
            else:
                number = i

            name = remove(name, '\t\n')
            links['links'].append({
                'link': section_link.get_attribute('href'),
                'filename': os.path.join(section_path, str(number) + "_" + name + ".pdf")
            })
            i = i + 1
        j = j + 1


def crawler():
    for item in links['links']:
        time.sleep(2)
        driver.get(item['link'])
        if driver.find_elements(By.LINK_TEXT, "Следующая"):
            course_id = item['link'].strip("https://sdo.sut.ru/mod/book/view.php?id=")
            driver.get("https://sdo.sut.ru/mod/book/tool/print/index.php?id=" + course_id)
        base64code = driver.print_page()
        pdf_byte = b64decode(base64code, validate=True)
        print(item['filename'])

        with open(item['filename'], 'wb') as f:
            f.write(pdf_byte)


def pdf_merger(course_name):
    hdir = "courses/" + course_name
    for root, dirs, files in os.walk(hdir):
        merger = PdfMerger()
        print(files)
        for filename in files:
            if filename.endswith(".pdf"):
                # print(filename)
                filepath = os.path.join(root, filename)

                ReadPDF = PdfReader(filepath)
                pages = len(ReadPDF.pages)
                output = PdfWriter()
                for i in range(pages):
                    ReadPDF = PdfReader(filepath)
                    pageObj = ReadPDF.pages[i]
                    text = pageObj.extract_text()
                    if len(text) > 0:
                        output.add_page(pageObj)
                output.write(filepath)

                merger.append(PdfReader(open(filepath, 'rb')))

        merger.write(os.path.join(hdir, os.path.basename(os.path.normpath(root)) + '.pdf'))

    all_pdfs = glob.glob('courses/' + course_name + '/*.pdf', recursive=True)
    merger = PdfMerger()
    for pdf in all_pdfs:
        merger.append(pdf)

    merger.write("courses/" + course_name + "/" + str(course_name) + ".pdf")
    merger.close()


def main():
    login_to_sdo()
    path = course_name_folder()
    scraper(path)
    crawler()
    driver.close()


if __name__ == "__main__":
    main()
    pdf_merger("COURSE_NAME")
