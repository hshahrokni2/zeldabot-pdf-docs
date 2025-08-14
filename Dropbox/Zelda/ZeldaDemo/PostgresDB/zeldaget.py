import os
import re
import json
import psycopg2
from psycopg2.extras import execute_batch, execute_values

# -----------------------
# 1. CONFIGURATION
# -----------------------
PATH_TO_JSONS = r"C:\Users\hshah\Dev\zeldabot\out_json"  # Adjust folder
BATCH_SIZE = 500

DB_HOST = "localhost"
DB_NAME = "zelda"
DB_USER = "postgres"
DB_PASS = "resP4ss!"

# Regex for "lgh 1234" or "lgh1234"
LGH_PATTERN = re.compile(r'lgh\D?(\d{3,4})', re.IGNORECASE)

def main():
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    conn.autocommit = False
    cur = conn.cursor()

    # Clear all existing data
    cur.execute("""
        TRUNCATE TABLE 
            apartments,
            addresses,
            documents,
            economy_data,
            brfs
        RESTART IDENTITY CASCADE;
    """)

    # Prep lists for batch insert
    brfs_data = []
    econ_data_list = []
    docs_data = []
    addresses_data = []
    apartments_temp = []

    # -----------------------
    # 2. Iterate JSON
    # -----------------------
    for filename in os.listdir(PATH_TO_JSONS):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(PATH_TO_JSONS, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # ---------------
        # BRF FIELDS
        # ---------------
        brf_id = data.get("brf_id")
        brf_name = data.get("brf_name")
        city = data.get("city")
        timestamp_ = data.get("timestamp")

        info_box = data.get("info_box", {})

        byggar = data.get("Byggår") or info_box.get("Byggår")
        antal_bostadsratter = data.get("Antal_bostadsrätter") or info_box.get("Antal_bostadsrätter")
        antal_hyresratter = data.get("Antal_hyresrätter") or info_box.get("Antal_hyresrätter")
        boarea_val = data.get("boarea_bostadsratter_value") or info_box.get("boarea_bostadsratter_value")
        markagande = data.get("Markägande") or info_box.get("Markägande")
        akta_forening = data.get("Äkta_förening") or info_box.get("Äkta_förening")

        # If city is missing, correct_address = False
        correct_address_val = bool(city and city.strip())

        brfs_data.append((
            brf_id,
            brf_name,
            city,
            byggar,
            antal_bostadsratter,
            antal_hyresratter,
            boarea_val,
            markagande,
            akta_forening,
            timestamp_,
            correct_address_val
        ))

        # ---------------
        # ECONOMY DATA
        # ---------------
        econ = data.get("economy_data", {})
        lan_text = econ.get("lån_text")
        lan_value = econ.get("lån_value")
        belaning_text = econ.get("belåning_per_m2_text") or econ.get("belaning_per_m2_text")
        belaning_val = econ.get("belåning_per_m2_value") or econ.get("belaning_per_m2_value")
        avgift_text = econ.get("avgift_text")
        avgift_per_m2_year = econ.get("avgift_per_m2_year")
        sparande_text = econ.get("sparande_text")
        sparande_per_m2_year = econ.get("sparande_per_m2_year")

        econ_data_list.append((
            brf_id,
            lan_text,
            lan_value,
            belaning_text,
            belaning_val,
            avgift_text,
            avgift_per_m2_year,
            sparande_text,
            sparande_per_m2_year
        ))

        # ---------------
        # DOCUMENTS
        # ---------------
        for doc in data.get("documents", []):
            doc_text = doc.get("doc_text") or doc.get("title")
            doc_type = doc.get("doc_type") or doc.get("type")
            href = doc.get("href")
            saved_path = doc.get("saved_path") or doc.get("saved_pdf")

            docs_data.append((brf_id, doc_text, doc_type, href, saved_path))

        # ---------------
        # ADDRESSES + APARTMENTS
        # ---------------
        for r in data.get("residences", []):
            # We'll store coordinate info + city in addresses
            geocoded = r.get("geocoded") or {}
            latitude = geocoded.get("latitude")
            longitude = geocoded.get("longitude")
            formatted_address = geocoded.get("formatted_address")

            city_appended = r.get("city_appended")  # We'll treat this as 'city'
            addresses_data.append((
                brf_id,
                city_appended,
                latitude,
                longitude,
                formatted_address
            ))

            # The "apartment" data is raw_address, size, estimated_value, lgh
            raw_address = r.get("raw_address")
            size = r.get("size")
            estimated_value = r.get("estimated_value")

            # Find "lgh 1234"
            lgh_val = None
            if raw_address:
                m = LGH_PATTERN.search(raw_address)
                if m:
                    lgh_val = m.group(1)  # e.g. "1002"

            apartments_temp.append({
                "index_in_batch": len(addresses_data) - 1,  # link by index
                "raw_address": raw_address,
                "size": size,
                "estimated_value": estimated_value,
                "lgh": lgh_val
            })

        # Insert if we reach the batch size
        if len(brfs_data) >= BATCH_SIZE:
            do_inserts(
                conn, cur,
                brfs_data,
                econ_data_list,
                docs_data,
                addresses_data,
                apartments_temp
            )
            brfs_data.clear()
            econ_data_list.clear()
            docs_data.clear()
            addresses_data.clear()
            apartments_temp.clear()

    # final leftover batch
    if brfs_data:
        do_inserts(
            conn, cur,
            brfs_data,
            econ_data_list,
            docs_data,
            addresses_data,
            apartments_temp
        )

    cur.close()
    conn.close()

# -----------------------
# 3. BATCH INSERT
# -----------------------
def do_inserts(
    conn,
    cur,
    brfs_data,
    econ_data_list,
    docs_data,
    addresses_data,
    apartments_temp
):
    """
    Inserts:
      - brfs
      - economy_data
      - documents
      - addresses (with RETURNING id)
      - apartments (linking address_id)
    Then commits.
    """
    # 1) brfs
    sql_brfs = """
        INSERT INTO brfs (
            brf_id,
            brf_name,
            city,
            byggar,
            antal_bostadsratter,
            antal_hyresratter,
            boarea_bostadsratter_value,
            markagande,
            akta_forening,
            timestamp,
            correct_address
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (brf_id) DO NOTHING;
    """
    execute_batch(cur, sql_brfs, brfs_data, page_size=BATCH_SIZE)

    # 2) economy_data
    sql_econ = """
        INSERT INTO economy_data (
            brf_id,
            lan_text,
            lan_value,
            belaning_per_m2_text,
            belaning_per_m2_value,
            avgift_text,
            avgift_per_m2_year,
            sparande_text,
            sparande_per_m2_year
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
    """
    execute_batch(cur, sql_econ, econ_data_list, page_size=BATCH_SIZE)

    # 3) documents
    sql_docs = """
        INSERT INTO documents (
            brf_id,
            doc_text,
            doc_type,
            href,
            saved_path
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
    """
    execute_batch(cur, sql_docs, docs_data, page_size=BATCH_SIZE)

    # 4) addresses (RETURNING id)
    sql_addresses = """
        INSERT INTO addresses (
            brf_id,
            city,
            latitude,
            longitude,
            formatted_address
        )
        VALUES %s
        RETURNING id;
    """
    address_ids = []
    for i in range(0, len(addresses_data), BATCH_SIZE):
        slice_ = addresses_data[i : i + BATCH_SIZE]
        cur.execute("BEGIN;")
        try:
            returned_rows = execute_values(cur, sql_addresses, slice_, fetch=True)
            for row in returned_rows or []:
                address_ids.append(row[0])
            cur.execute("COMMIT;")
        except:
            cur.execute("ROLLBACK;")
            raise

    # 5) apartments: link each address to apt data by index
    apts_data = []
    for i, item in enumerate(apartments_temp):
        addr_id = address_ids[i]
        raw_addr = item["raw_address"]
        size_ = item["size"]
        est_val = item["estimated_value"]
        lgh_ = item["lgh"]

        apts_data.append((addr_id, raw_addr, size_, est_val, lgh_))

    sql_apts = """
        INSERT INTO apartments (
            address_id,
            raw_address,
            size,
            estimated_value,
            lgh
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
    """
    if apts_data:
        execute_batch(cur, sql_apts, apts_data, page_size=BATCH_SIZE)

    conn.commit()

# -----------------------
# 4. RUN SCRIPT
# -----------------------
if __name__ == "__main__":
    main()
