import pandas as pd

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
    FINALdf = pd.concat(files, ignore_index=True).sort_values(by=["MPN", "Société"], ascending=[True, True])
    
    FINALdf.to_csv(FINALcsv, index=False)
    FINALdf.to_excel(FINALxlsx, index=False)

    return FINALcsv, FINALxlsx