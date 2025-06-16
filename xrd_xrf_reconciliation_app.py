import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="XRD/XRF Reconciliation App", layout="wide")

st.title("\U0001F52C XRD to XRF Reconciliation Dashboard")
st.markdown("Upload your XRD and XRF Excel files below. The app will convert mineral percentages to elemental/oxide contributions using the reference library.")

# Upload inputs
xrd_file = st.file_uploader("Upload XRD Data File", type=["xlsx"])
xrf_file = st.file_uploader("Upload XRF Data File", type=["xlsx"])
lib_file = st.file_uploader("Upload Mineral Library Reference", type=["xlsx"])

if xrd_file and xrf_file and lib_file:
    try:
        # Load data
        xrd_df = pd.read_excel(xrd_file)
        xrf_df = pd.read_excel(xrf_file)
        lib_df = pd.read_excel(lib_file)

        st.success("Files uploaded and loaded successfully!")

        # Unpivot XRD data
        xrd_long = xrd_df.melt(id_vars=["Sample ID"], var_name="Mineral Name", value_name="Mineral %")

        # Merge with mineral library
        merged = pd.merge(xrd_long, lib_df, on="Mineral Name", how="left")

        # Calculate Element %
        merged["Calculated Element %"] = merged["Mineral %"] * merged["Weight %"] / 100

        # Aggregate by sample and element/oxide
        summary = merged.groupby(["Sample ID", "Element or Oxide", "Component Type"], as_index=False)["Calculated Element %"].sum()

        # Merge with XRF for comparison
        comparison = pd.merge(summary, xrf_df, on=["Sample ID", "Element or Oxide"], how="outer")
        comparison.rename(columns={"Detected %": "XRF Detected %"}, inplace=True)

        # Calculate difference
        comparison["Difference %"] = comparison["Calculated Element %"] - comparison["XRF Detected %"]

        st.subheader("Comparison Table")
        st.dataframe(comparison)

        # Export
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            comparison.to_excel(writer, index=False, sheet_name='Reconciliation')
        st.download_button(label="Download Reconciliation Report (Excel)",
                           data=output.getvalue(),
                           file_name="Reconciliation_Report.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        st.error(f"Error processing files: {e}")

else:
    st.info("Please upload all three files to proceed.")
