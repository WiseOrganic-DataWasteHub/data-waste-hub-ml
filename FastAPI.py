from fastapi import FastAPI, Query, Response
import requests
import io
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np

plt.switch_backend('Agg')
app = FastAPI()

# -------------------------- FUNGSI UTAMA --------------------------------

# Fungsi untuk mendapatkan token
def get_token():
    url = "https://data-waste-hub-api-688382515205.asia-southeast2.run.app/api/v1/auth/login"
    data = {"username": "admin", "password": "admin123"}
    response = requests.post(url, json=data)
    
    #print("Response Login:", response.status_code, response.text)

    if response.status_code == 200:
        response_json = response.json()
        if response_json.get("success"):
            return response_json["data"]["token"]
        else:
            raise Exception(f"Login failed: {response_json.get('message')}")
    else:
        raise Exception(f"Failed to get token. Status Code: {response.status_code}, Response: {response.text}")

# Fungsi untuk mengambil data dari API (fleksibel: hari+bulan+tahun, bulan+tahun, atau hanya tahun)
def fetch_data_with_token(day: int = None, month: int = None, year: int = None):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    # URL API berdasarkan parameter
    if day is not None and month is not None and year is not None:
        url = f"https://data-waste-hub-api-688382515205.asia-southeast2.run.app/api/v1/waste-records/day/{day}/month/{month}/year/{year}"
    elif month is not None and year is not None:
        url = f"https://data-waste-hub-api-688382515205.asia-southeast2.run.app/api/v1/waste-records/month/{month}/year/{year}"
    elif year is not None:
        url = f"https://data-waste-hub-api-688382515205.asia-southeast2.run.app/api/v1/waste-records/year/{year}"
    else:
        raise Exception("Invalid parameters: Please specify year, or month and year, or day, month, and year.")

    #print(f"Fetching data from URL: {url}")
    response = requests.get(url, headers=headers)
    # print(f"Response Code: {response.status_code}")
    # print(f"Response Body: {response.text}")

    if response.status_code == 200:
        data = response.json()["data"]
        if len(data) == 0:
            raise Exception("No data available for the specified parameters.")
        return data
    else:
        raise Exception(f"Failed to fetch data. Status Code: {response.status_code}, Response: {response.text}")


# -------------------------- ENDPOINTS -----------------------------------

# Endpoint untuk mengambil data
@app.get("/fetch-data/")
def fetch_data(day: int = Query(None), month: int = Query(None), year: int = Query(...)):
    try:
        data = fetch_data_with_token(day=day, month=month, year=year)

        # Debug: Cetak data mentah
        #print("Data Mentah:", data)

        return {"success": True, "raw_data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Endpoint untuk visualisasi bar chart
@app.get("/visualize-bar-chart/")
def visualize_bar_chart(day: int = Query(None), month: int = Query(None), year: int = Query(...)):
    try:
        data = fetch_data_with_token(day=day, month=month, year=year)
        cleaned_data = [
            {
                "departement_name": item["departement"]["departement_name"],
                "total_weight":  round(item["total_weight"], 2)
            }
            for item in data if item["departement"] is not None
        ]

        #print("Data Dibersihkan:", cleaned_data)
        df = pd.DataFrame(cleaned_data)

        all_departments = ["Front Office", "Accounting", "HRD", "Spa", "Security", "Kitchen", "Restaurant and Bar", "Garden"]
        df = df.set_index("departement_name").reindex(all_departments, fill_value=0).reset_index()

        max_weight = df["total_weight"].max()
        y_max = max_weight + 10 

        plt.figure(figsize=(14, 6))
        sns.barplot(
            data=df,
            x="departement_name",
            y="total_weight",
            palette="cubehelix",
            edgecolor="black"
        )

        title = f"Total Berat Sampah per Departemen"
        if day is not None and month is not None:
            title += f" ({day}/{month}/{year})"
        elif month is not None:
            title += f" ({month}/{year})"
        else:
            title += f" (Tahun {year})"

        plt.title(title, fontsize=18, weight='bold', color='darkblue', pad=20)  
        plt.xlabel("Departemen", fontsize=14, weight='bold')
        plt.ylabel("Berat Sampah (kg)", fontsize=14, weight='bold')
        plt.xticks(rotation=45, fontsize=12, ha='right', weight='bold')
        plt.yticks(fontsize=12, weight='bold')
        plt.ylim(0, y_max)

        for index, row in df.iterrows():
            if row["total_weight"] > 0: 
                plt.text(index, row["total_weight"] + 2, f"{row['total_weight']} kg", ha='center', fontsize=10, color='black', weight='bold')

        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()

        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        return {"success": False, "error": str(e)}

# Endpoint untuk visualisasi pie chart
@app.get("/visualize-pie-chart/")
def visualize_pie_chart(day: int = Query(None), month: int = Query(None), year: int = Query(...)):
    try:
        data = fetch_data_with_token(day=day, month=month, year=year)
        cleaned_data = [
            {
                "departement_name": item["departement"]["departement_name"],
                "total_weight": round(item["total_weight"], 2)
            }
            for item in data if item["departement"] is not None
        ]
        df = pd.DataFrame(cleaned_data)
        labels = df["departement_name"]
        sizes = df["total_weight"]
        percentages = [f"{size / sizes.sum() * 100:.1f}%" for size in sizes]
        plt.figure(figsize=(14, 8))
        wedges, texts = plt.pie(
            sizes,
            startangle=140,
            colors=plt.cm.Set3.colors,
            wedgeprops={'edgecolor': 'black'},
        )
        for i, wedge in enumerate(wedges):
            angle = (wedge.theta2 - wedge.theta1) / 2 + wedge.theta1
            x = np.cos(np.radians(angle))
            y = np.sin(np.radians(angle))
            plt.annotate(
                labels[i],
                xy=(x, y),
                xytext=(x * 1.3, y * 1.1),
                ha='center',
                va='center',
                fontsize=10,
                weight='bold',
                arrowprops=dict(arrowstyle="-", color="black")
            )

        legend_labels = [
            f"{label} ({size} kg) ({percentage})"
            for label, size, percentage in zip(labels, sizes, percentages)
        ]
        plt.legend(
            wedges,
            legend_labels,
            title="Departemen, Total Berat (kg), dan Persentase",
            loc="upper left",
            bbox_to_anchor=(1.05, 0.3),
            fontsize=10,
            ncol=1
        )
        
        title = f"Distribusi Sampah per Departemen"
        if day is not None and month is not None:
            title += f" ({day}/{month}/{year})"
        elif month is not None:
            title += f" ({month}/{year})"
        else:
            title += f" (Tahun {year})"
        
        plt.title(title, fontsize=16, weight='bold')
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        return {"success": False, "error": str(e)}
    
# Endpoint untuk visualisasi pie chart kategori
@app.get("/visualize-pie-chart-categories/")
def visualize_pie_chart_categories(day: int = Query(None), month: int = Query(None), year: int = Query(...)):
    try:
        data = fetch_data_with_token(day=day, month=month, year=year)

        if not isinstance(data, list):
            raise Exception(f"Invalid data format: Expected a list, got {type(data)._name_}")

        categories_data = []
        for idx, item in enumerate(data):
            #print(f"Item ke-{idx}: Tipe = {type(item)}, Isi = {item}")
            if not isinstance(item, dict):
                # print(f"Item ke-{idx} tidak valid (bukan dict):", item)
                continue

            categories = item.get("categories")
            if not isinstance(categories, list):
                #print(f"Item ke-{idx} memiliki categories tidak valid (bukan list):", categories)
                continue

            for cat_idx, category in enumerate(categories):
                #print(f"Kategori ke-{cat_idx} di item ke-{idx}: Tipe = {type(category)}, Isi = {category}")

                if not isinstance(category, dict):
                    #print(f"Kategori ke-{cat_idx} di item ke-{idx} tidak valid (bukan dict):", category)
                    continue

                category_obj = category.get("category")
                if not isinstance(category_obj, dict):
                    #print(f"Kategori objek ke-{cat_idx} di item ke-{idx} tidak valid (bukan dict):", category_obj)
                    continue
                categories_data.append({
                    "category_name": category_obj.get("category_name", "Unknown"),
                    "total_weight": category.get("total_weight", 0)
                })

        #print("Data kategori yang berhasil dikumpulkan:", categories_data)

        if not categories_data:
            raise Exception("No valid category data available for the specified parameters.")

        df = pd.DataFrame(categories_data)
        grouped_df = df.groupby("category_name")["total_weight"].sum().reset_index()
        grouped_df["total_weight"] = grouped_df["total_weight"].apply(lambda x: round(x, 2)) 
        labels = grouped_df["category_name"]
        sizes = grouped_df["total_weight"]
        percentages = [f"{size / sizes.sum() * 100:.1f}%" for size in sizes]

        plt.figure(figsize=(16, 8))
        wedges, texts = plt.pie(
            sizes,
            startangle=140,
            colors=plt.cm.Set3.colors,
            wedgeprops={'edgecolor': 'black'},
        )
        for i, wedge in enumerate(wedges):
            angle = (wedge.theta2 - wedge.theta1) / 2 + wedge.theta1
            x = np.cos(np.radians(angle))
            y = np.sin(np.radians(angle))
            plt.annotate(
                labels[i],
                xy=(x, y),
                xytext=(x * 1.3, y * 1.1),
                ha='center',
                va='center',
                fontsize=10,
                weight='bold',
                arrowprops=dict(arrowstyle="-", color="black")
            )

        legend_labels = [
            f"{label} ({weight} kg) ({percentage})"
            for label, weight, percentage in zip(labels, sizes, percentages)
        ]
        plt.legend(
            wedges,
            legend_labels,
            title="Jenis Sampah, Total Berat, dan Persentase",
            loc="center left",
            bbox_to_anchor=(1.15, 0.3),
            fontsize=10,
            ncol=1
        )

        title = f"Distribusi Jenis Sampah"
        if day is not None and month is not None:
            title += f" ({day}/{month}/{year})"
        elif month is not None:
            title += f" ({month}/{year})"
        else:
            title += f" (Tahun {year})"

        plt.title(title, fontsize=16, weight='bold')
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()

        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        # print("Error:", e)
        return {"success": False, "error": str(e)}
    
# Endpoint untuk visualisasi pie chart kesimpulan
@app.get("/visualize-pie-chart-summary/")
def visualize_pie_chart_summary(day: int = Query(None), month: int = Query(None), year: int = Query(...)):
    try:
        data = fetch_data_with_token(day=day, month=month, year=year)

        category_mapping = {
            "Organik": ["WET ORGANIK", "WET ORGANIC"],
            "Non-Organik": ["PET", "ALUMINIUM CAN", "TETRA PACK", "GLASS BOTTLE"],
            "Residue": ["GENERAL PLASTIC RESIDUE", "GENERAL PAPER RESIDUE",
                        "PLASTIK BAG LINER", "CANDLES", "SLIPPERS"]
        }

        summary_data = {"Organik": 0, "Non-Organik": 0, "Residue": 0}

        for item in data:
            for category in item.get("categories", []):
                category_obj = category.get("category", {})
                if not category_obj:
                    continue
                category_name = category_obj.get("category_name", "").upper()
                total_weight = category.get("total_weight", 0)

                if category_name in category_mapping["Organik"]:
                    summary_data["Organik"] += total_weight
                elif category_name in category_mapping["Non-Organik"]:
                    summary_data["Non-Organik"] += total_weight
                elif category_name in category_mapping["Residue"]:
                    summary_data["Residue"] += total_weight

        if sum(summary_data.values()) == 0:
            raise Exception("No data available for the specified parameters.")

        for category, weight in summary_data.items():
            summary_data[category] = round(weight, 2) 

        df_summary = pd.DataFrame(
            {"Category": list(summary_data.keys()), "Total Weight": list(summary_data.values())}
        )
        sizes = df_summary["Total Weight"]
        labels = df_summary["Category"]
        percentages = [f"{size / sizes.sum() * 100:.1f}%" for size in sizes]

        plt.figure(figsize=(14, 8))
        wedges, texts, autotexts = plt.pie(
            sizes,
            startangle=140,
            colors=plt.cm.Paired.colors,
            wedgeprops={'edgecolor': 'black'},
            autopct=lambda p: f"{p:.1f}%" if p > 0 else "",  
            textprops={'fontsize': 12, 'weight': 'bold'}  
        )

        for i, wedge in enumerate(wedges):
            angle = (wedge.theta2 - wedge.theta1) / 2 + wedge.theta1
            x = np.cos(np.radians(angle))
            y = np.sin(np.radians(angle))
            plt.annotate(
                labels[i],
                xy=(x, y),
                xytext=(x * 1.2, y * 1.2),
                ha='center',
                va='center',
                fontsize=12,
                weight='bold',
                arrowprops=dict(arrowstyle="-", color="black")
            )

        legend_labels = [
            f"{label} ({weight} kg) ({percentage})"
            for label, weight, percentage in zip(labels, sizes, percentages)
        ]
        plt.legend(
            wedges,
            legend_labels,
            title="Kelompok Sampah, Total Berat, dan Persentase",
            loc="center left",
            bbox_to_anchor=(1, 0.3),
            fontsize=10,
            ncol=1
        )

        title = "Distribusi Sampah (Summary)"
        if day is not None and month is not None:
            title += f" ({day}/{month}/{year})"
        elif month is not None:
            title += f" ({month}/{year})"
        else:
            title += f" (Tahun {year})"

        plt.title(title, fontsize=16, weight='bold')
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()

        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        return {"success": False, "error": str(e)}

# Endpoint untuk visualisasi pie chart berdasarkan departemen
@app.get("/visualize-departement-pie-chart/")
def visualize_departement_pie_chart(
    departement_id: int = Query(...),
    day: int = Query(None),
    month: int = Query(None),
    year: int = Query(...)
):
    try:
        data = fetch_data_with_token(day=day, month=month, year=year)

        filtered_data = [item for item in data if item.get("departement_id") == departement_id]
        if not filtered_data:
            raise Exception(f"No data available for departement ID {departement_id}")

        departement_name = filtered_data[0].get("departement", {}).get("departement_name", f"ID {departement_id}")

        categories_data = []
        for item in filtered_data:
            for category in item.get("categories", []):
                if category.get("category"):
                    categories_data.append({
                        "category_name": category["category"]["category_name"],
                        "total_weight": round(category["total_weight"], 2)
                    })

        if not categories_data:
            raise Exception(f"No category data available for departement ID {departement_id}")

        df = pd.DataFrame(categories_data)
        grouped_df = df.groupby("category_name")["total_weight"].sum().reset_index()
        labels = grouped_df["category_name"]
        sizes = grouped_df["total_weight"]

        plt.figure(figsize=(16, 8))
        wedges, texts = plt.pie(
            sizes,
            labels=None,  
            startangle=140,
            colors=plt.cm.Set3.colors,
            wedgeprops={'edgecolor': 'black'},
        )

        for i, wedge in enumerate(wedges):
            angle = (wedge.theta2 - wedge.theta1) / 2 + wedge.theta1
            x = np.cos(np.radians(angle))
            y = np.sin(np.radians(angle))

            plt.annotate(
                labels[i],
                xy=(x, y),
                xytext=(x * 1.3, y * 1.1),  
                ha='center',
                va='center',
                fontsize=12,
                weight='bold',
                arrowprops=dict(arrowstyle="-", color="black")
            )

        legend_labels = [
            f"{label} ({weight} kg)  ({round(weight / sizes.sum() * 100, 1)}%)"
            for label, weight in zip(labels, sizes)
        ]
        plt.legend(
            wedges,
            legend_labels,
            title="Jenis Sampah, Berat, & Persentase",
            loc="center left",
            bbox_to_anchor=(1.15, 0.3),
            fontsize=10,
            ncol=1
        )

        title = f"Distribusi Jenis Sampah di Departemen {departement_name}"
        if day is not None and month is not None:
            title += f" ({day}/{month}/{year})"
        elif month is not None:
            title += f" ({month}/{year})"
        else:
            title += f" (Tahun {year})"

        plt.title(title, fontsize=16, weight='bold')
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()

        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        return {"success": False, "error": str(e)}
