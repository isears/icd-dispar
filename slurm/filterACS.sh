#!/bin/bash
#SBATCH -n 1
#SBATCH -p batch
#SBATCH --cpus-per-task=2
#SBATCH --mem=64G
#SBATCH --time=7:00:00
#SBATCH --output ./logs/filterACS-%j.log


export PYTHONUNBUFFERED=TRUE

python filterACS.py