# World Food Programme Supply Chain Optimization

This repository contains optimization models developed for the United Nations **World Food Programme (WFP)** to design an optimal food supply chain for Ethiopia over a **30-day period**. The project applies **Linear Programming (LP)** and **Mixed-Integer Linear Programming (MILP)** techniques using **CVXPY** to determine the best procurement, transportation, and distribution strategies.

## 📂 Project Structure

```
├── Basic_Linear_Programming_Model_Scenario_1.py
├── Basic_Linear_Programming_Model_Scenario_2.py
├── Mixed_Integer_Lineer_Programming_Model.py
├── README.md
```

### 📌 **Files Overview**

- **Basic_Linear_Programming_Model_Scenario_1.py** → LP model for Scenario 1, solving the base case with defined constraints.
- **Basic_Linear_Programming_Model_Scenario_2.py** → LP model for Scenario 2, including variations such as demand increase and port capacity reductions.
- **Mixed_Integer_Lineer_Programming_Model.py** → MILP model, integrating binary decision variables for realistic supplier activations.
- **SupplyChain_LP_Report_Edited.docx** → Project report detailing model formulation, results, and sensitivity analysis.
- **Assignment OPT for DS.pptx** → Presentation outlining the problem, approach, and findings.

## 🎯 Objective

The goal of this project is to **minimize total supply chain costs** while ensuring that all food demand and nutritional requirements are met for Ethiopian beneficiaries. The model incorporates:

- **Procurement planning**: Optimal allocation from multiple suppliers
- **Transportation logistics**: Cost-effective sea and land routing
- **Warehouse and port capacities**: Operational constraints
- **Nutritional targets**: Satisfying dietary requirements for all camps
- **Scenario analysis**: Testing model robustness under real-world uncertainties

## 🔬 Methodology

- **Linear Programming (LP)**: Used to model base scenarios with continuous decision variables.
- **Mixed Integer Linear Programming (MILP)**: Introduced binary variables for on/off supplier decisions.
- **Scenario Simulation**: Modeled supply chain under altered demand, capacity restrictions, and dietary relaxation.
- **Solver**: All models executed in Python using **CVXPY**.

## ⚙️ Constraint Types

The models incorporate the following key constraints:

- **Supplier Capacity Constraints**: Total dispatched commodities must not exceed supplier capacity.
- **Port Capacity Constraints**: Each port has a maximum intake capacity.
- **Warehouse Capacity & Balance**: Warehouses must maintain material balance and not exceed storage limits.
- **Port Balance**: Flow into each port equals flow out to warehouses.
- **Camp Demand Constraints**: Each camp must receive sufficient food for its population (e.g., 300g/day/person).
- **Nutritional Constraints**: Fulfillment of daily nutrient requirements (protein, energy, etc.) across 30 days.
- **Route Availability Constraints**: Shipments are only allowed along defined sea and land transport routes.
- **Non-negativity & Integer Constraints**: All flows must be non-negative; integer enforcement in MILP model.

## 🛠️ Installation & Setup

Install required libraries:
```bash
pip install cvxpy numpy pandas openpyxl
```

## 🚀 Running the Notebooks
Each `.ipynb` file can be opened and executed in **Jupyter Notebook** or **Google Colab**. Follow the structure:
1. **LP model**: `Opt for DS LP Version IV.ipynb`
2. **MILP model**: `Opt for DS MILP Version IV.ipynb`
3. **Scenario analysis**: `Opt for DS Scenarios Version IV.ipynb`

Ensure all cells are run sequentially and required libraries are installed.

## 📊 Results & Sensitivity Analysis

- **Base LP Model Cost**: ~$99.0M (fully satisfies demand and nutrition)
- **MILP Model Cost**: ~$25.4M (more realistic constraints, lower cost)
- **Scenario Simulations**:
  - +10% Demand → Cost increases significantly
  - -50% Port Capacity → Transport cost reallocation
  - Relaxed Nutrition → Minor cost improvement

## 🔍 Key Insights
- LP model gives feasible, interpretable baseline solution.
- MILP introduces practical restrictions like supplier enablement.
- Scenario stress tests highlight sensitivity to port constraints and supplier flexibility.
- Strategic investments in **alternative ports** and **supplier diversification** improve robustness.


## 🔍 Recommendations

- Expand **supplier procurement capacities** to lower shadow price bottlenecks.
- Increase **port handling capacities** to reduce transport inefficiencies.
- Optimize **port-to-warehouse connections** for better food distribution.
- Introduce **alternative supply routes** for resilience against disruptions.

## 👨‍💻 Authors
- **Semih Alper Dundar**
- **Doga Okumus**   

## 📝 License
This project is released under the **MIT License**.

---

This repository supports research at **Zero Hunger Lab**, aiming to enhance food security through data-driven decision-making. 🌍🍲

