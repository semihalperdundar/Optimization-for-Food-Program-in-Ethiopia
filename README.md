# World Food Programme Supply Chain Optimization

This repository contains optimization models developed for the United Nations **World Food Programme (WFP)** to design an optimal food supply chain for Ethiopia over a **30-day period**. The project applies **Linear Programming (LP)** and **Mixed-Integer Linear Programming (MILP)** techniques using **CVXPY** to determine the best procurement, transportation, and distribution strategies.

## 📂 Project Structure

```
├── Basic_Linear_Programming_Model_Scenario_1.py
├── Basic_Linear_Programming_Model_Scenario_2.py
├── Mixed_Integer_Lineer_Programming_Model.py
├── SupplyChain_LP_Report_Edited.docx
├── Assignment OPT for DS.pptx
├── README.md
```

### 📌 **Files Overview**

- **Basic_Linear_Programming_Model_Scenario_1.py** → LP model for Scenario 1, solving the base case with defined constraints.
- **Basic_Linear_Programming_Model_Scenario_2.py** → LP model for Scenario 2, including variations such as demand increase and port capacity reductions.
- **Mixed_Integer_Lineer_Programming_Model.py** → MILP model, integrating binary decision variables for realistic supplier activations.
- **SupplyChain_LP_Report_Edited.docx** → Project report detailing model formulation, results, and sensitivity analysis.
- **Assignment OPT for DS.pptx** → Presentation outlining the problem, approach, and findings.

## 🎯 Objective

The goal of this project is to **minimize total supply chain costs** while ensuring that all food demand and nutritional requirements are met for Ethiopian beneficiaries. The model takes into account:

- **Procurement decisions**: Selecting suppliers and determining the quantity of food to be purchased.
- **Sea and land transportation**: Optimal routing from suppliers to ports, warehouses, and finally to beneficiary camps.
- **Handling and storage constraints**: Port and warehouse capacities.
- **Nutritional requirements**: Ensuring that distributed food meets the dietary needs of beneficiaries.

## 🛠️ Installation & Setup

To run the optimization models, install the required dependencies:

```bash
pip install cvxpy numpy pandas openpyxl
```

## 🚀 Running the Models

To execute the LP model:
```bash
python Basic_Linear_Programming_Model_Scenario_1.py
```

To execute the MILP model:
```bash
python Mixed_Integer_Lineer_Programming_Model.py
```

## 📊 Results & Sensitivity Analysis

The **SupplyChain_LP_Report_Edited.docx** provides a detailed analysis of different scenarios, including:

- **Base Case**: Standard supply chain optimization under normal conditions.
- **Scenario 1**: Increased demand (+10%) and its impact on costs.
- **Scenario 2**: Reduction of primary port capacity (-50%) and resulting changes in logistics.
- **Scenario 3**: Relaxation of nutritional requirements (90% of baseline) and its cost implications.

## 📌 Key Findings

- **LP Model Cost**: $33,546,944.93 (Base Scenario, fully meeting demand and nutritional needs).
- **MILP Model Cost**: $30,303,438.11 (More practical supplier activation decisions, reducing costs by ~9.7%).
- **Port capacity and procurement constraints** were the most sensitive factors affecting overall costs.
- **Strategic investments in supplier flexibility and port infrastructure** would improve efficiency.

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

