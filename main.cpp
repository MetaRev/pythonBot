#include <iostream>
using namespace std;

void checkElement(int element) {
    cout << "Inside function: Address of element: " << &element << endl;
}

int main() {
    int arr[] = {10, 20, 30};

    cout << "Outside function: Address of arr[0]: " << &arr[0] << endl;

    checkElement(arr[0]);

    getchar();

    return 0;
}
