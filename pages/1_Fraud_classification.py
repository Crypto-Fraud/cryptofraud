import streamlit as st
import pandas as pd
import pandasql as ps
from joblib import load
import sqlite3
from sklearn.model_selection import train_test_split


# load the model and the scaler we saved in Project.ipynb (trained on the 9 columns)
# before there was nothing here, the app didnt use the model at all, it just showed the columns
model = load("knn_model.joblib")
scaler = load("scaler.joblib")


#cleaning the dataset

if "raw_dataset" not in st.session_state:
    st.session_state["raw_dataset"] = pd.read_csv("data-5.csv")
df = dataset = st.session_state["raw_dataset"]


cleaned = dataset[["amount", "wallet_age_days", "avg_inter_tx_interval_s", "std_inter_tx_interval_s",
                            "kyc_tier", "fraud"]]




# here we are selecting the three nearest neigbours
# this has to be here at the top because df is still the full dataset here (inside the if it becomes the typed in row)
# same split as when the model was trained (train_size=0.8, random_state=52)
train_rows, _ = train_test_split(df, train_size=0.8, random_state=52)
train_rows = train_rows.reset_index(drop=True)

df = train_rows

def nearest_transactions(X_scaled, k=3):
     # returns the k past transactions closest to the new one, with their distance
     distances, positions = model.kneighbors(X_scaled, n_neighbors=k)
     nearest = train_rows.iloc[positions[0]].copy()
     nearest.insert(0, "distance", distances[0].round(3))
     return nearest



#frotend

st.subheader("MANDATORY")

col1,col2,col3  = st.columns(3,vertical_alignment="bottom")

with col1:
     amount = st.number_input("Amount (USD)",min_value=0.0,value=None)
     st.write("You entered:", amount)

with col2:
     wallet_age_days = st.number_input("Age of wallet",min_value=0,step=1,value=None)
     st.write("You entered:", wallet_age_days)

with col3:
     avg_inter_tx_interval_s = st.number_input("Seconds between the wallet's transactions",min_value=0,step=1,value=None) 
     st.write("You entered:", avg_inter_tx_interval_s)

c1,c2 = st.columns(2,vertical_alignment="bottom")

with c1:
     std_inter_tx_interval_s = st.number_input("Standard deviation of that interval",min_value=0,step=1,value=None)
     st.write("You entered:",  std_inter_tx_interval_s)

with c2:
     kyc_tier = st.selectbox("Account verification stage", ["unverified","basic","full"],index=None)
     st.write("You entered:", kyc_tier)

st.subheader("OPTIONAL")

op1,op2,op3  = st.columns(3,vertical_alignment="bottom")

with op1:
     tx_hour  = st.number_input("Hour of day (0-23)",min_value=0,max_value=23,step=1,value=None)
     st.write("You entered:", tx_hour )
     if tx_hour is None:
          tx_hour= df["tx_hour"].mean()

with op2:
     input_count = st.number_input("Number of inputs funding the transaction",min_value=1,step=1,value=None)
     st.write("You entered:",input_count)
     if input_count is None:
          input_count = df["input_count"].mean()

with op3:
     output_count = st.number_input("Number of outputs",min_value=1,step=1,value=None)
     st.write("You entered:", output_count)
     if output_count is None:
          output_count = df["output_count"].mean()
     
c1,c2,c3 = st.columns(3,vertical_alignment="bottom")

with c1:
     tx_count_24h = st.number_input("Wallet's transactions in the last 24h",min_value=0,step=1,value=None)
     st.write("You entered:", tx_count_24h)
     if tx_count_24h is None:
          tx_count_24h = df["tx_count_24h"].mean()


with c2:
     unique_counterparties_24h = st.number_input("Different wallets touched in the last 24h",min_value=0,step=1,value=None)
     st.write("You entered:", unique_counterparties_24h)
     if unique_counterparties_24h is None:
          unique_counterparties_24h = df["unique_counterparties_24h"].mean()
 
with c3:
     max_graph_hop = st.number_input("Hop distance of the deepest recipient",min_value=1,step=1,value=None)
     st.write("You entered:", max_graph_hop)
     if max_graph_hop is None:
          max_graph_hop = df["max_graph_hop"].mean()

cl1,cl2,cl3 = st.columns(3,vertical_alignment="bottom")

with cl1:
     gas_price_pctile = st.number_input("Fee urgency percentile",min_value=0,max_value=100,step=1,value=None)
     st.write("You entered:", gas_price_pctile)
     if gas_price_pctile is None:
          gas_price_pctile = df["gas_price_pctile"].mean()

with cl2:
     weekend= st.radio("Weekend (Saturday or Sunday)",["Yes","No"],
     index=None,
     horizontal=True)

     if weekend=="Yes":
          is_weekend=1
     elif weekend=="No":
          is_weekend=0
     else:
          is_weekend=None
     st.write("You entered:",is_weekend)
     
 
with cl3:
     time_since_prev_tx_s = st.number_input("Seconds since the wallet's previous transaction",min_value=0,step=1,value=None)
     st.write("You entered:", time_since_prev_tx_s)
     if time_since_prev_tx_s is None:
          time_since_prev_tx_s = df["time_since_prev_tx_s"].mean()


cll1,cll2= st.columns(2,vertical_alignment="bottom")

with cll1:
     balance_change= st.number_input("Net change for the sender",value=None)
     st.write("You entered:", balance_change)
     if balance_change is None:
               balance_change = df["balance_change"].mean()
     
with cll2:
     new_address_fraction = st.number_input("New address share",min_value=0.000,max_value=1.000,step=0.001,format="%.3f",value=None)
     st.write("You entered:", new_address_fraction)
     if new_address_fraction is None:
                    new_address_fraction = df["new_address_fraction"].mean()



     #backend

if st.button("Submit", type="primary", width="stretch"):

     mandatory=[amount, wallet_age_days, avg_inter_tx_interval_s, std_inter_tx_interval_s, balance_change, new_address_fraction, kyc_tier]
     if None in mandatory:
          st.error("All mandatory fields need to be filled")
          st.stop()
     st.session_state["transaction"] ={
          "amount": amount,
          "wallet_age_days": wallet_age_days,
          "avg_inter_tx_interval_s": avg_inter_tx_interval_s,
          "std_inter_tx_interval_s":std_inter_tx_interval_s,
          "balance_change":balance_change,
          "new_address_fraction":new_address_fraction,
          "kyc_tier":kyc_tier,
          "tx_hour":tx_hour,
          "input_count":input_count,
          "output_count":output_count,
          "tx_count_24h":tx_count_24h,
          "unique_counterparties_24h":unique_counterparties_24h,
          "max_graph_hop":max_graph_hop,
          "gas_price_pctile":gas_price_pctile,
          "is_weekend":is_weekend,
          "time_since_prev_tx_s":time_since_prev_tx_s,
          }

     

     df = pd.DataFrame([{
          "amount": amount, "tx_hour": tx_hour, "input_count": input_count, "output_count": output_count,
          "wallet_age_days": wallet_age_days, "tx_count_24h": tx_count_24h,
          "unique_counterparties_24h": unique_counterparties_24h,
          "avg_inter_tx_interval_s": avg_inter_tx_interval_s, "std_inter_tx_interval_s": std_inter_tx_interval_s,
          "balance_change": balance_change, "new_address_fraction": new_address_fraction,
          "max_graph_hop": max_graph_hop, "time_since_prev_tx_s": time_since_prev_tx_s,
          "gas_price_pctile": gas_price_pctile, "is_weekend": is_weekend, "kyc_tier": kyc_tier,
     }])

     conn = sqlite3.connect(":memory:")
     df.to_sql("data", conn, index=False)

     useful_columns = [
          "amount",
          "wallet_age_days",
          "avg_inter_tx_interval_s",
          "std_inter_tx_interval_s",
          "kyc_tier"
     ]

     query = f"SELECT {', '.join(useful_columns)} FROM data"

     result = pd.read_sql_query(query, conn)

     st.dataframe(result) # displays the dataframe in the streamlit app

     conn.close()

     X_new = pd.get_dummies(df, columns=["kyc_tier"], dtype=int)

     X_new = X_new.reindex(columns=scaler.feature_names_in_, fill_value=0) ## here we ae saying that if the user inputs one strign the mdoel
     #doesnt knwo the other ctegories what to do when encoding so it need to fil them with values 0

     X_new_scaled = scaler.transform(X_new)

     score = model.predict(X_new_scaled)  # it gives 0 or 1

     if score > 0:   #fraud = 1
          st.error("fraud")
     else:
          st.success("not fraud")

     st.subheader("3 most similar past transactions")
     st.dataframe(nearest_transactions(X_new_scaled, k=3), hide_index=True)



#     st.session_state["raw_dataset"] = pd.read_csv("csvs/data-5.csv") # uploading
# raw_dataset = st.session_state["raw_dataset"] # downloading