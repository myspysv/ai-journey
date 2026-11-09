print("---CALCULATOR---")
a = int(input("Enter the first value: "))
b = int(input("Enter the second value: "))
c = input("What arithmetical operation do you want to do? (+/-): ")
if c == '+':
    d = a + b
    print(d)
if c == '-':
    d = a - b
    print(d)