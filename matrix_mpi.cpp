#include <mpi.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <cstdlib>
#include <cstdio> // для SEEK_SET

using namespace std;

typedef vector<vector<int> > Matrix;

Matrix readMatrix(const string& path, int& n) {
    ifstream fin(path.c_str());
    if (!fin) {
        cerr << "ERROR: cannot open " << path << "\n";
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
    fin >> n;
    Matrix m(n, vector<int>(n));
    for (int i = 0; i < n; ++i)
        for (int j = 0; j < n; ++j)
            fin >> m[i][j];
    return m;
}

void writeMatrix(const string& path, const Matrix& m) {
    ofstream fout(path.c_str());
    if (!fout) {
        cerr << "ERROR: cannot write " << path << "\n";
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
    int n = (int)m.size();
    fout << n << "\n";
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            fout << m[i][j];
            if (j + 1 < n) fout << ' ';
            else fout << '\n';
        }
    }
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    string pathA, pathB, pathOut;
    for (int i = 1; i + 1 < argc; i += 2) {
        string key = argv[i];
        string val = argv[i + 1];
        if (key == "--a") pathA = val;
        else if (key == "--b") pathB = val;
        else if (key == "--out") pathOut = val;
    }
    
    if (pathA.empty() || pathB.empty() || pathOut.empty()) {
        if (rank == 0) cerr << "Usage: mpi_matrix --a <A.txt> --b <B.txt> --out <C.txt>\n";
        MPI_Finalize();
        return 1;
    }

    int n = 0;
    Matrix A, B, C;
    
    if (rank == 0) {
        A = readMatrix(pathA, n);
        int nB;
        B = readMatrix(pathB, nB);
        if (n != nB) {
            cerr << "ERROR: matrices must be same size\n";
            MPI_Abort(MPI_COMM_WORLD, 1);
        }
        C.resize(n, vector<int>(n, 0));
    }

    MPI_Bcast(&n, 1, MPI_INT, 0, MPI_COMM_WORLD);

    int rows_per_proc = n / size;
    int remainder = n % size;
    int local_rows = rows_per_proc + (rank < remainder ? 1 : 0);

    Matrix localA(local_rows, vector<int>(n));
    vector<int> flatB(n * n);
    if (rank == 0) {
        for (int i = 0; i < n; ++i)
            for (int j = 0; j < n; ++j)
                flatB[i * n + j] = B[i][j];
    }

    // Замеряем время с помощью MPI_Wtime() — встроенный таймер
    MPI_Barrier(MPI_COMM_WORLD);
    double t1 = MPI_Wtime();

    MPI_Bcast(&flatB[0], n * n, MPI_INT, 0, MPI_COMM_WORLD);

    vector<int> flatA;
    vector<int> sendcounts(size), displs(size);
    if (rank == 0) {
        flatA.resize(n * n);
        for (int i = 0; i < n; ++i)
            for (int j = 0; j < n; ++j)
                flatA[i * n + j] = A[i][j];
        
        int offset = 0;
        for (int i = 0; i < size; ++i) {
            int r = rows_per_proc + (i < remainder ? 1 : 0);
            sendcounts[i] = r * n;
            displs[i] = offset;
            offset += r * n;
        }
    }

    vector<int> localA_flat(local_rows * n);
    MPI_Scatterv(rank == 0 ? &flatA[0] : NULL, &sendcounts[0], &displs[0], MPI_INT,
                 &localA_flat[0], local_rows * n, MPI_INT, 0, MPI_COMM_WORLD);

    vector<int> localC(local_rows * n, 0);
    for (int i = 0; i < local_rows; ++i) {
        for (int k = 0; k < n; ++k) {
            int aik = localA_flat[i * n + k];
            for (int j = 0; j < n; ++j) {
                localC[i * n + j] += aik * flatB[k * n + j];
            }
        }
    }

    vector<int> flatC;
    if (rank == 0) flatC.resize(n * n);

    MPI_Gatherv(&localC[0], local_rows * n, MPI_INT,
                rank == 0 ? &flatC[0] : NULL, &sendcounts[0], &displs[0], MPI_INT,
                0, MPI_COMM_WORLD);

    MPI_Barrier(MPI_COMM_WORLD);
    double t2 = MPI_Wtime();
    double sec = t2 - t1;

    if (rank == 0) {
        for (int i = 0; i < n; ++i)
            for (int j = 0; j < n; ++j)
                C[i][j] = flatC[i * n + j];
        
        writeMatrix(pathOut, C);
        
        double ops = 2.0 * n * n * n;
        cout << "size=" << n << " time=" << sec 
             << " ops=" << (long long)ops 
             << " procs=" << size << "\n";
    }

    MPI_Finalize();
    return 0;
}