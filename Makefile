CXX = mpicxx
CXXFLAGS = -O3 -Wall

all: matrix_mpi

matrix_mpi: matrix_mpi.cpp
	$(CXX) $(CXXFLAGS) matrix_mpi.cpp -o matrix_mpi

clean:
	rm -f matrix_mpi