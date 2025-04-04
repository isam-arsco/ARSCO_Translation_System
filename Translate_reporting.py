# import io matplotlib
# pip install fpdf matplotlib
import pandas as pd
import numpy as np
import sqlite3
from collections import Counter
from datetime import datetime
from fpdf import FPDF
import matplotlib.pyplot as plt
import io
import os
import time
from Graph_for_period import *       
from Utils import *
from datetime import date, timedelta

def golobal_outlook(staff_df, chapters_df, events_df, follow_up_df, pdf):
    s16 = 16
    s14 = 14
    s10 = 12
    colors = ["#54bebe", "#808080"]
    pdf.set_text_color(0, 0, 255)
    pdf.add_page()
    pdf.set_font("Helvetica", style="B", size=s16)
    title = "Organization of the encyclopedia"
    pdf.cell(200, 20, txt=title, ln=True)
    pdf.set_font("Helvetica", style="B", size=s12)
    title = "The encyclopedia is composed of the following 6 parts"
    pdf.cell(200, 20, txt=title, ln=True)

    data_labels = ['data', 'data2']
    create_bar_chart(pdf, data1, chart_title, colors, xlabel, ylabel)

    data_sets = [data1, data1]
    # create_bar_chart_mul(pdf, data_sets, chart_title, colors, xlabel, ylabel, data_labels, group_bars=True)

    # (2) Top 12 scores in google_hi from scientists_data
    pdf.add_page()
    pdf.set_font("Helvetica", style="B", size=s16)
    title = "2) Top scientists: based on Google Scholar  H-index"
    pdf.cell(200, 20, txt=title, ln=True)

    query = "SELECT * FROM scientists_data ORDER BY google_hi DESC LIMIT 12"
    df = pd.read_sql_query(query, conn)
    list_id = df[['full_name', 'affiliation', 'google_hi']].values.tolist()
    column_widths2 = [80, 120, 50]
    headers2 = ['Scientist', 'Affiliation', 'G-H-index']
    print_table(pdf, headers2, list_id, column_widths2)
    data2 = []
    for el in list_id:
        data2.append([el[0], el[2]])
    xlabel = 'Google H-index'
    ylabel = 'Scientist'
    create_bar_chart(pdf, data2, title, colors, xlabel, ylabel)

    # (3) Top 10 countries in scientists_data
    pdf.add_page()
    pdf.set_font("Helvetica", style="B", size=s16)
    pdf.cell(200, 15, txt="3) Scientists involved in ARSCO activities: top countries", ln=True)

    cursor.execute("SELECT country FROM scientists_data;")
    countries = [row[0] for row in cursor.fetchall() if row[0]]  # Handle potential NULL values
    country_counts = Counter(countries).most_common(10)
    data3 = []
    for country, count in country_counts:
        data3.append((country, count))
    headers3 = ['Country', 'Number of scientists']
    column_widths3 = [80, 60]
    print_table(pdf, headers3, data3, column_widths3)
    xlabel = 'Number of scientists'
    ylabel = 'Country'
    chart_title = "3) Scientists involved in ARSCO activities: top countries"

    create_bar_chart(pdf, data3, chart_title, colors, xlabel, ylabel)

    # (4) Top ten fulltext_views in ajsr_data
    pdf.add_page()
    pdf.set_font("Helvetica", style="B", size=s16)
    pdf.cell(200, 15, txt="4) AJSR: Top 10 full text views", ln=True)
    pdf.set_font("Helvetica", size=s10)
    cursor.execute("SELECT * FROM ajsr_data ORDER BY fulltext_views DESC LIMIT 10;")
    top_views = cursor.fetchall()
    data4 = []
    data4g = []
    for view in top_views:
        # pdf.cell(200, 10, txt=f"the paper DOI = {view[6]} has {view[11]} views", ln=True)
        data4.append((view[6], view[7][:60], view[11]))
        data4g.append((view[6], view[11]))
    headers4 = ['Paper DOI', 'Paper Title', 'views']
    column_widths4 = [50, 120, 40]
    print_table(pdf, headers4, data4, column_widths4)
    xlabel = 'Number of views'
    ylabel = 'DOI'
    chart_title = "4) AJSR: Top full text views"
    create_bar_chart(pdf, data4g, chart_title, colors, xlabel, ylabel)

    # (5) Top 10 countries in ajsr_data
    pdf.add_page()
    data5 = []
    pdf.set_font("Helvetica", style="B", size=s16)
    title = "5) AJSR: Top countries in the number of papers"
    pdf.cell(200, 15, txt=title, ln=True)
    pdf.set_font("Helvetica", size=s10)
    cursor.execute("SELECT country FROM ajsr_data;")
    countries_ajsr = [row[0] for row in cursor.fetchall() if row[0]]
    country_counts_ajsr = Counter(countries_ajsr).most_common(10)
    for country, count in country_counts_ajsr:
        # pdf.cell(200, 10, txt=f"{count} AJSR papers come from {country}", ln=True)
        data5.append((country, count))
    headers5 = ['Country', 'Contribution to AJSR']
    column_widths5 = [60, 50]
    print_table(pdf, headers5, data5, column_widths5)
    xlabel = 'Number of papers'
    ylabel = 'Country'
    create_bar_chart(pdf, data5, title, colors, xlabel, ylabel)


    # Total sum of citations
    pdf.add_page()
    pdf.set_font("Helvetica", style="B", size=s16)
    pdf.cell(200, 15, txt="6) AJSR: papers citations ", ln=True)
    cursor.execute("SELECT citation FROM ajsr_data;")
    results = cursor.fetchall()
    pdf.set_font("Helvetica", style="B", size=s14)
    sum_of_citations = sum(row[0] for row in results if row[0] is not None)
    pdf.cell(200, 10, txt=f"\n Total sum of citations: {sum_of_citations}", ln=True)
    pdf.ln(10)
    # Top 5 citations in AJSR papers
    pdf.set_font("Helvetica", style="B", size=s14)
    pdf.cell(200, 20, txt="6) AJSR: top 5 papers in the number of citations ", ln=True)

    cursor.execute("SELECT * FROM ajsr_data ORDER BY citation DESC LIMIT 5;")
    top_citations = cursor.fetchall()
    cursor.execute("SELECT name FROM scientists_data")
    names = cursor.fetchall()
    # print(names)
    data6 = []
    for score in top_citations:
        id_s = score[15] - 1
        # print(id_s)
        name = names[id_s][0]
        data6.append((score[4], name, score[8], score[11], score[9][:70]))
    headers6 = ['Year', 'Author1', 'DOI', 'Citations', 'Title']
    column_widths6 = [30, 40, 40, 30, 120]
    print_table(pdf, headers6, data6, column_widths6)

    # Google Analytics
    # (13) Count per month in ga_wp_data
    pdf.add_page()
    pdf.set_font("Helvetica", style="B", size=s16)
    title13 = "13) ARSCO Webpages: Top monthly views"
    pdf.cell(200, 15, txt=title, ln=True)
    pdf.cell(200, 15, txt="Top monthly views", ln=True)
    cursor.execute("SELECT strftime('%Y-%m', web_date) AS month, SUM(web_totalusers), SUM(web_views)"
                   " FROM ga_wp_data GROUP BY month LIMIT 10;")
    months = cursor.fetchall()
    data13 = []
    data13g = []
    for month, users, views in months:
        # pdf.cell(200, 10, txt=f"{month}: number of users =: {users}, with  {views} views", ln=True)
        data13.append((month, users, views))
        data13g.append((month, views))
    headers13 = ['Month/year', 'Users', 'views']
    column_widths13 = [40, 40, 40]
    print_table(pdf, headers13, data13, column_widths13)
    xlabel = 'Number of views'
    ylabel = 'Month/year'
    create_bar_chart(pdf, data13g, title13, colors, xlabel, ylabel)

    # (14) Youtube (ARSCO) YouTube-time
    pdf.add_page()
    pdf.set_font("Helvetica", style="B", size=s16)
    title14 = "14) ARSCO YouTube channel: monthly views"
    pdf.cell(200, 15, txt=title14, ln=True)
    cursor.execute("SELECT strftime('%Y-%m', date) AS month, SUM
