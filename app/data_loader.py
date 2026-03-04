import boto3
import pandas as pd
from io import StringIO
from io import BytesIO

BUCKET_NAME = "bucket-asthme-scraping"
FILE_KEY = "geodes_complet.xlsx"
POLLEN_FILE_KEY = "pollen.csv"

def load_data_from_s3():
    s3 = boto3.client('s3')
    local_file = "/tmp/geodes_complet.xlsx"
    s3.download_file(BUCKET_NAME, FILE_KEY, local_file)
    df = pd.read_excel(local_file, engine="openpyxl")
    return df

def load_data_csv_from_s3():
    s3 = boto3.client('s3')
    local_file = "/tmp/pollen.csv"
    s3.download_file(BUCKET_NAME, POLLEN_FILE_KEY, local_file)
    df = pd.read_csv(local_file)
    return df


def load_pollen_data_from_s3():
    """Charge les données pollen depuis S3"""
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=POLLEN_FILE_KEY)
    return pd.read_csv(StringIO(obj['Body'].read().decode('utf-8')))


def load_data_from_s3_excel():
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=FILE_KEY)
    return pd.read_excel(BytesIO(obj['Body'].read()), engine="openpyxl")
