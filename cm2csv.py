#!/usr/bin/env python3

import pdfplumber
import csv
import os
from datetime import datetime
import click


# Function to read tables from a PDF file
def read_pdf_tables(p_pdf_path):
    tables = []
    with pdfplumber.open(p_pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table is None:
                continue  # Skip this page if no table is found
            for i in range(len(table)):
                for j in range(len(table[i])):
                    if table[i][j] is not None:
                        table[i][j] = table[i][j].replace(".", "")
            tables.extend(table)
    return tables


# Function to filter rows that contain any string from a list of strings
def filter_rows(p_data, p_filter_strings):
    return [
        row
        for row in p_data
        if all(
            all(filter_string not in cell for filter_string in p_filter_strings)
            for cell in row
            if cell is not None
        )
    ]


# Function to remove the first column from the table
def remove_first_column(p_data):
    return [row[1:] for row in p_data]


# Function to stitch rows with empty first columns to their previous rows
def stitch_rows(p_data):
    stitched_data = []
    previous_row = []
    for row in p_data:
        if row[0] is None or row[0].strip() == "":
            if previous_row:
                stitched_row = [
                    str(prev_cell or "") + str(curr_cell or "")
                    for prev_cell, curr_cell in zip(previous_row, row)
                ]
                previous_row = stitched_row
        else:
            if previous_row:
                stitched_data.append(previous_row)
            previous_row = row
    if previous_row:
        stitched_data.append(previous_row)
    return stitched_data


# Function to sort rows by date
def sort_by_date(p_data):
    return sorted(
        p_data,
        key=lambda row: datetime.strptime(row[0], "%d/%m/%Y")
        if row[0]
        else datetime.min,
    )


# Function to write tables to a CSV file
def write_csv(p_data, p_csv_path):
    with open(p_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "label", "credit", "debit"])  # Write header
        for row in p_data:
            writer.writerow(row)


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--directory",
    required=True,
    default="example_directory",
    help="Directory containing PDF files.",
)
@click.option(
    "--csv_path",
    required=True,
    default="final_output.csv",
    help="Path for the output CSV file.",
)
@click.option(
    "--filter_strings",
    required=False,
    multiple=True,
    default=[
        "Total des mouvements",
        "CREDITEUR",
        "Date valeur",
    ],
    help="Strings to filter out from the table. ",
)
def convert(directory, csv_path, filter_strings):
    absolute_path = os.path.dirname(__file__)
    relative_path = directory
    directory = os.path.join(absolute_path, relative_path)

    absolute_path = os.path.dirname(__file__)
    relative_path = csv_path
    csv_path = os.path.join(absolute_path, relative_path)

    master_table = []  # To store data from all PDFs

    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(directory, filename)

            table = read_pdf_tables(pdf_path)
            filtered_table = filter_rows(table, filter_strings)

            # Stitch rows with empty first columns to their previous rows
            stitched_table = stitch_rows(filtered_table)

            # Remove the first column from the table
            stitched_table = remove_first_column(stitched_table)

            master_table.extend(stitched_table)

    # Sort rows by date
    master_table = sort_by_date(master_table)

    # Write sorted table to the CSV
    write_csv(master_table, csv_path)


# Main execution
if __name__ == "__main__":
    cli()
