import pandas as pd
import os
import sys
import dotenv
import pygbif.species as gbif
import pytaxize.gn as gn
import numpy as np
sys.path.append(os.getcwd())

dotenv.load_dotenv(".env")
data_dir = os.getenv("DATA_PATH")
# data_dir = "G:\GITAR\PubData"


# set data dir to "G:\GITAR\PubData"
# data_dir = r"G:\GITAR\PubData\\"

# Bring in new species lists


invasive_all_source = pd.read_csv( data_dir + "\species lists\invasive_all_source.csv", dtype={"usageKey": str})
gbif_backbone = pd.read_csv( data_dir + "\GBIF data\GBIF_backbone_invasive.csv", dtype={"usageKey": str})
cabi_gbif = pd.read_csv( data_dir + "\species lists\gbif_matched\cabi_gbif.csv", dtype={"usageKey": str})
eppo_gbif = pd.read_csv( data_dir + "\species lists\gbif_matched\eppo_gbif.csv", dtype={"usageKey": str})
sinas_gbif = pd.read_csv( data_dir + "\species lists\gbif_matched\sinas_gbif.csv", dtype={"usageKey": str})
daisie_gbif = pd.read_csv( data_dir + "\species lists\gbif_matched\daisie_gbif.csv", dtype={"usageKey": str})
data_files = [cabi_gbif, eppo_gbif, daisie_gbif]
#make column 'species' in sinasGBIF that copies taxonSINAS
sinas_gbif['species'] = sinas_gbif['taxonSINAS']
#rename sinas_gbif matchtype to matchType
sinas_gbif.rename(columns={'matchtype': 'matchType'}, inplace=True)
#if matchType is NA set to ""
sinas_gbif['matchType'] = sinas_gbif['matchType'].replace(np.nan, '', regex=True)

data_files = [sinas_gbif]
test = [cabi_gbif.head(50).copy()]


# Retry decorator to handle HTTP and timeout errors

specie_unfound = []
for file in data_files:
    for index, row in file.iterrows():
        if row['matchType'] in ["", "NA", "HIGHERRANK"]:
            specie_unfound.append(row['species'])
# drop duplicates
specie_unfound = list(set(specie_unfound))

check_species_df = pd.DataFrame(specie_unfound, columns=["Taxon"])
# add Taxon_orig that duplicates Taxon col
check_species_df['Taxon_orig'] = check_species_df['Taxon']
matched_species, unmatched = check_gbif_tax_secondary(check_species_df)
# make dc into dataframe
matched_species = pd.DataFrame(matched_species)



def update_GBIFstatus(row):
    if row["GBIFstatus"] == "Missing" and row["GBIFstatus_Synonym"] != None:
        row["GBIFstatus"] = row["GBIFstatus_Synonym"]
    elif row["GBIFstatus"] == None and row["GBIFstatus_Synonym"] != None:
        row["GBIFstatus"] = row["GBIFstatus_Synonym"]
    return row


matched_species = matched_species.apply(update_GBIFstatus, axis=1)
# write matched_species to csv as previously_unmatched_species.csv
matched_species.to_csv(
    data_dir + "\species lists\previously_unmatched_species_gbif_match_sinas.csv"
)

for file in data_files:

    if "kingdom" not in file.columns:
        file["kingdom"] = None
        file["phylum"] = None
        file["class"] = None
        file["order"] = None
        file["family"] = None

        file["genus"] = None
        file["GBIFstatus"] = None
        file["GBIFtaxonRank"] = None
        file["taxonomic_species"] = None
    if "canonicalName" not in file.columns:
        file["canonicalName"] = None
    #if usageKey col is not string, set to string and remove any .0 from floats
    if file['usageKey'].dtype != 'str':
        file['usageKey'] = file['usageKey'].astype(str)
        file['usageKey'] = file['usageKey'].str.replace('.0', '')
    
    for index, row in file.iterrows():
     
        skip_uk = 0
        if row['matchType'] in ["", "NA", "HIGHERRANK"]:
            # search for species in matched_species
            search = matched_species[matched_species['Taxon_orig'] == row['species']]
            if search.empty:
                print(row['species'])
                # break
                print(row)
                continue
            elif search.iloc[0]['GBIFstatus'] == "Missing" or search.iloc[0]['GBIFstatus'] == None:
                print("making XX")
                if file.at[index, "matchType"] == "HIGHERRANK":
                    print("HIGHERRANK")
                    print(file.at[index, "species"])
                try:
                    file.at[index, "usageKey"] = "XX" + row['species'].replace(" ", "_")
                    print('creating UK' + "XX" + row['species'].replace(" ", "_"))
                except AttributeError:
                    print(row['species'])
                    pass
            
             
                continue
            else:
                skip_uk = 1
                search = search.iloc[0]
            file.at[index, "kingdom"] = search['kingdom']
            file.at[index, "phylum"] = search['phylum']
            file.at[index, "class"] = search['class']
            file.at[index, "order"] = search['order']
            file.at[index, "family"] = search['family']
            file.at[index, "genus"] = search['genus']
            file.at[index, "usageKey"] = search['GBIFusageKey']
            file.at[index, "canonicalName"] = search['Taxon']
            file.at[index, "scientificName"] = search['scientificName']
            # file.at[index, "GBIFstatus"] = search['GBIFstatus']
            file.at[index, "matchType"] = search['GBIFmatchtype']
            file.at[index, "rank"] = search['GBIFtaxonRank']
            file.at[index, "taxonomic_species"] = search['species']
        else: 
            # match to gbif_backbone
            search = gbif_backbone[gbif_backbone['usageKey'] == row['usageKey']]

            if search.empty:
                # print(row['usageKey'])
                # break
                # print(row)
                # print(row["species"])
                print('no match to gbif backbone')
                # print(row['usageKey'])
                if (
                    pd.isnull(file.at[index, "usageKey"])
                    or file.at[index, "usageKey"] == ""
                    or row['usageKey'] == "nan"
                ):

                    print("making XX")
                    if file.at[index, "matchType"] == "HIGHERRANK":
                        print("HIGHERRANK")
                        print(file.at[index, "species"])
                    try:
                        file.at[index, "usageKey"] = "XX" + row['species'].replace(" ", "_")
                        print('creating UK' + "XX" + row['species'].replace(" ", "_"))
                    except AttributeError:
                        print(row['species'])
                        pass
               
                continue
            else:
                search = search.iloc[0]
                # print(search)
                file.at[index, "kingdom"] = search['kingdom']
                file.at[index, "phylum"] = search['phylum']
                file.at[index, "class"] = search['class']
                file.at[index, "order"] = search['order']
                file.at[index, "family"] = search['family']
                file.at[index, "genus"] = search['genus']
                file.at[index, "gbif_species"] = search['species']
                # if cannonical name blank
                if pd.isnull(row['canonicalName']):
                    file.at[index, "canonicalName"] = search['species']
                    file.at[index, "scientificName"] = search['scientificName']
                    # file.at[index, "GBIFstatus"] = search['GBIFstatus']
                    file.at[index, "matchType"] = search['taxonomicStatus']
                    file.at[index, "rank"] = search['taxonRank']
                    file.at[index, "taxonomic_species"] = search['species']
            # print file at index
            # print(file.at[index, "kingdom"])
            # if usageKey is na

        if pd.isnull(file.at[index, "usageKey"]) or file.at[index, "matchType"] == "HIGHERRANK" or file.at[index, "usageKey"] == "NA" or file.at[index, "usageKey"] == "" or pd.isnull(row['usageKey']):
            print("making XX")
            if file.at[index, "matchType"] == "HIGHERRANK":
                print("HIGHERRANK")
                print(file.at[index, "species"])
            try:
                file.at[index, "usageKey"] = "XX" + row['species'].replace(" ", "_")
                print('creating UK' + "XX" + row['species'].replace(" ", "_"))
            except AttributeError:
                print(row['species'])
        elif pd.isnull(row['usageKey'] ) or row['usageKey'] == "" or row['usageKey'] == "NaN" or row['usageKey'] == 'nan':
            print("NA")
            print(row['species'])
            print(row['usageKey'])
            print(file.at[index, "usageKey"])
            print(file.at[index, "species"])
        else:
            print(row['usageKey'])
            #print('broke')




cabi_gbif_match = data_files[0]
eppo_gbif_match = data_files[1]
daisie_gbif_match = data_files[2]
sinas_gbif_match = data_files[3]

#write to csv 
cabi_gbif_match.to_csv(data_dir + "\species lists\gbif_matched\cabi_gbif_matched.csv")
eppo_gbif_match.to_csv(data_dir + "\species lists\gbif_matched\eppo_gbif_matched.csv")
daisie_gbif_match.to_csv(data_dir + "\species lists\gbif_matched\daisie_gbif_matched.csv")
sinas_gbif_match.to_csv(data_dir + "\species lists\gbif_matched\sinas_gbif_matched.csv")
