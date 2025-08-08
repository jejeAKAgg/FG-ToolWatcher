import pandas as pd
import re
from UTILS.LOGmaker import logger

# ====================
#     LOGGER SETUP
# ====================
Logger = logger("CSVmerger")

# ====================
#    VARIABLE SETUP
# ====================
FINALcsv = 'DATA/RESULTSproducts.csv'
FINALxlsx = 'DATA/RESULTSproducts.xlsx'

# ====================
#     CSV MERGER 
# ====================
def FINALdf(files):
    # Fusion des fichiers
    final_df = pd.concat(files, ignore_index=True).sort_values(by=["MPN", "Société"], ascending=[True, True])

    # Export CSV brut
    final_df.to_csv(FINALcsv, index=False, encoding='utf-8-sig')

    # Préparer l'écriture Excel avec lien cliquable
    with pd.ExcelWriter(FINALxlsx, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet("Feuille1")
        writer.sheets["Feuille1"] = worksheet

        # Écriture de l'en-tête
        for col_idx, col_name in enumerate(final_df.columns):
            worksheet.write(0, col_idx, col_name)

        # Regex pour extraire le lien et le texte
        hyperlink_pattern = re.compile(r'=HYPERLINK\("([^"]+)"\s*;\s*"([^"]+)"\)', re.IGNORECASE)

        # Parcours des lignes
        for row_idx, row in final_df.iterrows():
            for col_idx, col_name in enumerate(final_df.columns):
                value = row[col_name]

                if col_name == "Article" and isinstance(value, str):
                    match = hyperlink_pattern.match(value.strip())
                    if match:
                        url, text = match.groups()
                        worksheet.write_url(row_idx + 1, col_idx, url.strip(), string=text.strip())
                    else:
                        worksheet.write(row_idx + 1, col_idx, value)
                else:
                    worksheet.write(row_idx + 1, col_idx, value)

    return FINALcsv, FINALxlsx