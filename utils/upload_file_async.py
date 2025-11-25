import boto3
from botocore.exceptions import NoCredentialsError
from config import AWS
import base64 as b64
import uuid
import os


def upload(base64, tipo, filename):
    try:
        # Configurações do AWS S3
        ACCESS_KEY = AWS["AccessKey"]
        SECRET_KEY = AWS["SecretKey"]
        REGION = AWS["Region"]
        BUCKET_NAME = AWS["BucketName"]

        # Inicializa o cliente S3
        s3_client = boto3.client('s3', 
                                 aws_access_key_id=ACCESS_KEY,
                                 aws_secret_access_key=SECRET_KEY,
                                 region_name=REGION)

        # Decodifica a imagem base64
        image_data = b64.b64decode(base64)

        # Define o nome do arquivo no S3
        if filename:
            file_name = f"uploads/{tipo}/{filename}"
        else:
            file_name = f"uploads/{tipo}/{str(uuid.uuid4())}"

        # Faz o upload para o S3
        s3_client.put_object(Bucket=BUCKET_NAME, Key=file_name, Body=image_data)

        # Retorna a URL pública do arquivo
        file_url = f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{file_name}"
        return file_url
    except Exception as e:
        print(f"Erro ao fazer upload: {e}")
        return None
    

def upload_local(base64, foto_arquivo_id):
    # Diretório para salvar as imagens (opcional)
    DOWNLOAD_FOLDER = 'downloads'
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)

    # Define um nome de arquivo local
    nome_arquivo_local = os.path.join(DOWNLOAD_FOLDER, f"{foto_arquivo_id}.jpg")

    # Salva o arquivo localmente
    with open(nome_arquivo_local, 'wb') as new_file:
        new_file.write(base64)