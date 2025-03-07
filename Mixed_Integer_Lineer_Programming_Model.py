# -*- coding: utf-8 -*-
"""Çabalıyorum  MILP Eklemeli.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1PumHTjm_dOxxnSZQrIWIBuDgydBX8lXb
"""

import cvxpy as cp
import numpy as np
import pandas as pd
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
from google.colab import drive
drive.mount('/content/drive')

# Excel dosya yolu
excel_path = "/content/drive/MyDrive/Tilburg University/OP FOR DS/Data OPT for DS.xlsx"

# ---------- Nodes ----------
df_nodes = pd.read_excel(excel_path, sheet_name="Nodes", engine="openpyxl")
beneficiary_camps = df_nodes[df_nodes["LocationTYpe"] == "Beneficiary Camp"]["Location"].unique()
ports = df_nodes[df_nodes["LocationTYpe"] == "Port"]["Location"].unique()
warehouses = df_nodes[df_nodes["LocationTYpe"] == "Warehouse"]["Location"].unique()
beneficiaries_dict = dict(zip(df_nodes["Location"], df_nodes["#Beneficiaries"].fillna(0)))
port_capacity_dict = dict(zip(df_nodes["Location"], df_nodes["Port capacity (mt/month)"].fillna(0)))
handling_cost_dict = dict(zip(df_nodes["Location"], df_nodes["Handling cost ($/ton)"].fillna(0)))
warehouse_cap_dict = dict(zip(df_nodes["Location"], df_nodes.get("Warehouse capacity", pd.Series()).fillna(0)))
warehouse_handling_dict = {wh: 0 for wh in warehouses}

# ---------- Commodities ----------
df_commodities = pd.read_excel(excel_path, sheet_name="Commodities", engine="openpyxl")
df_commodities["Commodity"] = df_commodities["Commodity"].str.upper().str.strip().str.rstrip("S")
commodities = df_commodities["Commodity"].unique()

# ---------- Nutrients (Daily Requirements) ----------
df_nutrients = pd.read_excel(excel_path, sheet_name="Nutrients", engine="openpyxl")
df_nutrients.columns = ["Nutrient", "Daily Requirement"]
df_nutrients["Nutrient"] = df_nutrients["Nutrient"].str.upper().str.replace(".", "").str.strip()
df_nutrients["Daily Requirement"] = df_nutrients["Daily Requirement"].astype(str).str.replace(",", ".").astype(float)
nutrient_names = df_nutrients["Nutrient"].unique()
daily_req_dict = dict(zip(df_nutrients["Nutrient"], df_nutrients["Daily Requirement"]))

# ---------- Nutritional Values (Pivot) ----------
df_nutr_values = pd.read_excel(excel_path, sheet_name="Nutritional values", engine="openpyxl")
df_nutr_values.rename(columns=lambda x: x.strip(), inplace=True)
nutr_value_col = "Nutritional value (value/100 gram)!!"
df_nutr_values["Commodity"] = df_nutr_values["Commodity"].str.upper().str.strip().str.rstrip("S")
df_nutr_values["Nutrient"] = (df_nutr_values["Nutrient"]
                              .str.upper()
                              .str.replace(".", "")
                              .str.strip())
nutr_value_df = df_nutr_values.pivot(index="Commodity", columns="Nutrient", values=nutr_value_col).fillna(0)
nutr_value_df.columns = [col.upper().replace(".", "").strip() for col in nutr_value_df.columns]
nutr_value_df.index = nutr_value_df.index.str.upper().str.strip()
commodity_list_nutr = nutr_value_df.index.tolist()
nutr_list_nutr = nutr_value_df.columns.tolist()

conversion_factor = 10000
nutr_matrix = np.zeros((len(commodity_list_nutr), len(nutr_list_nutr)))
for i, com in enumerate(commodity_list_nutr):
    for j, nut in enumerate(nutr_list_nutr):
        val_100g = nutr_value_df.loc[com, nut]
        nutr_matrix[i, j] = float(str(val_100g).replace(",", ".")) * conversion_factor

# ---------- Procurement ----------
df_proc = pd.read_excel(excel_path, sheet_name="Procurement", engine="openpyxl")
df_proc["Supplier"] = df_proc["Supplier"].astype(str).str.strip().str.upper()
df_proc["Commodity"] = df_proc["Commodity"].astype(str).str.strip().str.upper().str.rstrip("S")
suppliers = df_proc["Supplier"].unique().tolist()
commodities_proc = df_proc["Commodity"].unique().tolist()
n_suppliers = len(suppliers)
n_commodities_proc = len(commodities_proc)
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
            proc_cost[i, j] = 1e6

df_sea = pd.read_excel(excel_path, sheet_name="SeaTransport", engine="openpyxl")
sea_cost_dict = {}
for row in df_sea.itertuples(index=False):
    key = (row.Origin, row.Destination, row.Commodity)
    sea_cost_dict[key] = row[3]

df_land = pd.read_excel(excel_path, sheet_name="LandTransport", engine="openpyxl")
land_cost_dict = {}
for row in df_land.itertuples(index=False):
    key = (row.Origin, row.Destination)
    land_cost_dict[key] = row[2]

n_ports = len(ports)
n_warehouses = len(warehouses)
n_camps = len(beneficiary_camps)
days = 30

# ---------- Integrated LP + MILP Eklemeleri ----------

# Karar değişkenleri (sürekli):
x = cp.Variable((n_suppliers, n_ports, n_commodities_proc), nonneg=True)
sea_flow = cp.Variable((n_ports, n_ports, n_commodities_proc), nonneg=True)
y = cp.Variable((n_ports, n_warehouses, n_commodities_proc), nonneg=True)
z = cp.Variable((n_warehouses, n_camps, n_commodities_proc), nonneg=True)

# Yeni: Tedarikçi kullanım binary değişkeni
supplier_active = cp.Variable(n_suppliers, boolean=True)

penalty_demand_param = cp.Parameter(nonneg=True, value=1e4)
penalty_nutr_param   = cp.Parameter(nonneg=True, value=1e6)

demand_slacks = {}
nutr_slacks = {}
constraint_groups = {}

# (A) Tedarikçi Kapasitesi + MILP Kısıtı
constraint_groups["supplier_capacity"] = []
# Big-M değerini, tedarikçinin olası max kapasitesine göre seçebiliriz:
M = np.max(capacity) * 10  # Örnek
for s in range(n_suppliers):
    for f in range(n_commodities_proc):
        # Normal kapasite kısıt
        constraint_groups["supplier_capacity"].append(
            cp.sum(x[s, :, f]) <= capacity[s, f]
        )
    # MILP Big-M kısıtı: eğer supplier_active[s] = 0 ise x[s,p,f] = 0
    constraint_groups["supplier_capacity"].append(
        cp.sum(x[s, :, :]) <= M * supplier_active[s]
    )

# (B) Liman Akış Dengesi: Tedarikçi -> Deniz
constraint_groups["port_flow_balance"] = []
for p in range(n_ports):
    for f in range(n_commodities_proc):
        constraint_groups["port_flow_balance"].append(
            cp.sum(x[:, p, f]) == cp.sum(sea_flow[p, :, f])
        )

# (C) Liman Dengesi: Deniz -> Depo
constraint_groups["port_balance"] = []
for d in range(n_ports):
    for f in range(n_commodities_proc):
        constraint_groups["port_balance"].append(
            cp.sum(sea_flow[:, d, f]) == cp.sum(y[d, :, f])
        )

# (D) Depo Dengesi ve Kapasitesi
constraint_groups["warehouse_balance"] = []
for w, wh_name in enumerate(warehouses):
    if wh_name in warehouse_cap_dict and warehouse_cap_dict[wh_name] > 0:
        constraint_groups["warehouse_balance"].append(
            cp.sum(z[w, :, :]) <= warehouse_cap_dict[wh_name]
        )
    for f in range(n_commodities_proc):
        constraint_groups["warehouse_balance"].append(
            cp.sum(y[:, w, f]) == cp.sum(z[w, :, f])
        )

# (E) Liman Kapasitesi
constraint_groups["port_capacity"] = []
for p, port_name in enumerate(ports):
    port_cap = port_capacity_dict.get(port_name, 0)
    if port_cap > 0:
        constraint_groups["port_capacity"].append(
            cp.sum(x[:, p, :]) <= port_cap
        )

# (F) Kamp Talep Kısıtı (Beneficiaries)
constraint_groups["camp_demand"] = []
for c, camp_name in enumerate(beneficiary_camps):
    camp_population = beneficiaries_dict.get(camp_name, 0)
    min_food_per_person = 0.0  # eğer sadece nutrient'e odaklanıyorsanız
    base_demand = camp_population * min_food_per_person
    slack = cp.Variable(nonneg=True, name=f"demand_slack_{c}")
    demand_slacks[c] = slack
    constraint_groups["camp_demand"].append(
        cp.sum(z[:, c, :]) + slack >= base_demand
    )

# (G) Nutrient Kısıtları
constraint_groups["nutritional"] = []
new_nutr_matrix = np.zeros((n_commodities_proc, len(nutr_list_nutr)))
for f, com in enumerate(commodities_proc):
    if com in commodity_list_nutr:
        idx = commodity_list_nutr.index(com)
        new_nutr_matrix[f, :] = nutr_matrix[idx, :]
    else:
        print(f"⚠️ Warning: {com} not found in nutrient values, assigning zero.")
        new_nutr_matrix[f, :] = np.zeros(len(nutr_list_nutr))

for c, camp_name in enumerate(beneficiary_camps):
    camp_population = beneficiaries_dict.get(camp_name, 0)
    for j, nutr_name in enumerate(nutr_list_nutr):
        if nutr_name not in daily_req_dict:
            continue
        base_req = daily_req_dict[nutr_name] * days * camp_population
        slack_nutr = cp.Variable(nonneg=True, name=f"nutr_slack_{c}_{j}")
        nutr_slacks[(c, j)] = slack_nutr
        constraint_groups["nutritional"].append(
            cp.sum(cp.multiply(z[:, c, :], new_nutr_matrix[:, j].reshape(1, -1))) + slack_nutr >= base_req
        )

all_constraints = []
for group in constraint_groups.values():
    all_constraints += group

# ---------- Cost Functions ----------
def calc_procurement_cost(x, proc_cost):
    n_ports_local = x.shape[1]
    proc_cost_rep = np.tile(proc_cost[:, None, :], (1, n_ports_local, 1))
    return cp.sum(cp.multiply(x, proc_cost_rep))

def calc_sea_transport_cost(sea_flow, sea_cost_dict):
    cost = 0
    for p in range(n_ports):
        for d in range(n_ports):
            for f_idx, com in enumerate(commodities_proc):
                key = (ports[p], ports[d], com)
                cost_val = sea_cost_dict.get(key, 0)
                cost += cost_val * sea_flow[p, d, f_idx]
    return cost

def calc_port_handling_cost(x, handling_cost_dict):
    cost = 0
    for p, port_name in enumerate(ports):
        handle_c = handling_cost_dict.get(port_name, 0)
        cost += handle_c * cp.sum(x[:, p, :])
    return cost

def calc_land_transport_cost(y, land_cost_dict):
    cost = 0
    for p, port_name in enumerate(ports):
        for w, wh_name in enumerate(warehouses):
            key = (port_name, wh_name)
            land_c = land_cost_dict.get(key, 0)
            cost += land_c * cp.sum(y[p, w, :])
    return cost

def calc_warehouse_handling_cost(y, warehouse_handling_dict):
    cost = 0
    for w, wh_name in enumerate(warehouses):
        wh_c = warehouse_handling_dict.get(wh_name, 0)
        cost += wh_c * cp.sum(y[:, w, :])
    return cost

def calc_warehouse_to_camp_cost(z, land_cost_dict):
    cost = 0
    for w, wh_name in enumerate(warehouses):
        for c, camp_name in enumerate(beneficiary_camps):
            key = (wh_name, camp_name)
            land_c = land_cost_dict.get(key, 0)
            cost += land_c * cp.sum(z[w, c, :])
    return cost

cost_procurement = calc_procurement_cost(x, proc_cost)
cost_sea_transport = calc_sea_transport_cost(sea_flow, sea_cost_dict)
cost_port_handling = calc_port_handling_cost(x, handling_cost_dict)
cost_port_to_wh = calc_land_transport_cost(y, land_cost_dict)
cost_wh_handling = calc_warehouse_handling_cost(y, warehouse_handling_dict)
cost_wh_to_camp = calc_warehouse_to_camp_cost(z, land_cost_dict)
total_cost = (cost_procurement + cost_sea_transport + cost_port_handling +
              cost_port_to_wh + cost_wh_handling + cost_wh_to_camp)

penalty_cost = penalty_demand_param * cp.sum(list(demand_slacks.values())) \
               + penalty_nutr_param * cp.sum(list(nutr_slacks.values()))
total_cost_with_slack = total_cost + penalty_cost

objective = cp.Minimize(total_cost_with_slack)

# Artık MILP modelini çözmek için GLPK_MI (veya başka bir MILP çözücü) kullanıyoruz.
milp_problem = cp.Problem(objective, all_constraints)
result_milp = milp_problem.solve(solver=cp.GLPK_MI, verbose=True)

print("\nMILP Solver Status:", milp_problem.status)
print("MILP Optimal Total Cost (with penalties):", result_milp)

print("\n--- Slack Variable Values ---")
print("Demand Slack Values:")
for key, slack in demand_slacks.items():
    print(f"Camp {key}: {slack.value}")

print("\nNutritional Slack Values:")
for key, slack in nutr_slacks.items():
    print(f"Camp {key[0]}, Nutrient {key[1]}: {slack.value}")

total_demand_slack = sum(slack.value for slack in demand_slacks.values())
total_nutr_slack = sum(slack.value for slack in nutr_slacks.values())
print(f"\nTotal Demand Slack: {total_demand_slack}")
print(f"Total Nutritional Slack: {total_nutr_slack}")

# Diyagnostik fonksiyon (opsiyonel, eğer assignment'ta kullanmak isterseniz)
def diagnose_constraint_groups(objective, constraint_groups):
    all_cons = []
    for group in constraint_groups.values():
        all_cons += group
    print("\nToplam kısıt sayısı:", len(all_cons))
    print("---- Kısıt Grubu Diyagnostik Sonuçları ----")
    for group_name, group_constraints in constraint_groups.items():
        remaining_constraints = [c for g, clist in constraint_groups.items() if g != group_name for c in clist]
        prob = cp.Problem(objective, remaining_constraints)
        try:
            result = prob.solve(solver=cp.GLPK_MI, verbose=False)
        except Exception as e:
            print(f"[{group_name}] çıkarılırken hata: {e}")
            continue
        print(f"[{group_name}] çıkarıldığında problem durumu: {prob.status}")

original_prob = cp.Problem(objective, all_constraints)
print("\nOrijinal problem durumu:", original_prob.status)
diagnose_constraint_groups(objective, constraint_groups)


(CVXPY) Mar 04 04:04:10 PM: Your problem has 5000 variables, 944 constraints, and 2 parameters.
(CVXPY) Mar 04 04:04:10 PM: It is compliant with the following grammars: DCP, DQCP
(CVXPY) Mar 04 04:04:10 PM: CVXPY will first compile your problem; then, it will invoke a numerical solver to obtain a solution.
(CVXPY) Mar 04 04:04:10 PM: Your problem is compiled with the CPP canonicalization backend.
/usr/local/lib/python3.11/dist-packages/cvxpy/reductions/solvers/solving_chain.py:418: UserWarning: The problem has an expression with dimension greater than 2. Defaulting to the SCIPY backend for canonicalization.
  warnings.warn(UserWarning(
-------------------------------------------------------------------------------
                                  Compilation                                  
-------------------------------------------------------------------------------
(CVXPY) Mar 04 04:04:11 PM: Compiling problem (target solver=GLPK_MI).
(CVXPY) Mar 04 04:04:11 PM: Reduction chain: Dcp2Cone -> CvxAttr2Constr -> ConeMatrixStuffing -> GLPK_MI
(CVXPY) Mar 04 04:04:11 PM: Applying reduction Dcp2Cone
(CVXPY) Mar 04 04:04:11 PM: Applying reduction CvxAttr2Constr
(CVXPY) Mar 04 04:04:12 PM: Applying reduction ConeMatrixStuffing
(CVXPY) Mar 04 04:04:15 PM: Applying reduction GLPK_MI
(CVXPY) Mar 04 04:04:16 PM: Finished problem compilation (took 5.144e+00 seconds).
(CVXPY) Mar 04 04:04:16 PM: (Subsequent compilations of this problem, using the same arguments, should take less time.)
-------------------------------------------------------------------------------
                                Numerical solver                               
-------------------------------------------------------------------------------
(CVXPY) Mar 04 04:04:16 PM: Invoking solver GLPK_MI  to obtain a solution.
-------------------------------------------------------------------------------
                                    Summary                                    
-------------------------------------------------------------------------------
(CVXPY) Mar 04 04:04:23 PM: Problem status: optimal
(CVXPY) Mar 04 04:04:23 PM: Optimal value: 3.030e+07
(CVXPY) Mar 04 04:04:23 PM: Compilation took 5.144e+00 seconds
(CVXPY) Mar 04 04:04:23 PM: Solver (including time spent in interface) took 7.448e+00 seconds

MILP Solver Status: optimal
MILP Optimal Total Cost (with penalties): 30303438.11429051