#!/usr/bin/python3

import urllib.request
import re
import json
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def get_connection():
#     return dblib.connect(host='127.0.0.1', user='root', passwd='alpha65z', db='mysql')
    return sqlite3.connect('flats.db')

def get_url():
    return 'http://www.immobilienscout24.de/Suche/S-2/Wohnung-Miete/Hamburg/Hamburg/Winterhude_Uhlenhorst_St--Georg_St--Pauli_Rotherbaum_Ottensen_Othmarschen_Hoheluft-Ost_Hoheluft-West_Hammerbrook_Hamb--Altstadt_Hamm-Mitte_Hamm-Nord_Hamm-Sued_HafenCity_Eppendorf_Eimsbuettel_Eilbek_Altona-Altstadt_Altona-Nord_Sternschanze/2,50-/55,00-/EURO--1050,00/-/3,6,7,8,40,118,113/-/-/-/true/-/-/-/-/-/-/true?enteredFrom=result_list#showRealEstate=76964837'

def get_results(url):
    response = urllib.request.urlopen(url)
    data = response.read()
    text = data.decode('utf-8')
    try:
        line = [line for line in text.split('\r\n') if re.search('model.+id', line)][0]
    except IndexError:
        exit

    match = re.search("\{.+\}", line)
    if match:
        results_as_json = match.group(0)
    else:
        exit

    return json.loads(results_as_json)["results"]

def sort_results(results):
    return sorted(results, key=lambda x: x['id'])

def get_gmap_link():
    return 'http://some.path.to.google.de'

def make_flat(result):
    match = re.match("[^,]+", result['address'])
    if match:
        street = match.group(0)
    else:
        street = address
    (price, area, rooms) = [re.match('[^\s]+', item).group(0) for item in result['attributes']]
    _id = result['id']
    address = result.get('address', None)
    district = result.get('district', None)
    city = result.get('city', None)
    _zip = result.get('zip', None)
    latitude = result.get('latitude', None)
    longitude = result.get('longitude', None)
    title = result.get('title', None)
    gmap_link = get_gmap_link()
    return {
        'id': _id,
        'title': title,
        'address': address,
        'street': street,
        'district': district,
        'zip': _zip,
        'city': city,
        'area': area,
        'price': price,
        'rooms': rooms,
        'latitude': latitude,
        'longitude': longitude,
        'gmap_link': gmap_link}

def save_flat(conn, flat):
    query = """
    INSERT INTO flat (
        id,
        title,
        address,
        street,
        district,
        zip,
        city,
        area,
        price,
        rooms,
        latitude,
        longitude,
        gmap_link,
        mail_pending
    )
    VALUES (
        :id,
        :title,
        :address,
        :street,
        :district,
        :zip,
        :city,
        :area,
        :price,
        :rooms,
        :latitude,
        :longitude,
        :gmap_link,
        1)"""
    cur = conn.cursor()
    try:
        cur.execute(query, flat)
    except sqlite3.IntegrityError:
        return None
    else:
        conn.commit()
        return flat

def update_and_send_mail(conn, flats):
    new_flats = list(filter(lambda x: x is not None, (save_flat(conn, flat) for flat in flats)))
    if new_flats:
        print("new flats arrived...")
        send_mail(new_flats)
        print("sent mail...")
    else:
        print("no new flat found...")

#     r"""ON DUPLICATE KEY
#     UPDATE
#         id = (?),
#         title = (?),
#         address = (?),
#         street = (?),
#         district = (?),
#         city = (?),
#         area = (?),
#         price = (?),
#         rooms = (?),
#         latitude = (?),
#         longitude = (?),
#         gmap_link = (?),
#         mail_pending = 1"""
#     cur = conn.cursor()
#     cur.execute(query, values * 2)
#     conn.commit()

def get_new_flats(conn):
    cur = conn.cursor()
    query = """
    SELECT
        id,
        title,
        address,
        street,
        district,
        city,
        area,
        price,
        rooms,
        latitude,
        longitude,
        gmap_link
    FROM
        flat
    WHERE
        mail_pending"""

    cur.execute(query)
    return cur.fetchall()

def update_new_flat(conn, flats):
    cur = conn.cursor()
    query = """
    UPDATE flats.flat
    SET
        mail_pending = 0
    WHERE
        id = %d"""
    for flat in flats:
        cur.execute(query, flat['id'])

def flat_to_ul(flat):
    return r"""
    <ul>
        <li>{title}</li>
        <li>{street}</li>
        <li>{district}</li>
        <li>{zip}, {city}</li>
        <li>price: {price}&euro;</li>
        <li>area: {area}m&sup2;</li>
        <li>rooms: {rooms}</li>
        <!--li>{gmap_link}</li-->
        <li>http://www.immobilienscout24.de/expose/{id}</li>
    </ul>""".format(**flat)

def send_mail(flats):
    sender = "lars.winderling@gmail.com"
    recipient = "lars.winderling@gmail.com"
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "flat crawler - new flats"
    msg['From'] = sender
    msg['To'] = recipient
    # Create the body of the message (a plain-text and an HTML version).
    text = "Hi!\nHow are recipient?\nHere is the link recipient wanted:\nhttp://www.python.org"
    prepared_flats = [flat_to_ul(flat) for flat in flats]
    body = "\n".join(prepared_flats)
    html = """\
    <html>
      <head></head>
      <body>
        {body}
      </body>
    </html>
    """.format(body=body)
    part1 = MIMEText(text.encode('utf-8'), 'plain', 'utf-8')
    part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')
    msg.attach(part1)
    msg.attach(part2)
    s = smtplib.SMTP("smtp.gmail.com", 587)
    s.starttls()
    s.login("lars.winderling@gmail.com", "Ixh<|_B1@k0nTO1")
    s.sendmail(sender, recipient, msg.as_string())
    s.quit()

if __name__ == "__main__":
    url = get_url()
    results = get_results(url)
    flats = [make_flat(result) for result in results]
    conn = get_connection()
    update_and_send_mail(conn, flats)

