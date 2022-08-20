#!/bin/bash
#SBATCH -n 1
#SBATCH -p batch
#SBATCH --cpus-per-task=21
#SBATCH --mem=128G
#SBATCH --time=00:50:00
#SBATCH --output ./logs/filterParallel-%j.log


export PYTHONUNBUFFERED=TRUE

python filterParallel.py