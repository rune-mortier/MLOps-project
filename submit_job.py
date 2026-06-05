"""
M5 Forecasting — Azure ML Job Submitter
Stuurt een training job op naar Azure ML.

Gebruik:
    python submit_job.py
    python submit_job.py --sample_frac 0.1 --epochs 30
"""

import argparse
from azure.ai.ml import MLClient, command
from azure.ai.ml.entities import Environment, AmlCompute
from azure.identity import DefaultAzureCredential


SUBSCRIPTION_ID = "91a4d59e-f70a-4dfe-b8c0-38b9bef510a6"
RESOURCE_GROUP  = "azure-ai"
WORKSPACE_NAME  = "MLOps-project"

COMPUTE_NAME = "m5-cluster-v3"
COMPUTE_SIZE = "Standard_D4s_v3"
MIN_NODES       = 0                   # schaalt terug naar 0 na gebruik = geen kosten
MAX_NODES       = 2


def parse_args():
    parser = argparse.ArgumentParser(description="Submit M5 training job naar Azure ML")
    parser.add_argument("--sample_frac",    type=float, default=0.05)
    parser.add_argument("--epochs",         type=int,   default=50)
    parser.add_argument("--batch_mlp",      type=int,   default=4096)
    parser.add_argument("--batch_lstm",     type=int,   default=512)
    parser.add_argument("--seq_len",        type=int,   default=14)
    parser.add_argument("--blob_conn_str",  type=str,   default=None,
                        help="Azure Blob connection string (of zet BLOB_CONN_STR env var)")
    parser.add_argument("--blob_container", type=str,   default="m5data")
    return parser.parse_args()


def get_or_create_compute(ml_client):
    """Maak compute cluster aan als het nog niet bestaat."""
    try:
        cluster = ml_client.compute.get(COMPUTE_NAME)
        print(f"✓ Compute cluster '{COMPUTE_NAME}' gevonden.")
        return cluster
    except Exception:
        print(f"→ Compute cluster '{COMPUTE_NAME}' aanmaken...")
        cluster = AmlCompute(
            name=COMPUTE_NAME,
            size=COMPUTE_SIZE,
            min_instances=MIN_NODES,
            max_instances=MAX_NODES,
            idle_time_before_scale_down=120,  # 2 min inactief → schaalt terug naar 0
        )
        ml_client.compute.begin_create_or_update(cluster).result()
        print(f"✓ Cluster aangemaakt: {COMPUTE_NAME} ({COMPUTE_SIZE})")
        return cluster


def get_or_create_environment(ml_client):
    """Maak de conda-omgeving aan in Azure ML."""
    env_name = "m5-forecasting-env"
    try:
        env = ml_client.environments.get(env_name, label="latest")
        print(f"✓ Environment '{env_name}' gevonden.")
        return env
    except Exception:
        print(f"→ Environment '{env_name}' aanmaken...")
        env = Environment(
            name=env_name,
            description="M5 Forecasting — Keras + PyTorch + MLflow",
            conda_file="environment.yml",
            image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04",
        )
        env = ml_client.environments.create_or_update(env)
        print(f"✓ Environment aangemaakt: {env_name}")
        return env


def main():
    args = parse_args()

    print("→ Verbinding maken met Azure ML...")
    ml_client = MLClient(
        credential=DefaultAzureCredential(),
        subscription_id=SUBSCRIPTION_ID,
        resource_group_name=RESOURCE_GROUP,
        workspace_name=WORKSPACE_NAME,
    )
    print(f"✓ Verbonden met workspace '{WORKSPACE_NAME}'")

    get_or_create_compute(ml_client)
    env = get_or_create_environment(ml_client)

    import os
    blob_conn_str = args.blob_conn_str or os.environ.get("BLOB_CONN_STR", "")
    if not blob_conn_str:
        print("\n⚠️  Geen blob_conn_str meegegeven.")
        print("   Zet de BLOB_CONN_STR environment variable, of geef --blob_conn_str mee.")
        print("   De job wordt toch gesubmit — zorg dat data_dir 'csv/' al bestaat op de compute.\n")

    command_str = (
    f"python training/train.py"
    f" --data_dir csv/"
    f" --blob_container {args.blob_container}"
    f" --output_dir outputs/"
    f" --sample_frac {args.sample_frac}"
    f" --epochs {args.epochs}"
    f" --batch_mlp {args.batch_mlp}"
    f" --batch_lstm {args.batch_lstm}"
    f" --seq_len {args.seq_len}"
)

    job = command(
        code=".",                        # upload de hele projectmap
        command=command_str,
        environment=env,
        compute=COMPUTE_NAME,
        display_name="m5-forecasting-run",
        description="MLP + LSTM training op M5 Walmart data",
        environment_variables={"BLOB_CONN_STR": blob_conn_str},
        experiment_name="m5-forecasting",
    )

    print("\n→ Job submitten naar Azure ML...")
    returned_job = ml_client.jobs.create_or_update(job)

    print(f"\n✅ Job gesubmit!")
    print(f"   Naam      : {returned_job.name}")
    print(f"   Status    : {returned_job.status}")
    print(f"   Studio URL: {returned_job.studio_url}")
    print(f"\nVolg je job op in Azure ML Studio:")
    print(f"  {returned_job.studio_url}")


if __name__ == "__main__":
    main()
