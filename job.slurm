#!/bin/bash
#SBATCH --job-name=mpi_matrix
#SBATCH --time=00:10:00
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --partition=batch
#SBATCH --output=job_%j.out

module load intel/mpi4
mpirun -np $SLURM_NTASKS ./matrix_mpi --a data/a_200.txt --b data/b_200.txt --out results/c_mpi_200.txt