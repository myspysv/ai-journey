students = [
    {"name": "Alex", "score": 51},
    {"name": "Anna", "score": 84},
    {"name": "Max", "score": 61},
    {"name": "Paul", "score": 89},
    {"name": "Peter", "score": 85}
]

total_score = 0
best_student = students[0]

for s in students:
    total_score += s["score"]
    if s["score"] > best_student["score"]:
        best_student = s
avg = total_score / len(students)
top_students = [s["name"] for s in students if s["score"] > 80]

print("2. СЕРЕДНІЙ БАЛ")
print(f"Total score is {total_score}.")
print(f"The average score is {round(avg, 2)}.")
print("\n3. НАЙКРАЩИЙ СТУДЕНТ (ПОШУК МАКСИМУМУ)")
print(f"The best student is {best_student['name']} with {best_student['score']}")
print("\n4. ФІЛЬТРАЦІЯ (БАЛ ВИЩЕ 80)")
print(f"The best students are {top_students}")