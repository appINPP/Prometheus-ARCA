#imports
import pandas
import argparse
from pathlib import Path
import numpy as np

#path to the original arca file
REPO_ROOT = Path("/prometheusLink")
arca=str(REPO_ROOT/"resources"/"geofiles"/"arca.geo")

parser = argparse.ArgumentParser(description="Load the geometry file")
parser.add_argument("file", type=str,help="Path to the input file")
args = parser.parse_args()
file = Path(args.file)

with open(file,"r",encoding="utf-8") as f:
    rows=[]
    x=y=z=0
    count_lines=0
    count_doms=0
    count_strings=0

    #skips first 623 lines as well as the header of the first data set
    for _ in range (623):
        next(f)
        
    for line in f:
        if line=="\n":
            if count_lines==31:                                                               #31 corresponds to no of PMTs
                rows.append([x/31-23.5, y/31-295, z/31-3450., count_strings, count_doms])     #change of coordinates
                x=y=z=0
                count_doms+=1
            if count_doms==18:
                count_doms=0
                count_strings+=1
            count_lines=0
            next(f,None)
            continue
            
        count_lines+=1
        parts=line.split()
        x+=float(parts[1])
        y+=float(parts[2])
        z+=float(parts[3])
        
print(np.array(rows))

with open(arca, "r", encoding="utf-8") as f:
    geoheader=[next(f) for _ in range(4)]                 #skips first four lines of metadata

with open(arca, "w", encoding="utf-8") as f:
    f.writelines(geoheader)    
    for row in rows:
        f.write("\t".join(map(str,row)) + "\n")
