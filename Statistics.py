    # importing 
import streamlit as st
import pandas as pd
import pandasql as ps

    # file import
if "raw_dataset" not in st.session_state:
    st.session_state["raw_dataset"] = pd.read_csv("data-5.csv")
raw_dataset = st.session_state["raw_dataset"]

    # basic function setting
def query(sql):
    return ps.sqldf(sql, globals())

    # navigation button for going to clasification page
left, center, right = st.columns([1, 1, 1])
with center:                            
    st.page_link("pages/1_Fraud_classification.py", label="Input prediction", icon="🔮")  

    # if no "saved_dws" exists in st.cloud, the drop-off-window automatically sets to "amount" and stores it in st.cloud
if "saved_dws" not in st.session_state:
    st.session_state["saved_dws"] = "amount"

    # drop window to chose the most significant patterns
choice = st.menu_button(st.session_state["saved_dws"], options=["amount", "wallet_age_days", "avg_inter_tx_interval_s", "std_inter_tx_interval_s", "kyc_tier"])
    # if the choice is not None then store it in st.cloud and re-run the script
if choice is not None:
    st.session_state["saved_dws"] = choice
    st.rerun()

if st.session_state["saved_dws"] == "kyc_tier":
    work_df = query(f""" 
    SELECT kyc_tier,
    COUNT(*) AS total,
    SUM(fraud) AS fraud_count,
    COUNT(*) - SUM(fraud) AS clean_count,
    ROUND(100.0 * SUM(fraud) / COUNT(*), 2) || '%' AS fraud_rate
    FROM raw_dataset
    GROUP BY kyc_tier;
    """)
    st.dataframe(work_df)

else:

        # window for assigning out_modifier to use it later in calculations
    out_modifier = st.number_input("outlier modifier constant",value=1.5,min_value=0.0)
    st.write(f"Outlier modifier is set to: {out_modifier}")

        # quering for tables where fraud=1, fraud=0, and mixed 
    mix = query(f"""
    SELECT {st.session_state["saved_dws"]}
    FROM raw_dataset;
    """)

    fraud = query(f"""
    SELECT {st.session_state["saved_dws"]}
    FROM raw_dataset
    WHERE fraud = 1;
    """)

    clean = query(f"""
    SELECT {st.session_state["saved_dws"]}
    FROM raw_dataset
    WHERE fraud = 0;
    """)
        # making them a list
    super_list = [fraud, clean, mix]

        # title list for output thourgh cycle
    title = ["### Fraud:", "### Clean:", "### Mixed:"]

        #calculation of stat values thourgh cycle
    mean, amean, q1, q2, q3, iqr, lower_boundary, upper_boundary, mins, maxs, num_outliers_list  = [], [], [], [], [], [], [], [], [], [], []
    for i in range(3):
            # every cycle we are working with different dataset
        work_dataset = super_list[i]

            # mean and absolute mean
        mean.append(work_dataset[st.session_state["saved_dws"]].mean())
        amean.append(work_dataset[st.session_state["saved_dws"]].abs().sum() / work_dataset[st.session_state["saved_dws"]].count())

            # assigning quartiles and mean
        temp_q1, temp_q2, temp_q3 = work_dataset[st.session_state["saved_dws"]].quantile([0.25, 0.5, 0.75])
        q1.append(temp_q1)
        q2.append(temp_q2)
        q3.append(temp_q3)

            # assigning inter quartial range
        temp_iqr = temp_q3 - temp_q1
        iqr.append(temp_iqr)

            # assigning lower and uppe boundaries in accordance to out_modifier
        temp_lower = temp_q1 - out_modifier * temp_iqr
        temp_upper = temp_q3 + out_modifier * temp_iqr
        lower_boundary.append(temp_lower)
        upper_boundary.append(temp_upper)

            # assigning min and max
        mins.append(work_dataset[st.session_state["saved_dws"]].min())
        maxs.append(work_dataset[st.session_state["saved_dws"]].max())

        # assigning amount of outliers
        num_outliers = 0

        for value in work_dataset[st.session_state["saved_dws"]]:
            if value < temp_lower:
                num_outliers += 1
            elif value > temp_upper:
                num_outliers += 1
        num_outliers_list.append(num_outliers)

        # output of the statistical data thourgh cycle
    for i in range(len(title)):
        st.write(title[i])
        left, center, right = st.columns([1, 1, 1])
        with left:
            st.write(f"Mean: {mean[i]:.3f}")
            st.write(f"Abs mean: {amean[i]:.3f}")
            st.write(f"Median: {q2[i]:.3f}")
            
        with center:
            st.write(f"Q1: {q1[i]:.3f}")
            st.write(f"Q3: {q3[i]:.3f}")
            st.write(f"IQR: {iqr[i]:.3f}")
        with right:
            st.write(f"Min: {mins[i]}")
            st.write(f"Max: {maxs[i]}")

        st.write(f"Outlier are not between {lower_boundary[i]:.1f} and {upper_boundary[i]:.1f} and there are {num_outliers_list[i]} outliers")
