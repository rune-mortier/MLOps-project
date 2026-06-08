import os, shutil, pathlib, time
from azure.ai.ml import MLClient
from azure.identity import ClientSecretCredential

cred = ClientSecretCredential(
    tenant_id=os.environ['AZURE_TENANT_ID'],
    client_id=os.environ['AZURE_CLIENT_ID'],
    client_secret=os.environ['AZURE_CLIENT_SECRET'],
)
ml = MLClient(cred, os.environ['AZURE_SUBSCRIPTION_ID'], 'azure-ai', 'MLOps-project')

# Meest recente job ophalen
jobs = list(ml.jobs.list())
job = next(j for j in jobs if (j.experiment_name or '') == 'm5-forecasting')
print(f'Job gevonden: {job.name} (status: {job.status})')

# Wachten tot job klaar is
terminal_states = {'Completed', 'Failed', 'Canceled', 'NotResponding'}
while job.status not in terminal_states:
    print(f'Wachten... status: {job.status}')
    time.sleep(30)
    job = ml.jobs.get(job.name)

print(f'Job klaar met status: {job.status}')

if job.status != 'Completed':
    raise Exception(f'Job mislukt met status: {job.status}')

# Artifacts downloaden
ml.jobs.download(name=job.name, download_path='.', output_name='default')
src = pathlib.Path('named-outputs/default')
if src.exists():
    shutil.copytree(src, 'outputs', dirs_exist_ok=True)
    print('Artifacts gekopieerd naar outputs/')