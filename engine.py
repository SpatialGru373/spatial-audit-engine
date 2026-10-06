import arcpy
import os
import datetime
import osmnx as ox
import networkx as nx

# Set environment overwrite rules
arcpy.env.overwriteOutput = True

# Define exact directory paths matching your Downloads folder structure
base_dir = r"C:/Users/HP VICTUS/Downloads/SpatialAuditEngine"
input_csv = os.path.join(base_dir, "inputs", "client_sites.csv")
scratch_dir = os.path.join(base_dir, "scratch")
output_gdb = os.path.join(scratch_dir, "workspace.gdb")
output_pdf_dir = os.path.join(base_dir, "outputs")

# Ensure directories exist
for d in [scratch_dir, output_pdf_dir]:
    if not os.path.exists(d):
        os.makedirs(d)

# Create scratch geodatabase if it doesn't exist
if not arcpy.Exists(output_gdb):
    arcpy.management.CreateFileGDB(scratch_dir, "workspace.gdb")

print(">>> Step 1: Workspace and scratch geodatabase initialized successfully.")

# Function to convert client CSV to spatial point features
def convert_csv_to_points(csv_path, output_fc):
    spatial_ref = arcpy.SpatialReference(4326) # WGS 1984
    arcpy.management.XYTableToPoint(
        in_table=csv_path,
        out_feature_class=output_fc,
        x_field="Longitude",
        y_field="Latitude",
        coordinate_system=spatial_ref
    )
    print(f">>> Step 2: Converted CSV to spatial features: {output_fc}")

target_points = os.path.join(output_gdb, "client_sites_pts")
convert_csv_to_points(input_csv, target_points)

# --- STEP 3: LIVE OPENSOURCE DATA FETCHING & DYNAMIC MCDA SCORING ---
def run_spatial_scoring(target_fc):
    print(">>> Step 3: Connecting to OpenStreetMap via osmnx for live infrastructure analysis...")

    fields_to_add = [
        ("Score_Demand_40", "DOUBLE"),
        ("Score_Infrastruct_40", "DOUBLE"),
        ("Score_GridGap_20", "DOUBLE"),
        ("Final_MCDA_Score", "DOUBLE")
    ]
    
    existing_fields = [f.name for f in arcpy.ListFields(target_fc)]
    for field_name, field_type in fields_to_add:
        if field_name not in existing_fields:
            arcpy.management.AddField(target_fc, field_name, field_type)

    print(">>> Step 4: Scoring pillars initialized. Querying live road networks...")

    cursor_fields = [
        "Site_ID", 
        "Latitude", 
        "Longitude",
        "Population_Density", 
        "Competitor_Density", 
        "Score_Demand_40", 
        "Score_Infrastruct_40", 
        "Score_GridGap_20", 
        "Final_MCDA_Score"
    ]

    with arcpy.da.UpdateCursor(target_fc, cursor_fields) as cursor:
        for row in cursor:
            site_id = row[0]
            lat = row[1]
            lon = row[2]
            pop_density = row[3] if row[3] is not None else 5000  
            comp_density = row[4] if row[4] is not None else 2

            # --- LIVE OSM INFRASTRUCTURE QUERY ---
            try:
                print(f"Fetching live road network for {site_id} ({lat}, {lon})...")
                G = ox.graph_from_point((lat, lon), dist=2000, network_type='drive')
                road_accessibility_factor = len(G.nodes) / 100.0  
                road_dist_km = max(0.1, 3.0 / (road_accessibility_factor + 0.5))
            except Exception as e:
                print(f"Warning: Live OSM fetch failed for {site_id} ({e}). Using default fallback.")
                road_dist_km = 1.5

            # --- MATHEMATICAL SCORING LOGIC ---
            # Pillar 1: Demand Density (Max 40 points)
            score_demand = min(40.0, (pop_density / 15000.0) * 40.0)
            
            # Pillar 2: Infrastructure / Proximity (Max 40 points)
            score_infrastructure = max(5.0, 40.0 - (road_dist_km * 10.0))
            
            # Pillar 3: Competitor Gap (Max 20 points)
            score_grid_gap = max(2.0, 20.0 - (comp_density * 3.0))
            
            # Final 100-Point Composite Score Calculation
            final_score = score_demand + score_infrastructure + score_grid_gap
            
            # Update row values
            row[5] = score_demand
            row[6] = score_infrastructure
            row[7] = score_grid_gap
            row[8] = final_score
            
            cursor.updateRow(row)
            print(f"Processed {site_id} --> Live Road Prox: {road_dist_km:.2f}km --> Final Score: {final_score:.1f}/100")

    print(">>> Step 5: Live OpenStreetMap MCDA Scoring Matrix successfully computed.")

run_spatial_scoring(target_points)

# --- STEP 4: AUTOMATED EXECUTIVE REPORT GENERATION ---
def generate_executive_report(target_fc, output_dir):
    print(">>> Step 6: Generating client-ready executive summary report...")
    report_path = os.path.join(output_dir, "Spatial_Audit_Executive_Summary.txt")
    
    with open(report_path, "w") as f:
        f.write("====================================================\n")
        f.write("       SPATIAL AUDIT-AS-A-SERVICE: EXECUTIVE REPORT\n")
        f.write("       Multi-Criteria Decision Analysis (MCDA) Matrix\n")
        f.write(f"       Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("====================================================\n\n")
        f.write("RANKING SUMMARY (Top Evaluated Expansion Sites):\n")
        f.write("-" * 52 + "\n")
        f.write(f"{'Site ID':<10} | {'Site Name':<30} | {'Score':<6}\n")
        f.write("-" * 52 + "\n")
        
        with arcpy.da.SearchCursor(target_fc, ["Site_ID", "Site_Name", "Final_MCDA_Score"]) as cursor:
            rows = sorted(list(cursor), key=lambda x: x[2], reverse=True)
            for row in rows:
                f.write(f"{row[0]:<10} | {row[1]:<30} | {row[2]:<5.1f}/100\n")
                
        f.write("-" * 52 + "\n\n")
        f.write("METHODOLOGY NOTE:\n")
        f.write("Evaluated via 100-point weighted composite framework:\n")
        f.write(" - Demand Density & Demographics (40%)\n")
        f.write(" - Live OpenStreetMap Infrastructure & Proximity (40%)\n")
        f.write(" - Competitor Gap & Grid Feasibility (20%)\n")
        f.write("\nCONFIDENTIAL: Prepared by Spatial Audit Engine.")

    print(f">>> Step 7: Executive report successfully compiled at: {report_path}")

generate_executive_report(target_points, output_pdf_dir)