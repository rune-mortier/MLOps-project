import os, shutil, pathlib
from azure.ai.ml import MLClient
from azure.identity import ClientSecretCredential

cred = ClientSecretCredential(
    tenant_id=os.environ['AZURE_TENANT_ID'],
    client_id=os.environ['AZURE_CLIENT_ID'],
    client_secret=os.environ['AZURE_CLIENT_SECRET'],
)
ml = MLClient(cred, os.environ['AZURE_SUBSCRIPTION_ID'], 'azure-ai', 'MLOps-project')
jobs = list(ml.jobs.list())
job = next(j for j in jobs if (j.experiment_name or '') == 'm5-forecasting')
print('Downloading from job:', job.name)
ml.jobs.download(name=job.name, download_path='.', output_name='default')
src = pathlib.Path('named-outputs/default')
if src.exists():
    shutil.copytree(src, 'outputs', dirs_exist_ok=True)
    print('Artifacts gekopieerd naar outputs/')