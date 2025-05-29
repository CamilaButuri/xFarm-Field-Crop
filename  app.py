import streamlit as st
import pandas as pd
import requests
import json
import time

st.set_page_config(page_title="xFarm Field & Crop Mapper")

st.title("🌾 xFarm - Field & Crop Mapper")
st.markdown("Carica il tuo Excel con `username`, `password`, `companyId` e scarica i risultati.")

uploaded_file = st.file_uploader("Carica il file Excel", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    output_data = []

    LOGIN_URL = "https://api-prod.xfarm.ag/api/public/v1/auth/login"
    FIELDS_URL = "https://api-prod.xfarm.ag/api/private/v1/fields/?companyIds={companyId}&multiFarm=true&lang=it"
    CROPS_URL = "https://api-prod.xfarm.ag/api/private/v1/crops?field={fieldId}&companyIds={companyId}&multiFarm=true&lang=it"

    def get_token(username, password):
        response = requests.post(
            LOGIN_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps({"username": username, "password": password}),
        )
        return response.json().get("access_token") if response.status_code == 200 else None

    def get_fields(token, company_id):
        url = FIELDS_URL.format(companyId=company_id)
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(url, headers=headers)
        return res.json() if res.status_code == 200 else []

    def get_crops(token, company_id, field_id):
        url = CROPS_URL.format(fieldId=field_id, companyId=company_id)
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(url, headers=headers)
        return res.json() if res.status_code == 200 else []

    with st.spinner("Elaborazione in corso..."):
        for _, row in df.iterrows():
            username = row["username"]
            password = row["password"]
            company_id = row["companyId"]
            token = get_token(username, password)
            if not token:
                continue
            fields = get_fields(token, company_id)
            for field in fields:
                field_id = field.get("id")
                field_name = field.get("name")
                field_size = field.get("size")
                group_name = field.get("group", {}).get("name")
                crops = get_crops(token, company_id, field_id)
                if crops:
                    for crop in crops:
                        commodity = crop.get("commodity")
                        if isinstance(commodity, dict):
                            commodity_id = commodity.get("id")
                            commodity_name = commodity.get("name")
                        else:
                            commodity_id = commodity
                            commodity_name = None
                        output_data.append({
                            "username": username,
                            "companyId": company_id,
                            "fieldId": field_id,
                            "fieldName": field_name,
                            "fieldSize": field_size,
                            "groupName": group_name,
                            "cropId": crop.get("id"),
                            "cropYear": crop.get("year"),
                            "cropCommodityId": commodity_id,
                            "cropCommodityName": commodity_name,
                            "cropSize": crop.get("size"),
                            "supplyChainDestination": crop.get("supplyChainDestination")
                        })
                else:
                    output_data.append({
                        "username": username,
                        "companyId": company_id,
                        "fieldId": field_id,
                        "fieldName": field_name,
                        "fieldSize": field_size,
                        "groupName": group_name,
                        "cropId": None,
                        "cropYear": None,
                        "cropCommodityId": None,
                        "cropCommodityName": None,
                        "cropSize": None,
                        "supplyChainDestination": None
                    })
                time.sleep(0.2)

        output_df = pd.DataFrame(output_data)
        st.success("✅ Elaborazione completata!")
        st.dataframe(output_df)

        # Download link
        st.download_button(
            label="📥 Scarica Excel",
            data=output_df.to_excel(index=False, engine="openpyxl"),
            file_name="field_crop_mapping.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
