# -*- coding: utf-8 -*-
"""Mixed_Integer_Lineer_Programming_Model.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1uhHOePvsgO1H60Ug3Z5UdI34AXtSsxMe
"""

import cvxpy as cp
import numpy as np
import pandas as pd
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
from google.colab import drive
drive.mount('/content/drive')

# Path to the Excel file
excel_path = "/content/drive/MyDrive/Tilburg University/OP FOR DS/Data OPT for DS.xlsx"

########################################
### 1. Nodes Sheet: Read data and normalize location types
########################################
print("\n--- Reading Nodes Sheet ---")
df_nodes = pd.read_excel(excel_path, sheet_name="Nodes", engine="openpyxl")
print("Nodes DataFrame:")
print(df_nodes.to_string())

# Normalize location types (removing angle brackets):
beneficiary_camps = df_nodes[df_nodes["LocationTYpe"].str.upper().str.strip() == "BENEFICIARY CAMP"]["Location"] \
    .str.replace("[<>]", "", regex=True).unique()
ports = df_nodes[df_nodes["LocationTYpe"].str.upper().str.strip() == "PORT"]["Location"] \
    .str.replace("[<>]", "", regex=True).unique()
warehouses = df_nodes[df_nodes["LocationTYpe"].str.upper().str.strip() == "WAREHOUSE"]["Location"] \
    .str.replace("[<>]", "", regex=True).unique()

print("\nBeneficiary Camps:", beneficiary_camps)
print("Ports:", ports)
print("Warehouses:", warehouses)

# Relevant dictionaries (names normalized)
beneficiaries_dict = dict(zip(
    df_nodes["Location"].str.upper().str.strip().str.replace("[<>]", "", regex=True),
    df_nodes["#Beneficiaries"].fillna(0)
))
port_capacity_dict = dict(zip(
    df_nodes[df_nodes["LocationTYpe"].str.upper().str.strip() == "PORT"]["Location"]
        .str.upper().str.strip().str.replace("[<>]", "", regex=True),
    df_nodes[df_nodes["LocationTYpe"].str.upper().str.strip() == "PORT"]["Port capacity (mt/month)"].fillna(0)
))
handling_cost_dict = dict(zip(
    df_nodes["Location"].str.upper().str.strip().str.replace("[<>]", "", regex=True),
    df_nodes["Handling cost ($/ton)"].fillna(0)
))
warehouse_cap_dict = dict(zip(
    df_nodes[df_nodes["LocationTYpe"].str.upper().str.strip() == "WAREHOUSE"]["Location"]
        .str.upper().str.strip().str.replace("[<>]", "", regex=True),
    df_nodes[df_nodes["LocationTYpe"].str.upper().str.strip() == "WAREHOUSE"]["Port capacity (mt/month)"].fillna(0)
))
warehouse_handling_dict = dict(zip(
    df_nodes[df_nodes["LocationTYpe"].str.upper().str.strip() == "WAREHOUSE"]["Location"]
        .str.upper().str.strip().str.replace("[<>]", "", regex=True),
    df_nodes[df_nodes["LocationTYpe"].str.upper().str.strip() == "WAREHOUSE"]["Handling cost ($/ton)"]
        .fillna(0).astype(float)
))

print("\nBeneficiaries Dict:")
print(beneficiaries_dict)
print("\nPort Capacity Dict:")
print(port_capacity_dict)
print("\nHandling Cost Dict:")
print(handling_cost_dict)
print("\nWarehouse Capacity Dict:")
print(warehouse_cap_dict)
print("\nWarehouse Handling Dict:")
print(warehouse_handling_dict)

# Dictionary for location types (angle brackets removed)
location_type_dict = dict(zip(
    df_nodes["Location"].str.upper().str.strip().str.replace("[<>]", "", regex=True),
    df_nodes["LocationTYpe"].str.upper().str.strip()
))

########################################
### 2. Commodities, Nutrients, Nutritional Values Sheets
########################################
print("\n--- Reading Commodities Sheet ---")
df_commodities = pd.read_excel(excel_path, sheet_name="Commodities", engine="openpyxl")
df_commodities["Commodity"] = df_commodities["Commodity"].str.upper().str.strip()
print("Commodities DataFrame:")
print(df_commodities.to_string())

commodities = df_commodities["Commodity"].unique()
print("\nUnique Commodities:", commodities)

print("\n--- Reading Nutrients (Daily Requirements) Sheet ---")
df_nutrients = pd.read_excel(excel_path, sheet_name="Nutrients", engine="openpyxl")
df_nutrients.columns = ["Nutrient", "Daily Requirement"]
df_nutrients["Nutrient"] = df_nutrients["Nutrient"].str.upper().str.replace(".", "").str.strip()
df_nutrients["Daily Requirement"] = df_nutrients["Daily Requirement"].astype(str).str.replace(",", ".").astype(float)
print("Nutrients DataFrame:")
print(df_nutrients.to_string())

nutrient_names = df_nutrients["Nutrient"].unique()
daily_req_dict = dict(zip(df_nutrients["Nutrient"], df_nutrients["Daily Requirement"]))
print("\nNutrient Names:", nutrient_names)
print("Daily Requirement Dict:")
print(daily_req_dict)

print("\n--- Reading Nutritional Values Sheet ---")
df_nutr_values = pd.read_excel(excel_path, sheet_name="Nutritional values", engine="openpyxl")
df_nutr_values.rename(columns=lambda x: x.strip(), inplace=True)
nutr_value_col = "Nutritional value (value/100 gram)!!"
df_nutr_values["Commodity"] = df_nutr_values["Commodity"].str.upper().str.strip()
df_nutr_values["Nutrient"] = df_nutr_values["Nutrient"].str.upper().str.replace(".", "").str.strip()
print("Nutritional Values DataFrame:")
print(df_nutr_values.to_string())

nutr_value_df = df_nutr_values.pivot(index="Commodity", columns="Nutrient", values=nutr_value_col).fillna(0)
nutr_value_df.columns = [col.upper().replace(".", "").strip() for col in nutr_value_df.columns]
nutr_value_df.index = nutr_value_df.index.str.upper().str.strip()
print("\nPivoted Nutritional Values DataFrame:")
print(nutr_value_df.to_string())

commodity_list_nutr = nutr_value_df.index.tolist()
nutr_list_nutr = nutr_value_df.columns.tolist()
print("\nCommodity List (for Nutrients):", commodity_list_nutr)
print("Nutrient List:", nutr_list_nutr)

conversion_factor = 10000
nutr_matrix = np.zeros((len(commodity_list_nutr), len(nutr_list_nutr)))
for i, com in enumerate(commodity_list_nutr):
    for j, nut in enumerate(nutr_list_nutr):
        val_100g = nutr_value_df.loc[com, nut]
        nutr_matrix[i, j] = float(str(val_100g).replace(",", ".")) * conversion_factor
print("\nNutrient Matrix (after conversion):")
print(nutr_matrix)

########################################
### 3. Procurement Sheet
########################################
print("\n--- Reading Procurement Sheet ---")
df_proc = pd.read_excel(excel_path, sheet_name="Procurement", engine="openpyxl")
df_proc["Supplier"] = df_proc["Supplier"].astype(str).str.strip().str.upper()
df_proc["Commodity"] = df_proc["Commodity"].astype(str).str.strip().str.upper()
print("Procurement DataFrame:")
print(df_proc.to_string())

suppliers = df_proc["Supplier"].unique().tolist()
commodities_proc = df_proc["Commodity"].unique().tolist()
n_suppliers = len(suppliers)
n_commodities_proc = len(commodities_proc)
print("\nSuppliers:", suppliers)
print("Commodities (Procurement):", commodities_proc)

capacity = np.zeros((n_suppliers, n_commodities_proc))
proc_cost = np.zeros((n_suppliers, n_commodities_proc))
for i, sup in enumerate(suppliers):
    for j, com in enumerate(commodities_proc):
        row = df_proc[(df_proc["Supplier"] == sup) & (df_proc["Commodity"] == com)]
        if not row.empty:
            capacity[i, j] = row["Procurement capacity (ton/month)"].values[0]
            proc_cost[i, j] = row["Procurement price ($/ton)"].values[0]
        else:
            capacity[i, j] = 0
            proc_cost[i, j] = 1e3

########################################
### 4. LandTransport Sheet
########################################
print("\n--- Reading LandTransport Sheet ---")
df_land = pd.read_excel(excel_path, sheet_name="LandTransport", engine="openpyxl")
print("LandTransport DataFrame:")
print(df_land.to_string())

df_land["Origin_Normalized"] = df_land["Origin"].str.upper().str.strip().str.replace("[<>]", "", regex=True)
df_land["Destination_Normalized"] = df_land["Destination"].str.upper().str.strip().str.replace("[<>]", "", regex=True)
df_land["Origin_Type"] = df_land["Origin_Normalized"].map(location_type_dict)
df_land["Destination_Type"] = df_land["Destination_Normalized"].map(location_type_dict)
print("\nFlagged LandTransport data (first 10 records):")
print(df_land.head(10).to_string())

df_port_to_wh = df_land[(df_land["Origin_Type"] == "PORT") & (df_land["Destination_Type"] == "WAREHOUSE")].copy()
df_wh_to_camp = df_land[(df_land["Origin_Type"] == "WAREHOUSE") & (df_land["Destination_Type"] == "BENEFICIARY CAMP")].copy()

land_cost_port_to_wh = {
    (row.Origin_Normalized, row.Destination_Normalized): row[2]
    for row in df_port_to_wh.itertuples(index=False)
}
land_cost_wh_to_camp = {
    (row.Origin_Normalized, row.Destination_Normalized): row[2]
    for row in df_wh_to_camp.itertuples(index=False)
}

print("\nPort-to-Warehouse Land Transport Cost Dict:")
print(land_cost_port_to_wh)
print("\nWarehouse-to-Camp Land Transport Cost Dict:")
print(land_cost_wh_to_camp)

########################################
### 5. SeaTransport Sheet
########################################
print("\n--- Reading SeaTransport Sheet ---")
df_sea = pd.read_excel(excel_path, sheet_name="SeaTransport", engine="openpyxl")
df_sea["Origin"] = df_sea["Origin"].str.upper().str.strip()
df_sea["Destination"] = df_sea["Destination"].str.upper().str.strip()
df_sea["Commodity"] = df_sea["Commodity"].str.upper().str.strip()

sea_cost_dict = {}
for _, row in df_sea.iterrows():
    key = (row["Origin"], row["Destination"], row["Commodity"])
    sea_cost_dict[key] = row["SeaTransport cost ($/ton)"]
print(f"Loaded {len(sea_cost_dict)} sea transportation routes")

########################################
### 6. All Nodes and Dimensions
########################################
all_nodes = list(ports) + list(warehouses) + list(beneficiary_camps)
print("\nAll Nodes (all_nodes):", all_nodes)
n_ports = len(ports)
n_warehouses = len(warehouses)
n_camps = len(beneficiary_camps)
days = 30
n_nutrients = len(nutrient_names)
print(f"\nn_ports: {n_ports}, n_warehouses: {n_warehouses}, n_camps: {n_camps}, days: {days}, n_nutrients: {n_nutrients}")

########################################
### 7. MILP Model Setup: Define Decision Variables
########################################
print("\n--- MILP Model Setup ---")
# For a MILP, we'll define the decision variables as integer. (Use x>=0 for non-negativity.)
x = cp.Variable((n_suppliers, n_ports, n_commodities_proc), integer=True)
y = cp.Variable((n_ports, n_warehouses, n_commodities_proc), integer=True)
z = cp.Variable((n_warehouses, n_camps, n_commodities_proc), integer=True)

# Add non-negativity constraints:
nonneg_constraints = [x >= 0, y >= 0, z >= 0]

########################################
### 8. Extra Constraints: Only allow routes defined in Excel
########################################
constraint_groups_extra = []
# Port-to-Warehouse:
for p in range(n_ports):
    port_norm = ports[p].upper().strip()
    for w in range(n_warehouses):
        wh_norm = warehouses[w].upper().strip()
        if (port_norm, wh_norm) not in land_cost_port_to_wh:
            for f in range(n_commodities_proc):
                constraint_groups_extra.append(y[p, w, f] == 0)
# Warehouse-to-Camp:
for w in range(n_warehouses):
    wh_norm = warehouses[w].upper().strip()
    for c in range(n_camps):
        camp_norm = beneficiary_camps[c].upper().strip()
        if (wh_norm, camp_norm) not in land_cost_wh_to_camp:
            for f in range(n_commodities_proc):
                constraint_groups_extra.append(z[w, c, f] == 0)
# SeaTransport: disallow supplier-port-commodity combinations that are not defined in Excel
for s in range(n_suppliers):
    for p in range(n_ports):
        for f in range(n_commodities_proc):
            key = (suppliers[s], ports[p], commodities_proc[f])
            if key not in sea_cost_dict:
                constraint_groups_extra.append(x[s, p, f] == 0)

########################################
### 9. Defining Constraint Groups
########################################
constraint_groups = {}

# 1. Supplier Capacity Constraints:
for s in range(n_suppliers):
    for f in range(n_commodities_proc):
        constraint_groups.setdefault("supplier_capacity", []).append(cp.sum(x[s, :, f]) <= capacity[s, f])

# 2. Port Balance Direct Constraint:
for p in range(n_ports):
    for f in range(n_commodities_proc):
        constraint_groups.setdefault("port_balance_direct", []).append(cp.sum(x[:, p, f]) == cp.sum(y[p, :, f]))

# 3. Warehouse Balance Constraints:
for w, wh_name in enumerate(warehouses):
    wh_norm = wh_name.upper().strip()
    # If the warehouse has a capacity > 0, add a usage constraint:
    if wh_norm in warehouse_cap_dict and warehouse_cap_dict[wh_norm] > 0:
        constraint_groups.setdefault("warehouse_balance", []).append(
            cp.sum(z[w, :, :]) <= warehouse_cap_dict[wh_norm]
        )
    # Flow in = Flow out for each commodity
    for f in range(n_commodities_proc):
        constraint_groups.setdefault("warehouse_balance", []).append(
            cp.sum(y[:, w, f]) == cp.sum(z[w, c, f] for c in range(n_camps))
        )

# 4. Port Capacity Constraints:
for p, port_name in enumerate(ports):
    port_norm = port_name.upper().strip()
    port_cap = port_capacity_dict.get(port_norm, 0)
    if port_cap > 0:
        constraint_groups.setdefault("port_capacity", []).append(cp.sum(x[:, p, :]) <= port_cap)

# 5. Camp Demand Constraints (Hard Constraint):
for c, camp_name in enumerate(beneficiary_camps):
    camp_norm = camp_name.upper().strip()
    camp_population = beneficiaries_dict.get(camp_norm, 0)
    min_food_per_person_daily_g = 300  # 300 grams per person per day
    base_demand = camp_population * days * min_food_per_person_daily_g / 1_000_000
    constraint_groups.setdefault("camp_demand", []).append(cp.sum(z[:, c, :]) >= base_demand)

# 6. Nutritional Constraints (Hard Constraint):
for c in range(n_camps):
    camp_norm = beneficiary_camps[c].upper().strip()
    camp_population = beneficiaries_dict.get(camp_norm, 0)
    for j, nutr_name in enumerate(nutr_list_nutr):
        if nutr_name not in daily_req_dict:
            continue
        base_req = daily_req_dict[nutr_name] * days * camp_population
        constraint_groups.setdefault("nutritional", []).append(
            cp.sum(cp.multiply(z[:, c, :], np.tile(nutr_matrix[:, j], (1,)))) >= base_req
        )

constraint_groups.setdefault("route_availability", []).extend(constraint_groups_extra)

all_constraints = nonneg_constraints
for group in constraint_groups.values():
    all_constraints += group

########################################
### 10. Cost Functions
########################################
def calc_procurement_cost(x, proc_cost):
    n_ports_local = x.shape[1]
    proc_cost_rep = np.tile(proc_cost[:, None, :], (1, n_ports_local, 1))
    return cp.sum(cp.multiply(x, proc_cost_rep))

def calc_port_handling_cost(x, handling_cost_dict):
    cost = 0
    for p, port_name in enumerate(ports):
        port_norm = port_name.upper().strip()
        handle_c = handling_cost_dict.get(port_norm, 0)
        cost += handle_c * cp.sum(x[:, p, :])
    return cost

def calc_land_transport_cost(y, land_cost_dict):
    cost = 0
    for p, port_name in enumerate(ports):
        port_norm = port_name.upper().strip()
        for w, wh_name in enumerate(warehouses):
            key = (port_norm, wh_name.upper().strip())
            land_c = land_cost_dict.get(key, 0)
            cost += land_c * cp.sum(y[p, w, :])
    return cost

def calc_warehouse_handling_cost(y, warehouse_handling_dict):
    cost = 0
    for w, wh_name in enumerate(warehouses):
        wh_norm = wh_name.upper().strip()
        wh_c = warehouse_handling_dict.get(wh_norm, 0)
        cost += wh_c * cp.sum(y[:, w, :])
    return cost

def calc_warehouse_to_camp_cost(z, land_cost_dict):
    cost = 0
    for w, wh_name in enumerate(warehouses):
        wh_norm = wh_name.upper().strip()
        for c, camp_name in enumerate(beneficiary_camps):
            camp_norm = camp_name.upper().strip()
            key = (wh_norm, camp_norm)
            land_c = land_cost_dict.get(key, 0)
            cost += land_c * cp.sum(z[w, c, :])
    return cost

def calc_sea_transport_cost(x, sea_cost_dict):
    cost = 0
    for s, supplier in enumerate(suppliers):
        for p, port in enumerate(ports):
            for f, commodity in enumerate(commodities_proc):
                key = (supplier, port, commodity)
                sea_c = sea_cost_dict.get(key, 0)
                cost += sea_c * cp.sum(x[s, p, f])
    return cost

cost_procurement = calc_procurement_cost(x, proc_cost)
cost_sea_transport = calc_sea_transport_cost(x, sea_cost_dict)
cost_port_handling = calc_port_handling_cost(x, handling_cost_dict)
cost_port_to_wh = calc_land_transport_cost(y, land_cost_port_to_wh)
cost_wh_handling = calc_warehouse_handling_cost(y, warehouse_handling_dict)
cost_wh_to_camp = calc_warehouse_to_camp_cost(z, land_cost_wh_to_camp)

total_cost = (
    cost_procurement
    + cost_port_handling
    + cost_sea_transport
    + cost_port_to_wh
    + cost_wh_handling
    + cost_wh_to_camp
)

objective = cp.Minimize(total_cost)
milp_problem = cp.Problem(objective, all_constraints)

# Because we have integer variables, we cannot do sensitivity (shadow price) analysis with MILP.
print("\nBuilding and solving the MILP Model...")
# For MILP, we use an appropriate solver (e.g., GUROBI, CPLEX, or CBC).
# Below, CBC is used. If it's not installed, you can change the solver parameter.
# Here, we set a time limit of 600,000 ms (10 minutes) and a 5% MIP gap:
result_milp = milp_problem.solve(solver=cp.GLPK_MI, verbose=True, tm_lim=600000, mip_gap=0.05)
print("\nMILP Solver Status:", milp_problem.status)
print("MILP Optimal Total Cost:", milp_problem.value)

########################################
### Additional: Nutritional Balance Analysis
########################################
print("\n======= Nutritional Balance Analysis (For Each Camp) =======")
total_camps = len(beneficiary_camps)
fully_met = 0
partially_met = 0
for c, camp in enumerate(beneficiary_camps):
    camp_norm = camp.upper().strip()
    population = beneficiaries_dict.get(camp_norm, 0)
    if population <= 0:
        continue
    # Calculate total nutrient amounts:
    total_nutrients = np.zeros(len(nutr_list_nutr))
    for w in range(n_warehouses):
        for f, com in enumerate(commodities_proc):
            flow = z.value[w, c, f]
            if flow > 1e-3:
                if com in commodity_list_nutr:
                    i = commodity_list_nutr.index(com)
                    total_nutrients += flow * nutr_matrix[i, :]
    nutrient_per_person = total_nutrients / (population * days)
    met_all = True
    print(f"\nCamp: {camp_norm} | Population: {population}")
    for j, nutr in enumerate(nutr_list_nutr):
        daily_req = daily_req_dict.get(nutr, 0)
        provided = nutrient_per_person[j]
        pct = (provided / daily_req * 100) if daily_req > 0 else 0
        status = "Sufficient" if pct >= 100 else "Insufficient"
        if pct < 100:
            met_all = False
        print(f"  {nutr}: Provided = {provided:.2f} (Required per day = {daily_req:.2f}) -> %{pct:.1f} -> {status}")
    if met_all:
        fully_met += 1
    else:
        partially_met += 1
print(f"\nTotal Camps: {total_camps} | Fully Met: {fully_met} | Partially/Not Met: {partially_met}")

########################################
### Additional: Facility Utilization Analysis
########################################
print("\n======= Facility Utilization Analysis =======")
print("\nPort Utilization:")
for p, port in enumerate(ports):
    usage = sum(x.value[s, p, f] for s in range(n_suppliers) for f in range(n_commodities_proc))
    capacity_val = port_capacity_dict.get(port.upper().strip(), None)
    if capacity_val and capacity_val > 0:
        utilization = usage / capacity_val * 100
        print(f"  {port}: Usage = {usage:.2f} / Capacity = {capacity_val:.2f} ({utilization:.1f}%)")
    else:
        print(f"  {port}: Usage = {usage:.2f} (No capacity info)")
print("\nWarehouse Utilization:")
for w, wh in enumerate(warehouses):
    usage = sum(y.value[p, w, f] for p in range(n_ports) for f in range(n_commodities_proc))
    capacity_val = warehouse_cap_dict.get(wh.upper().strip(), None)
    if capacity_val and capacity_val > 0:
        utilization = usage / capacity_val * 100
        print(f"  {wh}: Usage = {usage:.2f} / Capacity = {capacity_val:.2f} ({utilization:.1f}%)")
    else:
        print(f"  {wh}: Usage = {usage:.2f} (No capacity info)")

########################################
### Additional: Cost Breakdown & Unit Cost Analysis
########################################
print("\n======= Cost Breakdown Analysis =======")
proc_cost_total = cost_procurement.value
sea_transport_total = cost_sea_transport.value
port_handling_total = cost_port_handling.value
port_to_wh_total = cost_port_to_wh.value
wh_handling_total = cost_wh_handling.value
wh_to_camp_total = cost_wh_to_camp.value
print(f"  Procurement Cost: ${proc_cost_total:.2f}")
print(f"  Sea Transport Cost: ${sea_transport_total:.2f}")
print(f"  Port Handling Cost: ${port_handling_total:.2f}")
print(f"  Port->Warehouse Transport Cost: ${port_to_wh_total:.2f}")
print(f"  Warehouse Handling Cost: ${wh_handling_total:.2f}")
print(f"  Warehouse->Camp Transport Cost: ${wh_to_camp_total:.2f}")
print(f"  Total Cost: ${total_cost.value:.2f}")

# Additional per-unit cost calculations:
total_ton = 0
for s in range(n_suppliers):
    for p in range(n_ports):
        for f in range(n_commodities_proc):
            total_ton += x.value[s, p, f]
if total_ton > 0:
    cost_per_ton = total_cost.value / total_ton
    print(f"\nUnit Cost: Average cost per 1 ton of commodities = ${cost_per_ton:.2f}")
else:
    print("\nTotal transported tonnage is zero, unable to calculate unit cost.")

total_population = sum(beneficiaries_dict.get(camp.upper().strip(), 0) for camp in beneficiary_camps)
if total_population > 0:
    cost_per_person_per_day = total_cost.value / (total_population * days)
    print(f"Cost to feed one person per day = ${cost_per_person_per_day:.2f}")
else:
    print("\nTotal population is zero, unable to calculate cost per person.")

########################################
### Reporting the Solution Results
########################################
print("\n--- Final Values of Decision Variables ---")
print("x (Supplier -> Port) solution values:")
print(x.value)
print("\ny (Port -> Warehouse) solution values:")
print(y.value)
print("\nz (Warehouse -> Camp) solution values:")
print(z.value)

########################################
### DETAILED FLOW BREAKDOWN
########################################
# 1. Procurement Flow Breakdown: Supplier -> Port
proc_flow_data = []
for s in range(n_suppliers):
    for p in range(n_ports):
        for f in range(n_commodities_proc):
            flow = x.value[s, p, f]
            if flow > 1e-3:
                cost_val = proc_cost[s, f]
                proc_flow_data.append([
                    suppliers[s], ports[p], commodities_proc[f], flow, cost_val, flow * cost_val
                ])
proc_df = pd.DataFrame(proc_flow_data, columns=[
    "Supplier", "Port", "Commodity", "Flow", "Procurement Price", "Cost"
])
print("\n--- Procurement Flow Breakdown ---")
print(proc_df.to_string())

# 2. Sea Transport Flow Breakdown: Supplier -> Port
sea_flow_data = []
for s in range(n_suppliers):
    for p in range(n_ports):
        for f in range(n_commodities_proc):
            flow = x.value[s, p, f]
            if flow > 1e-3:
                key = (suppliers[s], ports[p], commodities_proc[f])
                sea_cost = sea_cost_dict.get(key, 0)
                sea_flow_data.append([
                    suppliers[s], ports[p], commodities_proc[f], flow, sea_cost, flow * sea_cost
                ])
sea_flow_df = pd.DataFrame(sea_flow_data, columns=[
    "Supplier", "Port", "Commodity", "Flow", "Sea Transport Cost", "Cost"
])
print("\n--- Sea Transport Flow Breakdown ---")
print(sea_flow_df.to_string())

# 3. Port-to-Warehouse Transport Flow Breakdown: Port -> Warehouse
port_to_wh_data = []
for p in range(n_ports):
    for w in range(n_warehouses):
        for f in range(n_commodities_proc):
            flow = y.value[p, w, f]
            if flow > 1e-3:
                key = (ports[p].upper().strip(), warehouses[w].upper().strip())
                cost_val = land_cost_port_to_wh.get(key, 0)
                port_to_wh_data.append([
                    ports[p], warehouses[w], commodities_proc[f], flow, cost_val, flow * cost_val
                ])
port_to_wh_df = pd.DataFrame(port_to_wh_data, columns=[
    "Port", "Warehouse", "Commodity", "Flow", "Land Cost", "Cost"
])
print("\n--- Port-to-Warehouse Transport Flow Breakdown ---")
print(port_to_wh_df.to_string())

# 4. Warehouse-to-Camp Transport Flow Breakdown: Warehouse -> Camp
wh_to_camp_data = []
for w in range(n_warehouses):
    for c in range(n_camps):
        for f in range(n_commodities_proc):
            flow = z.value[w, c, f]
            if flow > 1e-3:
                key = (warehouses[w].upper().strip(), beneficiary_camps[c].upper().strip())
                cost_val = land_cost_wh_to_camp.get(key, 0)
                wh_to_camp_data.append([
                    warehouses[w], beneficiary_camps[c], commodities_proc[f],
                    flow, cost_val, flow * cost_val
                ])
wh_to_camp_df = pd.DataFrame(wh_to_camp_data, columns=[
    "Warehouse", "Camp", "Commodity", "Flow", "Land Cost", "Cost"
])
print("\n--- Warehouse-to-Camp Transport Flow Breakdown ---")
print(wh_to_camp_df.to_string())

########################################
### After the MILP Solution: Cost Breakdown & Unit Cost Analysis
########################################
print("\n======= MILP Cost Breakdown Analysis =======")
proc_cost_total_milp = cost_procurement.value
sea_transport_total_milp = cost_sea_transport.value
port_handling_total_milp = cost_port_handling.value
port_to_wh_total_milp = cost_port_to_wh.value
wh_handling_total_milp = cost_wh_handling.value
wh_to_camp_total_milp = cost_wh_to_camp.value

print(f"  Procurement Cost: ${proc_cost_total_milp:.2f}")
print(f"  Sea Transport Cost: ${sea_transport_total_milp:.2f}")
print(f"  Port Handling Cost: ${port_handling_total_milp:.2f}")
print(f"  Port->Warehouse Transport Cost: ${port_to_wh_total_milp:.2f}")
print(f"  Warehouse Handling Cost: ${wh_handling_total_milp:.2f}")
print(f"  Warehouse->Camp Transport Cost: ${wh_to_camp_total_milp:.2f}")

total_cost_milp = total_cost.value
print(f"  Total Cost: ${total_cost_milp:.2f}")

# Additional per-unit cost calculations:
total_ton_milp = 0
for s in range(n_suppliers):
    for p in range(n_ports):
        for f in range(n_commodities_proc):
            total_ton_milp += x.value[s, p, f]
if total_ton_milp > 0:
    cost_per_ton_milp = total_cost_milp / total_ton_milp
    print(f"\nUnit Cost: Average cost per 1 ton of commodities = ${cost_per_ton_milp:.2f}")
else:
    print("\nTotal transported tonnage is zero, unable to calculate unit cost.")

# Calculate total population and cost per person per day:
total_population = sum(beneficiaries_dict.get(camp.upper().strip(), 0) for camp in beneficiary_camps)
if total_population > 0:
    cost_per_person_per_day = total_cost_milp / (total_population * days)
    print(f"Cost to feed one person per day = ${cost_per_person_per_day:.2f}")
else:
    print("\nTotal population is zero, unable to calculate cost per person.")

########################################
### Percentage Shares of MILP Cost Components
########################################
print("\n======= Percentage Shares of MILP Cost Components =======")
def print_share(name, comp_cost):
    pct = (comp_cost / total_cost_milp * 100) if total_cost_milp > 0 else 0
    print(f"  {name}: ${comp_cost:.2f} -> %{pct:.1f}")

print_share("Procurement Cost", proc_cost_total_milp)
print_share("Sea Transport Cost", sea_transport_total_milp)
print_share("Port Handling Cost", port_handling_total_milp)
print_share("Port->Warehouse Transport Cost", port_to_wh_total_milp)
print_share("Warehouse Handling Cost", wh_handling_total_milp)
print_share("Warehouse->Camp Transport Cost", wh_to_camp_total_milp)