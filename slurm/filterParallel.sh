#!/bin/bash
#SBATCH -n 1
#SBATCH -p batch
#SBATCH --cpus-per-task=8
#SBATCH --mem=128G
#SBATCH --time=00:20:00
#SBATCH --output ./logs/filterParallel.log


export PYTHONUNBUFFERED=TRUE

python filterParallel.py